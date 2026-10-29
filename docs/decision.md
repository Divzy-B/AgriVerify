# Decision Log

Chronological. A later entry may supersede an earlier one; superseded entries are kept. Dates before 2026-10-29 are not recorded in the repository and are marked TBD.

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

## Proposed, not yet decided

### P1 — Identify farmers by phone number, not a spoken farm ID
Farm IDs like `TX-001` are internal labels a farmer would not know. `Farmer.phone_number` already exists. Inbound: look up the farmer by caller number and confirm the farm. Outbound: pass the known farmer and field to the agent. Needs a lookup-by-phone endpoint and a prompt change.

### P2 — Enrollment through a registration form
A reviewer or field officer registers farmer, phone, language, crop and field boundary. Boundary by drawing on a map, or by centre point plus area for a demo square. In production this data would come from the insurer's policy system.

### P4 — Docs live in `docs/` using kebab-case names
This set follows the global documentation convention. `ARCHITECTURE.md` became `system-architecture-document.md`. The three setup guides (`SATELLITE_SETUP.md`, `VOICE_PROVIDER_SETUP.md`, `DEMO_SCRIPT.md`) are kept as operational guides.
