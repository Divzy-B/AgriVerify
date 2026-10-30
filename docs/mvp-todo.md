# MVP To-Do

Last updated: 2026-10-29. `[x]` done, `[ ]` open. **You** = needs your account, device or a decision. **Code** = a change in this repository.

MVP definition: a farmer reports a planting date by phone, the system fetches real Sentinel-2 data for their registered field, returns a verdict, and a reviewer sees and acts on it in the dashboard. Demo mode stays available as the offline fallback.

## Done

- [x] Documentation set in `docs/`
- [x] Earth Engine works without a service-account key (`earthengine authenticate`)
- [x] Earth Engine connection verified for project `bolna-ai-hackathon` (30 scenes returned near Lubbock, TX)
- [x] `.env` moved to `Bolna_AI_Project/.env`

## Decisions needed first (You)

- [ ] **How is a farmer identified on a call?** Recommended: caller phone number matched to `Farmer.phone_number`, confirmed by the agent. Alternative: spoken farm ID plus one-time code. Blocks phase 2.
- [ ] **Who registers fields, and how is the boundary drawn?** Recommended for the MVP: a reviewer form with centre point plus area (demo square). Blocks phase 1.
- [ ] **Target region and crop for the demo.** Texas cotton (current seed data) or Maharashtra cotton (matches Hindi/Marathi). Affects the monsoon-cloud risk.

## Phase 1 — Real data end to end (Code)

- [x] 1.1 **Registration form** in the dashboard. Done 2026-10-29: new **Register Farm** screen and `POST /registrations` (farmer + field in one transaction, centre point plus area becomes a square, see D13 and D15). Tested with 10 backend tests and by driving the built page in a browser (validation, success, duplicate phone, new field appears in the simulator list). Open follow-ups: a database unique index on phone; a map to draw boundaries.
- [x] 1.2 **Fetch satellite data inside `verify_claim`.** Done 2026-10-29: when a non-demo field has fewer than 4 real observations in the reported date −30 to +75 days window (capped at today), it fetches and stores them, one row per date. Demo mode never calls Earth Engine. Not yet run against live Earth Engine from the app (1.4).
- [x] 1.3 **Surface fetch errors.** Done 2026-10-29 in the backend: a failed fetch puts "Satellite data could not be retrieved: <reason>" first in the verification's limitations (status stays `INSUFFICIENT_EVIDENCE`, no fake data). A future-dated claim gets its own message. The dashboard still shows only the first limitation on the satellite page; a dedicated error state is TBD.
- [ ] 1.4 **Run the adapter on a real polygon** and check the NDVI series looks plausible. Use a field with a known planting date if you can get one (You).
  - Partly done 2026-10-29: ran the adapter and a full `verify_claim` on the TX-001 demo square near Lubbock for April 25 to Aug 9, 2025. It returned 68 rows (31 unique dates; most dates have two scenes). Live run found and fixed a bug: `divide()` dropped `system:time_start`, so the adapter had never worked on real data.
  - Result: `INSUFFICIENT_EVIDENCE` / `WEAK_EVIDENCE`. Real NDVI sat at about 0.21–0.32 with day-to-day noise and no clear rise, unlike the demo series (0.12 rising to 0.42). That square is not a known cotton field, so this says nothing about accuracy yet. It does show the +0.08 absolute threshold is fragile on real data (see 4.3).
  - Still open: a field with a known crop and planting date.
- [x] 1.5 **Wire `VERIFICATION_TOLERANCE_DAYS`** into `VerificationEngine`. Done 2026-10-29, with a test showing the same claim flips between `REVIEW_REQUIRED` (tolerance 2) and `WITHIN_TOLERANCE` (tolerance 7).
- [ ] 1.8 **Check the +0.08 NDVI jump threshold; it looks fragile and is unverified.** The estimator flags green-up when NDVI rises 0.08 above the average of the first three readings. On real Lubbock data (2026-10-29) NDVI hovered around 0.21–0.32 with day-to-day noise and no clear rise, so a fixed 0.08 jump can be missed or triggered by noise (the one reading that came close, 0.317 on May 24, had 28.7% cloud). The demo series (0.12 rising to 0.42) hides this. **Needs to be checked** against at least one real field with a known crop and planting date, and probably against a few. Options to evaluate: a relative rise instead of an absolute one, smoothing over several readings, requiring the rise to be sustained, and a stricter cloud limit. Do not trust a verdict from this estimator on real data until this is done (You: provide a field with a known planting date; Code: tune and test).
- [x] 1.6 **Date sanity checks** on claim creation. Done 2026-10-29: rejects future dates (always), dates older than `MAX_PLANTING_AGE_DAYS` (default 548) and a second claim for the same field and planting year (both outside demo mode). See decision D12. Open follow-up: a way for a reviewer to correct or reopen a mistaken claim, since duplicates are now blocked.
- [ ] 1.7 Tests with Earth Engine mocked. Done for 1.2, 1.3, 1.5 and 1.6 (`backend/tests/test_live_observations.py`, 18 tests passing).

