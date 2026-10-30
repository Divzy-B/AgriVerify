# Decision Log

Chronological. A later entry may supersede an earlier one; superseded entries are kept. Dates before 2026-10-29 are not recorded in the repository and are marked TBD.

D1–D8b were **reconstructed on 2026-10-29 by reading the existing code and docs**. Their reasoning is inferred from the README, the old architecture doc and the code itself, not confirmed by the people who made them. The team should correct any that are wrong. D9 onward were decided during work on this log's date and record the reasoning at the time.

## Decisions reflected in the existing code (date TBD)

### D1 — The planting date is estimated as a window, never an exact date
Satellites see vegetation change, not seeds being planted. A 4–14 day emergence lag turns a green-up date into an interval. Presenting an exact date would overstate the evidence. Trade-off: less crisp for reviewers.

### D2 — Decisions come from a deterministic rule, not an LLM
Insurance outcomes must be explainable and repeatable. The voice agent only collects and confirms data. Every verification stores estimator and policy versions.

### D3 — Fail closed; never substitute demo data for real data
If Earth Engine is missing or errors, the API returns `NOT_CONFIGURED` and an error message. Demo observations carry `is_demo_data=true` and every screen labels them.

### D4 — Demo mode is the default
`AGRIVERIFY_DEMO_MODE=true` needs no accounts, so the demo is reliable offline.

### D5 — Provider-neutral voice boundary with a Bolna adapter
Business logic never sees vendor payloads. The text simulator calls the same service functions as the voice tools, so tests and demos exercise the real path.

### D6 — Webhook idempotency by `(provider, provider_session_id)`
Providers retry. A unique constraint makes repeat delivery safe.

### D7 — No invented webhook signature scheme
Bolna documents no signed-webhook contract, so the app compares an optional custom header (`X-Webhook-Secret`) instead of inventing HMAC verification.

### D8 — SQLite locally, PostgreSQL in Docker
Zero setup for development; Compose provides a production-like database.

### D8a — The dashboard falls back to labelled preview data when the API is down
`lib/api.ts` returns bundled synthetic records and the page shows a "STATIC PREVIEW — API OFFLINE" banner, so a hosted or static build still renders. Trade-off: a failed or unauthorised call (including a wrong `API_KEY`) also falls back silently to preview data; see to-do 3.3.

### D8b — Demo-only phone sign-in
The sign-in screen accepts any plausible phone number and the fixed code `246810`, keeping the session in `localStorage`. It exists so the demo looks like a real product; it is not security. Real authentication is TBD (to-do 3.6).

## Decisions made 2026-10-29

### D9 — Earth Engine works without a service-account key
Context: the Google Cloud organization enforces `iam.disableServiceAccountKeyCreation`, so a key file cannot be created. Decision: if no service account and key are configured, call `ee.Initialize(project=...)` and use credentials from `earthengine authenticate`. `earth_engine_configured` is now true when `EARTH_ENGINE_PROJECT` is set. Why not disable the org policy: it is a security default and not ours to weaken for convenience. Trade-off: local development uses a personal login; a deployed server must attach a service account instead of a key.
Verified: `ee.Initialize` succeeded and a Sentinel-2 query for May 2025 near Lubbock, TX returned 30 scenes.

### D10 — Earth Engine access level
Use Earth Engine Resource Viewer plus Service Usage Consumer for any service account. The app only reads the public catalog, so write and admin roles are unnecessary. Requested OAuth scopes: Google Cloud data and Earth Engine data; Cloud Storage is not needed (no exports).

### D11 — Claim verification fetches its own satellite data
`verify_claim` calls `ensure_observations` first. Non-demo only. Window: reported date −30 to +75 days, capped at today (30 days of baseline before, enough time after for green-up). Fetch only if fewer than 4 real observations are in the window; the number matches the estimator's minimum. Store one row per date, keeping the scene with the lowest cloud cover, because Sentinel-2 can return two scenes for the same date and the `(field, date, source)` constraint would otherwise fail (the same bug existed in the satellite-analysis route; both now use `store_earth_engine_observations`). A failure is reported first in `limitations`, not hidden. Trade-off: the whole window is refetched whenever it is thin, and the fetch runs inside the request; incremental fetching and background jobs are deferred.

### D12 — Claims are checked for plausible planting dates at creation
`create_claim` rejects: a future date (always); a date older than `MAX_PLANTING_AGE_DAYS` (default 548, about 18 months); and a second claim for the same field with a planting date in the same calendar year. Why: each of these wastes a satellite fetch and produces a meaningless verdict, and a farmer or voice agent can otherwise create them by accident. The age and duplicate rules are skipped in demo mode, because the seeded data is dated 2025 and demos re-run the same intake; the future-date rule applies everywhere. A retried voice call is still safe: the idempotency key returns the existing claim before any date check runs. Trade-offs: the calendar year stands in for a real season model (a reviewer cannot yet correct a mistaken claim, since nothing can be deleted or reopened); the 18-month limit is a guess. The error text is written to be relayed to a farmer by the voice agent.

### D13 — Field boundaries are entered as a centre point plus an area (a square), for now
Farmers cannot supply GeoJSON, and drawing on a map is a separate piece of work. The registration form (to-do 1.1) takes latitude, longitude and area in hectares and generates a square polygon of that area, the same approach the demo seed uses. Why: it is enough to exercise the whole pipeline and the demo. Trade-off: real plots are not square, so edge pixels can include non-field land, and the area in the record is the entered figure, not a measurement. Replace with map drawing, GPS corner walk or land-record lookup before real use. Decided by the user, 2026-10-29.

### D15 — One registration call creates the farmer and the field; the phone number is the farmer's identity
`POST /registrations` creates both in one transaction, so a half-registered farmer cannot exist, and generates the field id (`FLD-` plus 6 hex digits) and the square boundary on the server, so the browser never builds geometry. The phone number is stored as `+` and digits and may belong to only one farmer, because voice identification by caller number (proposal P1) depends on it. A farmer with several fields is handled by choosing the existing farmer in the form. Found while testing in a browser: the first version kept the `+` only if typed, so the same number entered both ways was not detected as a duplicate; every number now stores with the `+`. Limits: the uniqueness check is in application code, not a database constraint (two simultaneous registrations could race); a number entered without a country code cannot be told from another country's; area is capped at 1000 ha and latitude at ±85° (the square's width formula breaks near the poles). Field names are free text and not unique.

### D14 — Project docs live in `docs/` with kebab-case names
The set follows the user's global documentation convention: `decision.md` and `flow.md` live inside `docs/`, not at the repo root. `ARCHITECTURE.md` became `system-architecture-document.md`. The three operational guides (`SATELLITE_SETUP.md`, `VOICE_PROVIDER_SETUP.md`, `DEMO_SCRIPT.md`) keep their names. Decided by the user, 2026-10-29.

## Proposed, not yet decided

### P1 — Identify farmers by phone number, not a spoken farm ID
Farm IDs like `TX-001` are internal labels a farmer would not know. `Farmer.phone_number` already exists. Inbound: look up the farmer by caller number and confirm the farm. Outbound: pass the known farmer and field to the agent. Needs a lookup-by-phone endpoint and a prompt change.

### P2 — Enrollment through a registration form
A reviewer or field officer registers farmer, phone, language, crop and field boundary. The boundary method for the MVP is decided (D13); the form itself is to-do 1.1. In production this data would come from the insurer's policy system.
