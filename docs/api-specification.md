# API Specification

Base path `/api/v1`. OpenAPI UI at `/docs` when the backend runs. Source: `backend/app/main.py`, `schemas.py`. Last reviewed: 2026-10-29.

## Authentication

| Class | Rule |
|---|---|
| **Dashboard** | If `API_KEY` is set, header `X-API-Key` must match, else `401`. If unset, open. |
| **Webhook** | If `BOLNA_WEBHOOK_SECRET` is set, header `X-Webhook-Secret` must match, else `401`. |
| **Voice tools** | **None currently.** Planned: same secret header as the webhook (TBD). |
| **Health** | None. |

CORS allows origins from `ALLOWED_ORIGINS`, methods GET/POST/PATCH, headers `Content-Type`, `X-API-Key`, `X-Webhook-Secret`, `Idempotency-Key`.

## Endpoints

### Health and dashboard
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/health` | none | `{status, demo_mode, voice_provider, voice_configured, earth_engine_configured}` |
| GET | `/dashboard/summary` | dashboard | Totals, status distribution, six recent claims |

### Farmers
| Method | Path | Body / query | Response |
|---|---|---|---|
| GET | `/farmers` | | `FarmerRead[]` |
| POST | `/farmers` | `FarmerCreate` | `201 FarmerRead` |
| GET | `/farmers/{id}` | | `FarmerRead`, `404` |

`FarmerCreate`: `name` (2–160), `phone_number?` (≤32), `preferred_language` (`en`/`hi`/`mr`, default `en`). `FarmerRead` omits the phone number.

### Fields
| Method | Path | Notes |
|---|---|---|
| GET | `/fields?search=` | Matches id (upper-cased, contains) or name (case-insensitive) |
| POST | `/fields` | `FieldCreate`; `404` if the farmer does not exist. `boundary_geojson` must be a non-empty Polygon or MultiPolygon |
| GET | `/fields/{id}` | id is upper-cased |
| GET | `/fields/{id}/satellite-analysis` | `SatelliteAnalysisRead`; see below |

`FieldCreate`: `id` (`^[A-Za-z0-9-]{3,64}$`), `farmer_id`, `name`, `crop_type`, `boundary_geojson`, `latitude` (−90..90), `longitude` (−180..180), `area_hectares` (> 0).

`SatelliteAnalysisRead`: `field_id`, `satellite_data_source`, `analysis_mode` (`DEMO` | `EARTH_ENGINE` | `NOT_CONFIGURED`), `acquisition_dates[]`, `observations[]`, `estimated_planting_window {start,end}|null`, `estimator_version`, `evidence_quality`, `limitations[]`, `processing_status` (`COMPLETE` | `INSUFFICIENT_EVIDENCE` | `NOT_CONFIGURED`), `is_demo_data`.

### Claims and verification
| Method | Path | Notes |
|---|---|---|
| GET | `/claims?q=&status=&limit=&offset=` | limit 1–100 (default 50). `q` matches field or farmer id, upper-cased |
| POST | `/claims` | `ClaimCreate {farmer_id, field_id, reported_planting_date, idempotency_key?}`; header `Idempotency-Key` also accepted; `422` if the field is not the farmer's |
| GET | `/claims/{id}` | `404` |
| POST | `/claims/{id}/verify` | Runs verification, returns `VerificationRead` |
| PATCH | `/claims/{id}/review` | `{reviewer_notes (1–4000), status?}` |
| GET | `/verifications/{id}` | `VerificationRead`, `404` |
| GET | `/reports/{claim_id}/pdf` | `application/pdf`, inline; `409` if never verified |

`VerificationRead`: `id`, `claim_id`, `estimated_planting_date`, `estimated_window_start`, `estimated_window_end`, `discrepancy_days`, `evidence_quality`, `status`, `estimator_version`, `policy_version`, `evidence_summary`, `limitations[]`, `generated_at`.

### Voice
| Method | Path | Auth | Body |
|---|---|---|---|
| GET | `/voice/sessions`, `/voice/sessions/{id}` | dashboard | |
| POST | `/voice/simulator` | dashboard | `{farm_id, crop_type, planting_date, language}` → `{mode:"SIMULATION", session_id, claim_id, verification}` |
| POST | `/voice/tools/lookup-field` | none | `{farm_id}` → `{farm_id, crop_type, farmer_id, message}`; `404` |
| POST | `/voice/tools/create-claim` | none | `{farm_id, crop_type?, planting_date, session_id?}` → `{claim_id, status}`; `422` on missing date, unknown farm or crop mismatch |
| POST | `/voice/tools/run-verification` | none | `{session_id}` (required) → `{claim_id, verification_id, status, evidence_quality, message}` |
| POST | `/voice/tools/request-human-review?claim_id=` | none | → `{claim_id, status:"HUMAN_REVIEW", message}` |
| POST | `/voice/webhooks/{provider}` | webhook | Only `bolna`; body is Bolna's execution payload → `{accepted, session_id}` |

Bolna payload fields read: `execution_id` (or `id`, `call_id`), `status`, `transcript` (or `conversation`), `agent_data.language`.

## Errors

FastAPI default shape `{"detail": "..."}`. Codes used: `401` auth, `404` not found, `409` report before verification, `422` validation or business rule.

## Status and quality vocabularies

- Claim/verification status: `PENDING`, `WITHIN_TOLERANCE`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `HUMAN_REVIEW`.
- Evidence quality: `INSUFFICIENT_EVIDENCE`, `WEAK_EVIDENCE`, `MODERATE_EVIDENCE`, `STRONG_EVIDENCE`.

## Planned (TBD)

Lookup by phone number for voice; outbound-call trigger; authenticated voice tools; farmer/field registration UI support.