## Phase 2 — Real voice (Code + You)

- [ ] 2.1 **Lookup by phone number** endpoint, and update the agent prompt (`voice/prompts/farmer_intake.md`) for the chosen identification method.
- [ ] 2.2 **Authenticate the four voice tool endpoints** with the webhook secret header.
- [ ] 2.3 **Use `normalize_confirmed_date`** in `create-claim` and handle the year-missing error with a clear message to the agent.
- [ ] 2.4 **Link the voice session to the claim** for real calls (set `claim_id` from the tool calls or webhook).
- [ ] 2.5 **Align tool names**: prompt says `record_planting_claim`, `run_planting_verification`, `get_verification_result`; endpoints are `create-claim`, `run-verification` (which already returns the result). Fix the prompt or add routes.
- [ ] 2.6 **Create the Bolna agent**, configure the four tools and the webhook callback with the secret header (You; needs Bolna account).
- [ ] 2.7 **Public HTTPS URL** for tools and webhook, for example ngrok for the demo (You).
- [ ] 2.8 **Test call** with a demo identity; confirm the voice session, claim, verification and audit entries (You + Code).
- [ ] 2.9 *Optional:* outbound-call endpoint that uses `initiate_call` and passes farmer and field to the agent.
- [ ] 2.10 **Test Hindi** in the agent before claiming support; leave Marathi unadvertised until tested.

## Phase 3 — Reviewer experience (Code)

- [ ] 3.1 **Claim detail view** with evidence, reviewer notes and status actions (uses `PATCH /claims/{id}/review`).
- [ ] 3.2 **Write an audit log entry** when a reviewer changes a claim.
- [ ] 3.3 **Send `X-API-Key`** from the frontend when `API_KEY` is set; stop silently falling back to preview data on a 401.
- [ ] 3.4 **PDF links from the API base URL**, not hardcoded `localhost:8000`.
- [x] 3.5 **Field selectors from data**, not the hardcoded `TX-001..003`; crop from the field record, not fixed "Cotton". Done 2026-10-29 for the Satellite Intelligence and AI Verification Calls screens. Also fixed: the simulator's result message used to vanish because every refresh swapped the page for the loading card; refreshes after a save are now quiet.
- [ ] 3.6 **Real sign-in** or an `API_KEY`-only gate. The demo phone code `246810` is not security. Decide how much the demo needs.

## Phase 4 — Hardening and demo readiness

- [ ] 4.1 Tests for the Bolna adapter, voice tools, PDF output and auth.
- [ ] 4.2 Confirm `.env` is not committed and rotate any secret that has appeared in logs or chat (`BOLNA_WEBHOOK_SECRET` is set in `.env`).
- [ ] 4.3 Calibration sanity check: compare estimated windows with at least a few known planting dates, or with USDA NASS Crop Progress for the season. Depends on 1.8 (the +0.08 threshold must be checked first).
- [ ] 4.4 Decide how to handle cloudy seasons in the pitch: state the limitation, or add Sentinel-1 radar later.
- [ ] 4.5 Update `DEMO_SCRIPT.md` for the live flow, keeping demo mode as the fallback.
- [ ] 4.6 Update `docs/`: decisions, flow, API spec and PRD status as each item lands.
- [ ] 4.7 Create a git branch for the work; the Earth Engine and config changes are still uncommitted on `main`.

## Missed-requirement checks

- [ ] Consent wording for calls and field analysis in the agent's opening lines.
- [ ] What the farmer is told after human review (SMS, call back, or nothing in the MVP).
- [ ] Caller verification so one farmer cannot file for another's field (covered by 2.1 if phone match is used).
- [ ] Plots under about 1 ha: note the 10 m mixed-pixel limit in the pitch.

## Not needed for the MVP

Production authentication and roles; policy and season model; crop- and region-specific calibration; PostGIS geometry; Cesium 3D globe; Sentinel-1 radar path; payments.

## Suggested order

1. Decisions above → 1.1, 1.2, 1.3 → 1.4 (first real verdict).
2. 2.1–2.5 → 2.6–2.8 (first real call).
3. 3.1–3.4 → 4.1–4.6.

Minimum demo path if time runs out: 1.1–1.4 plus the existing simulator, with demo mode as the fallback.
