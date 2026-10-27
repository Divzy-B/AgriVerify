# Satellite Intelligence Setup

## Demo mode

`AGRIVERIFY_DEMO_MODE=true` creates the three persisted synthetic Texas cotton
series. The interface labels them as synthetic, and every observation has
`is_demo_data=true`. This is the correct buildathon route when no Earth Engine
credentials are present.

## Live Earth Engine mode

1. Register the intended Google account / Cloud project for Earth Engine and
   enable access according to Google’s current account requirements.
2. Create and authorize a service account for the project, then keep its JSON
   key in your secret manager.
3. Set `AGRIVERIFY_DEMO_MODE=false`, `EARTH_ENGINE_PROJECT`,
   `EARTH_ENGINE_SERVICE_ACCOUNT`, and `EARTH_ENGINE_PRIVATE_KEY_JSON`.
4. Submit a valid WGS84 GeoJSON Polygon or MultiPolygon with the field record.
5. Request `GET /api/v1/fields/{field_id}/satellite-analysis` and inspect the
   returned source, dates, observations, cloud coverage, limitations, and
   evidence grade.

The adapter uses `COPERNICUS/S2_SR_HARMONIZED`, Level-2A surface reflectance.
It filters by field and date, performs a QA60 cloud/cirrus mask, rescales the
data by 10,000, computes field-mean NDVI (B8 and B4) and SAVI, and persists
non-demo provenance. Failed credentials, unavailable scenes, or analysis errors
return a visible not-configured state rather than generated output.

## Scientific limitations

The baseline uses a vegetation transition to make a broad planting-window
inference. Germination lag, crop variety, irrigation, previous vegetation,
field preparation, clouds, satellite revisit cadence, and mixed pixels can all
shift the signal. It must be validated against reference data before it is used
as a calibrated operational model. No confidence percentage is generated.

## References

- [Google Earth Engine — Harmonized Sentinel-2 MSI Level-2A surface reflectance](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED)
- [Earth Engine Sentinel-2 dataset overview](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2)
