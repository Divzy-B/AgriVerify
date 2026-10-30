# Product Requirements Document — AgriVerify

Last reviewed: 2026-10-29. Status of each requirement is against the code in this repository.

## Problem

A farmer files a crop-insurance claim and states a planting date. The planting date can decide whether a policy applies and what is paid. Sending an inspector to every farm is slow and expensive, and many farmers cannot easily use apps or forms.

## Goal

Give an insurance reviewer fast, evidence-based support for checking a reported planting date:

1. Collect the planting date from the farmer by voice (Bolna AI), in the farmer's language.
2. Estimate a planting **window** from satellite vegetation data (NDVI).
3. Compare the reported date with the window using a fixed, auditable rule.
4. Present the result, evidence and limitations to a human reviewer.

## Non-goals

- Approving, denying or pricing a claim. A human always decides.
- Proving the exact moment of planting. Satellites observe vegetation change, which is indirect evidence.
- A full policy-administration or payments system.
- Letting an LLM decide any outcome. The voice layer only collects and confirms data.

## Users

| User | Needs |
|---|---|
| **Farmer** | Report the planting date by phone, in their language, without an app. |
| **Insurance reviewer** | See which claims match the satellite evidence, which need investigation, and why. Download a report. |
| **Field officer / enrolling agent** (TBD) | Register farmers and field boundaries at policy sale. Not built yet. |

## Scope and requirement status

| # | Requirement | Status |
|---|---|---|
| R1 | Store farmers, fields (GeoJSON boundary), claims, observations, verifications, voice sessions, audit log. | Done |
| R2 | Estimate a planting window from cloud-screened NDVI. | Done (uncalibrated) |
| R3 | Decide `WITHIN_TOLERANCE` / `REVIEW_REQUIRED` / `INSUFFICIENT_EVIDENCE` by a deterministic rule with a configurable tolerance (default 7 days). | Done |
| R4 | Offline demo mode with clearly labelled synthetic data. | Done |
| R5 | Live Sentinel-2 NDVI through Google Earth Engine, failing closed. | Wired into claim verification 2026-10-29 (tested with Earth Engine mocked); first live run from the app pending |
| R6 | Voice intake through Bolna: tool endpoints and webhook. | Endpoints done and secret-protected; agent not created; no outbound call trigger |
| R7 | Text simulator that exercises the same backend path as a call. | Done |
| R8 | Dashboard: overview, farm explorer, satellite view, claims, calls, reports, settings. | Done (read-only) |
| R9 | PDF verification report per claim. | Done |
| R10 | Reviewer notes and status override. | API done; no UI |
| R11 | Enrollment: register farmer, phone, language, field boundary. | Done 2026-10-29 (Register Farm screen, `POST /registrations`); boundary is an approximate square from a centre point and area |
| R12 | Identify the farmer by phone number rather than a spoken farm ID. | Backend and prompt done 2026-10-29; depends on Bolna passing the caller's number (TBD) |
| R13 | Real authentication and roles. | Not done (demo sign-in only) |

## Acceptance criteria for the MVP

1. With demo mode on, seeded claims verify to the documented outcomes: TX-001 `WITHIN_TOLERANCE`, TX-002 `REVIEW_REQUIRED`, TX-003 `INSUFFICIENT_EVIDENCE`.
2. With demo mode off and Earth Engine configured, a claim on a real field fetches observations around the reported date and verifies without manual steps.
3. A farmer can report a date through a real Bolna call and the claim, verification and transcript appear in the dashboard.
4. Every verification records estimator version, policy version, evidence quality, interval and limitations.
5. No screen or report presents synthetic data as real, or an estimate as an exact date or a coverage decision.

## Success metrics (TBD)

Share of claims resolved without a field visit; reviewer time per claim; estimate accuracy against known planting dates. Targets are TBD and need reference data.

## Risks

| Risk | Note |
|---|---|
| Cloudy seasons (for example monsoon) leave too few clear optical images. | Radar (Sentinel-1) is the usual remedy; not implemented. |
| Small plots mix field and non-field pixels at 10 m. | Mitigation TBD. |
| The estimator thresholds are guesses. | Validate against reference planting dates before real use. |
| Someone files a claim for another farmer's field. | Caller verification (phone match or one-time code) is TBD. |
| Hindi and Marathi voice quality is unverified. | Test in the Bolna agent before advertising. |
| Consent and data retention for calls and field data. | Policy TBD. |

## Open questions

- How is a farmer identified on a call: caller ID, one-time code, or both?
- Who draws field boundaries, and with what tool?
- Which crops and regions are in scope beyond Texas cotton?
- What happens after a human review: is the farmer informed, and how?
