# Environment and Configuration Reference

Settings are loaded by `backend/app/core/config.py` (`pydantic-settings`) from the process environment and from `.env` in the **repository root** (`Bolna_AI_Project/.env`). Unknown keys are ignored. Last reviewed: 2026-10-29.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `AGRIVERIFY_DEMO_MODE` | `true` | `true`: seed synthetic data, auto-verify pending claims, never call Earth Engine. `false`: real data only. |
| `DATABASE_URL` | `sqlite:///./agriverify.db` | SQLAlchemy URL. Compose overrides it with `postgresql+psycopg://agriverify:agriverify@db:5432/agriverify`. |
| `API_KEY` | empty | If set, dashboard routes require header `X-API-Key`. Empty means open. |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins. |
| `VOICE_PROVIDER` | `bolna` | Only `bolna` exists. |
| `BOLNA_API_KEY` | empty | Bearer token for outbound Bolna calls. Secret. |
| `BOLNA_AGENT_ID` | empty | Bolna agent to call. |
| `BOLNA_WEBHOOK_SECRET` | empty | If set, webhook requests must send `X-Webhook-Secret` with this value. Secret. |
| `EARTH_ENGINE_PROJECT` | empty | Google Cloud project **ID**. Setting it marks Earth Engine as configured. |
| `EARTH_ENGINE_SERVICE_ACCOUNT` | empty | Optional. Service-account email. |
| `EARTH_ENGINE_PRIVATE_KEY_JSON` | empty | Optional. The key JSON as one line. Secret. Not needed when using `earthengine authenticate`. |
| `VERIFICATION_TOLERANCE_DAYS` | `7` | Days a reported date may sit outside the estimated window and still be `WITHIN_TOLERANCE`. Applied at each verification. |
| `MAX_PLANTING_AGE_DAYS` | `548` | Oldest reported planting date accepted for a new claim (days before today). Ignored in demo mode. |
| `NEXT_PUBLIC_API_BASE_URL` | TBD (Compose sets `http://localhost:8000/api/v1`) | Frontend API base. |

Derived: `earth_engine_configured` = project is set. `bolna_configured` = API key and agent id both set.

## Modes

| Mode | Settings |
|---|---|
| Offline demo | `AGRIVERIFY_DEMO_MODE=true`, nothing else. |
| Live satellite, no key | `AGRIVERIFY_DEMO_MODE=false`, `EARTH_ENGINE_PROJECT=<id>`, then `earthengine authenticate` once. |
| Live satellite, service account | Also set service account and key JSON, or attach the account on Google Cloud. |
| Live voice | Set Bolna key and agent id, a public HTTPS URL for the webhook, and the agent's tool endpoints. |

## Setup checklist: Earth Engine

1. Register the Google Cloud project for Earth Engine (non-commercial or commercial).
2. Enable the Earth Engine API on the project.
3. Run `earthengine authenticate`, approve Google Cloud data and Earth Engine data (Cloud Storage is not needed).
4. Set `EARTH_ENGINE_PROJECT` and `AGRIVERIFY_DEMO_MODE=false` in `.env`.
5. For a service account instead: grant Earth Engine Resource Viewer and Service Usage Consumer. Key creation may be blocked by the organization policy `iam.disableServiceAccountKeyCreation`; use step 3 instead.
6. Check: `python -c "import ee; ee.Initialize(project='<id>'); print(ee.Number(1).add(1).getInfo())"` prints `2`.

## Setup checklist: Bolna

See [VOICE_PROVIDER_SETUP.md](VOICE_PROVIDER_SETUP.md).

## Secrets guidance

- `.env` is git-ignored; `.env.example` holds names only. Verify `.env` is in `.gitignore` before the first commit.
- Never place a secret in a variable that is supposed to hold a name or a URL.
- The browser receives no secrets. `NEXT_PUBLIC_*` values are public by definition.
- Rotate any secret that has appeared in a log, chat or screenshot.

## Ports

Backend 8000, frontend 3000, PostgreSQL 5432 (Compose).
