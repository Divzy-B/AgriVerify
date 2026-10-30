# AgriVerify

AgriVerify is a local, demo-ready agricultural insurance verification platform.
It turns a farmer intake into a planting claim, builds an evidence-based planting
window from field observations, and makes the deterministic review outcome
available in a dashboard, a text simulator, and a PDF report.

The application deliberately does **not** claim that satellite imagery observes
the moment a seed is planted. The baseline detector treats a sustained
vegetation change as indirect evidence and returns a window with limitations.

## What works now

- FastAPI + SQLAlchemy REST API, OpenAPI at `/docs`, SQLite local fallback, and
  Docker Compose PostgreSQL option.
- A seeded offline dataset for TX-001, TX-002, and TX-003. Every generated
  observation has `is_demo_data=true` and the dashboard has a visible warning.
- Deterministic rule evaluation: within a configurable seven-day tolerance,
  review required, or insufficient evidence.
- Next.js dashboard screens for Overview, Farm Explorer, Satellite
  Intelligence, Claims, AI Verification Calls, Verification Reports, and
  Settings. The static view uses a labeled fallback when the local API is down.
- A text intake simulator that uses the same create-claim and verification
  services as voice tools; it never pretends to be a phone call.
- Generic voice provider boundary and a Bolna HTTP adapter; normalized webhook
  persistence with a provider/session uniqueness constraint.
- An Earth Engine adapter for `COPERNICUS/S2_SR_HARMONIZED` that fails closed
  when credentials or processing are unavailable. It never replaces an error
  with fake “real satellite” values.
- In-browser 2D geospatial fallback, GeoJSON field boundaries, index charts,
  and generated PDF verification reports.

## Quick start (local demo)

Prerequisites: Python 3.11+ and Node.js 22+.

```powershell
Copy-Item .env.example .env
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. API reference: `http://localhost:8000/docs`.

To run through Docker instead:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Tests

```powershell
cd backend
pytest -q
cd ..\frontend
npm run typecheck
npm run build
```

## Architecture

```
Next.js dashboard ──── REST / polling ──── FastAPI
                                              ├─ claim + verification services
                                              ├─ SQLAlchemy (SQLite / PostgreSQL)
                                              ├─ satellite adapters (demo / Earth Engine)
                                              ├─ PDF report generator
                                              └─ VoiceProvider → Bolna adapter
```

See [system architecture](docs/system-architecture-document.md), [flow](docs/flow.md),
[decision log](docs/decision.md), [voice provider setup](docs/VOICE_PROVIDER_SETUP.md),
[satellite setup](docs/SATELLITE_SETUP.md), and the [demo script](docs/DEMO_SCRIPT.md).
The full document set is indexed in [file-folder-structure](docs/file-folder-structure.md).

## Environment

`AGRIVERIFY_DEMO_MODE=true` is the default and needs no external account. Keep
demo mode enabled for a reliable offline buildathon presentation. Use
`API_KEY` in any shared environment; dashboard endpoints then require an
`X-API-Key` header. Do not treat this starter authentication as a full
production identity system.

Live external integration requires credentials that are not included in the
repository:

- `BOLNA_API_KEY` and `BOLNA_AGENT_ID`
- An Earth Engine project plus authorized service account and JSON key data
- Public HTTPS callback infrastructure for provider webhooks

## Known limitations

- The 2D map is the operational fallback. CesiumJS is a frontend dependency,
  but production Cesium asset hosting / imagery configuration remains a
  deployment integration task.
- The planting estimator is intentionally transparent and uncalibrated. It is
  not a scientific crop phenology model and has no confidence percentage.
- Hindi and Marathi must be tested in the configured Bolna agent before live
  calls are advertised; the local simulator only models language preference.
- Real Earth Engine work requires reference validation and field-specific
  quality review. No live satellite or phone integration has been executed in
  this repository because credentials are absent.

## Attribution

Voice infrastructure integration is implemented for Bolna AI. Sentinel-2
surface-reflectance access is designed for Google Earth Engine / Copernicus
data, subject to the provider and dataset terms.
