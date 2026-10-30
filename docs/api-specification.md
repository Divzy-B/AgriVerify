# API Specification

Base path `/api/v1`. OpenAPI UI at `/docs` when the backend runs. Source: `backend/app/main.py`, `schemas.py`. Last reviewed: 2026-10-29.

## Authentication

| Class | Rule |
|---|---|
| **Dashboard** | If `API_KEY` is set, header `X-API-Key` must match, else `401`. If unset, open. |
| **Voice tools and webhook** (`secret` below) | If `BOLNA_WEBHOOK_SECRET` is set, header `X-Webhook-Secret` must match (constant-time compare), else `401`. **If it is not set these endpoints are open**, which is for local development only. |
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

### Registration
| Method | Path | Notes |
|---|---|---|
| POST | `/registrations` | Creates a field, and a farmer unless `farmer_id` names an existing one, in one transaction. Dashboard auth. `201 {farmer, field, demo_mode}` |

`RegistrationCreate`: `farmer_id?`; `name` (2–160) and `phone_number` (required unless `farmer_id` is given); `preferred_language` (`en`/`hi`/`mr`); `crop_type`; `field_name`; `latitude` (−85..85); `longitude` (−180..180); `area_hectares` (> 0, ≤ 1000). The server generates the field id (`FLD-` plus 6 hex digits) and an approximate square boundary of the stated area centred on the point.

The phone number is stored normalised as `+` and digits (8–15 digits, country code required), so `+91 98765 43210` and `919876543210` are the same farmer. Errors: `409` phone already registered, `404` unknown `farmer_id`, `422` invalid phone, missing name/phone, or out-of-range values.

### Claims and verification
| Method | Path | Notes |
|---|---|---|
| GET | `/claims?q=&status=&limit=&offset=` | limit 1–100 (default 50). `q` matches field or farmer id, upper-cased |
| POST | `/claims` | `ClaimCreate {farmer_id, field_id, reported_planting_date, idempotency_key?}`; header `Idempotency-Key` also accepted; `422` if the field is not the farmer's, the date is in the future, or (outside demo mode) the date is older than `MAX_PLANTING_AGE_DAYS` or the field already has a claim for that planting year |
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
| POST | `/voice/tools/lookup-farmer` | secret | `{phone_number}` (any formatting) → `{farmer_name, language, fields:[{farm_id, name, crop_type, area_hectares}], message}`; `404` no farmer with that number, `422` invalid number. Returns only that farmer's fields |
| POST | `/voice/tools/lookup-field` | secret | `{farm_id}` → `{farm_id, crop_type, farmer_id, message}`; `404` |
| POST | `/voice/tools/create-claim` | secret | `{farm_id, phone_number, planting_date, session_id, crop_type?}` → `{claim_id, status}`. `phone_number` (the caller's number) and `session_id` are **required**, and the field must belong to that number's farmer. `planting_date` is a string as confirmed with the caller (`2025-05-25`, `25 May 2025`, `25/05/2025`); it must include the year, and a numeric date that could be day/month or month/day (`05/06/2025`) is refused. Retrying with the same `session_id` returns the same claim. `422` on a missing date, number or session id, an ambiguous or year-less date, unknown farm, **a farm not registered to the caller**, crop mismatch, or an implausible date (same rules as `POST /claims`); the `detail` text is meant to be read to the farmer |
| POST | `/voice/tools/run-verification` | secret | `{session_id}` (required) → `{claim_id, verification_id, status, evidence_quality, message}` |
| POST | `/voice/tools/request-human-review?claim_id=` | secret | → `{claim_id, status:"HUMAN_REVIEW", message}` |
| POST | `/voice/webhooks/{provider}` | secret | Only `bolna`; body is Bolna's execution payload → `{accepted, session_id}` |

Bolna payload fields read: `execution_id` (or `id`, `call_id`), `status`, `transcript` (or `conversation`), `agent_data.language`.

## Errors

FastAPI default shape `{"detail": "..."}`. Codes used: `401` auth, `404` not found, `409` report before verification, `422` validation or business rule.

## Status and quality vocabularies

- Claim/verification status: `PENDING`, `WITHIN_TOLERANCE`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `HUMAN_REVIEW`.
- Evidence quality: `INSUFFICIENT_EVIDENCE`, `WEAK_EVIDENCE`, `MODERATE_EVIDENCE`, `STRONG_EVIDENCE`.

## Planned (TBD)

Outbound-call trigger; stronger caller verification (one-time code) than caller ID.
