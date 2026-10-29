"""Earth Engine integration. It is invoked only when configured; demo data is never substituted."""
from datetime import date

from app.core.config import Settings


class EarthEngineUnavailable(RuntimeError):
    pass


def fetch_sentinel2_observations(*, boundary_geojson: dict, start: date, end: date, settings: Settings) -> list[dict]:
    """Return field-aggregated, cloud-screened Sentinel-2 SR observations.

    The configured service account must be authorized for Earth Engine. The runtime
    deliberately fails closed instead of providing fabricated Earth Engine values.
    """
    if not settings.earth_engine_configured:
        raise EarthEngineUnavailable("Earth Engine is not configured. Enable demo mode or set EARTH_ENGINE_PROJECT (plus application-default credentials or a service-account key).")
    try:
        import json
        import ee

        if settings.earth_engine_service_account and settings.earth_engine_private_key_json:
            credentials = ee.ServiceAccountCredentials(
                settings.earth_engine_service_account,
                key_data=json.loads(settings.earth_engine_private_key_json),
            )
            ee.Initialize(credentials, project=settings.earth_engine_project)
        else:  # run `earthengine authenticate` once (or attach a service account on GCP)
            ee.Initialize(project=settings.earth_engine_project)
        geometry = ee.Geometry(boundary_geojson)

        def mask_and_indices(image):
            qa = image.select("QA60")
            clear = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
            clean = image.updateMask(clear).divide(10000)
            ndvi = clean.normalizedDifference(["B8", "B4"]).rename("ndvi")
            savi = clean.expression("((nir-red)/(nir+red+0.5))*1.5", {"nir": clean.select("B8"), "red": clean.select("B4")}).rename("savi")
            # divide() drops image properties; the date and cloud percentage are read downstream
            return clean.addBands([ndvi, savi]).copyProperties(image, ["system:time_start", "CLOUDY_PIXEL_PERCENTAGE"])

        collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geometry).filterDate(start.isoformat(), end.isoformat())
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)).map(mask_and_indices))

        def reduce_image(image):
            values = image.select(["ndvi", "savi"]).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=geometry, scale=10, maxPixels=10_000_000
            )
            return ee.Feature(None, {
                "date": image.date().format("YYYY-MM-dd"),
                "ndvi": values.get("ndvi"), "savi": values.get("savi"),
                "cloud_coverage": image.get("CLOUDY_PIXEL_PERCENTAGE"),
            })

        features = collection.map(reduce_image).getInfo().get("features", [])
        return [feature["properties"] for feature in features if feature["properties"].get("ndvi") is not None]
    except Exception as exc:  # provider errors must be visible, not replaced by demo observations
        raise EarthEngineUnavailable(f"Earth Engine analysis failed: {exc}") from exc

