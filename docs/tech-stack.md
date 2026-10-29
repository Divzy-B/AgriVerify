# Tech Stack

Last reviewed: 2026-10-29. Rationale for rejected alternatives is only recorded where the repository or our discussion states it; otherwise `TBD`.

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI 0.115, Uvicorn | Typed request validation, automatic OpenAPI, async webhook handling |
| ORM / migrations | SQLAlchemy 2.0, Alembic | Typed models; migration path beyond the demo `create_all` |
| Settings | pydantic-settings | Typed environment loading from `.env` |
| Database | SQLite (local), PostgreSQL 16 (Compose) | Zero-setup development; production-like option |
| HTTP client | httpx | Calls to Bolna |
| Dates | python-dateutil | Parsing confirmed dates |
| PDF | ReportLab | Pure-Python report generation, no browser dependency |
| Satellite | `earthengine-api` 1.4.0, dataset `COPERNICUS/S2_SR_HARMONIZED` | 10 m, ~5-day Sentinel-2 surface reflectance with a QA band; free for non-commercial use |
| Voice | Bolna AI (REST + webhooks) | Hackathon sponsor; supports Indian languages |
| Frontend | Next.js 15, React 19, TypeScript 5.7 | App Router, typed UI |
| UI | Tailwind 3.4, lucide-react, Recharts | Fast styling, icons, NDVI and status charts |
| Packaging | Docker, Docker Compose | One-command local stack |
| Tests | pytest, pytest-asyncio | |

## Declared but not used

- `geoalchemy2`: boundaries are stored as JSON, not PostGIS geometry.
- `cesium`: the map is a 2D fallback; the 3D globe is not integrated.
- `@tanstack/react-query`: `page.tsx` uses plain `fetch` helpers. (`clsx` not verified: TBD.)

Remove or adopt these deliberately; unused dependencies add install weight and audit surface.

## Alternatives for NDVI data (not adopted)

| Option | Note |
|---|---|
| Copernicus Data Space / Sentinel Hub Statistical API | Closest equivalent; REST, polygon in, statistics out |
| Microsoft Planetary Computer, AWS Earth Search (STAC) | Raw bands; NDVI computed by us |
| NASA AppEEARS, Earth Engine MODIS | 250 m; too coarse for small plots |
| Agromonitoring (OpenWeather) | Simple polygon-to-NDVI REST; third-party limits |

Radar (Sentinel-1) is the standard complement for cloudy seasons; not adopted yet.

## Reference data for calibration (not adopted)

USDA NASS Crop Progress (weekly planted percentage by state) and USDA Cropland Data Layer (crop type map).
