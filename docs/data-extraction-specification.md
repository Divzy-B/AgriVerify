# Data Extraction Specification

What satellite data is extracted, how it is filtered and transformed, and what is stored. Last reviewed: 2026-10-29.

## Source

| Item | Value |
|---|---|
| Provider | Google Earth Engine |
| Dataset | `COPERNICUS/S2_SR_HARMONIZED` (Sentinel-2 Level-2A surface reflectance) |
| Spatial resolution used | 10 m (`reduceRegion` scale 10, `maxPixels` 10,000,000) |
| Revisit | about every 5 days; actual usable cadence depends on clouds |
| Bands | B8 (near infrared), B4 (red), QA60 (cloud mask) |
| Verified 2026-10-29 | 30 scenes returned for May 2025 near Lubbock, TX (point query) |

## Inputs

Field boundary (`Field.boundary_geojson`, WGS 84 Polygon or MultiPolygon), a start date and an end date.

## Pipeline

```mermaid
flowchart LR
    A[Scenes over field boundary<br/>in date range] --> B[Scene filter<br/>CLOUDY_PIXEL_PERCENTAGE < 60]
    B --> C[Pixel mask QA60<br/>bit 10 and 11 = 0]
    C --> D[Divide by 10000<br/>reflectance]
    D --> E[NDVI = normalizedDifference B8,B4<br/>SAVI = 1.5·(NIR−Red)/(NIR+Red+0.5)]
    E --> F[Field mean at 10 m]
    F --> G[One row per scene]
    G --> H[(satellite_observations)]
```

## Output per observation

| Field | Meaning |
|---|---|
| `acquisition_date` | Scene date, `YYYY-MM-dd` |
| `ndvi` | Field-mean NDVI; rows with no NDVI are dropped |
| `additional_indices.savi` | Field-mean SAVI |
| `cloud_coverage` | Scene-level `CLOUDY_PIXEL_PERCENTAGE` (whole scene, not the field) |
| `data_source` | `COPERNICUS/S2_SR_HARMONIZED` |
| `quality_flags` | Empty list for live rows |
| `source_metadata` | `{"collection": ...}` |
| `is_demo_data` | `false` for live rows |

Uniqueness: one row per `(field, date, data_source)`.

## Filtering used by the estimator

Observations used for estimation must have an NDVI value and `cloud_coverage <= 35` (or unknown). Fewer than 4 usable rows produces `INSUFFICIENT_EVIDENCE`. See [technical-design-document.md](technical-design-document.md).

Note the two cloud filters differ: Earth Engine admits scenes up to 60% cloudy (after masking pixels), the estimator keeps rows up to 35%.

## Date range

- **Claim verification** (`ensure_observations`): reported planting date −30 days to +75 days, capped at today, fetched when the window holds fewer than 4 real observations. Dates already stored are skipped when saving; the whole window is still requested.
- **Satellite-analysis endpoint:** Jan 1 to today of the current year, only when a field has no stored observations.
- When two scenes share a date, the one with lower cloud cover is stored.

## Known limits

- **Clouds and monsoon:** optical imagery fails under persistent cloud. Sentinel-1 radar is the usual complement; not implemented.
- **Mixed pixels:** plots under about 1 ha are dominated by edge pixels at 10 m.
- **Scene-level cloud percentage** does not describe the cloud over the field itself; the QA60 pixel mask does the real screening.
- **QA60** is a coarse mask; a scene classification layer (SCL) may screen better. TBD.
- **Not a crop model:** NDVI rises for reasons other than planting (weeds, prior cover, irrigation).

## Demo data

`SYNTHETIC_DEMO_SERIES`: 7, 7 and 1 observations for TX-001, TX-002, TX-003 with `is_demo_data=true` and flag `SYNTHETIC_DEMO`. Never mixed with live rows in the UI labelling: a field is labelled demo only if all its rows are demo.

## Validation (TBD)

No reference planting dates have been used. Candidate references: farmer-recorded dates from pilot fields; USDA NASS Crop Progress for season-level sanity checks; USDA Cropland Data Layer to find cotton fields.
