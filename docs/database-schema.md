# Database Schema

Source of truth: `backend/app/models.py`; migration `backend/alembic/versions/0001_initial_schema.py`. Last reviewed: 2026-10-29. Databases: SQLite (local) or PostgreSQL 16 (Compose). JSON columns use SQLAlchemy `JSON`.

```mermaid
erDiagram
    FARMERS ||--o{ FIELDS : owns
    FARMERS ||--o{ CLAIMS : files
    FIELDS ||--o{ CLAIMS : "subject of"
    FIELDS ||--o{ SATELLITE_OBSERVATIONS : has
    CLAIMS ||--o{ VERIFICATIONS : "evaluated by"
    CLAIMS ||--o{ VOICE_SESSIONS : "created from"
    FARMERS ||--o{ VOICE_SESSIONS : "spoke in"

    FARMERS { string id PK
              string name
              string phone_number
              string preferred_language }
    FIELDS { string id PK
             string farmer_id FK
             string name
             string crop_type
             json boundary_geojson
             float latitude
             float longitude
             float area_hectares }
    CLAIMS { string id PK
             string farmer_id FK
             string field_id FK
             date reported_planting_date
             string status
             datetime submitted_at
             text reviewer_notes
             string idempotency_key UK }
    SATELLITE_OBSERVATIONS { string id PK
                             string field_id FK
                             date acquisition_date
                             string data_source
                             float ndvi
                             json additional_indices
                             float cloud_coverage
                             json quality_flags
                             json source_metadata
                             bool is_demo_data }
    VERIFICATIONS { string id PK
                    string claim_id FK
                    date estimated_planting_date
                    date estimated_window_start
                    date estimated_window_end
                    int discrepancy_days
                    string evidence_quality
                    string status
                    string estimator_version
                    string policy_version
                    text evidence_summary
                    json limitations
                    datetime generated_at }
    VOICE_SESSIONS { string id PK
                     string provider
                     string provider_session_id
                     string farmer_id FK
                     string claim_id FK
                     string language
                     string status
                     json transcript
                     datetime started_at
                     datetime ended_at }
    AUDIT_LOGS { string id PK
                 string actor_type
                 string actor_id
                 string entity_type
                 string entity_id
                 string action
                 json metadata
                 datetime created_at }
```

`audit_logs` has no foreign keys by design: `entity_type` and `entity_id` point loosely at any record.

## Tables

### farmers
`id` (string 64, UUID default), `name` (160, required), `phone_number` (32, nullable), `preferred_language` (16, default `en`; API accepts `en`, `hi`, `mr`), `created_at`, `updated_at`.

### fields
`id` (string 64, caller-supplied, pattern `^[A-Za-z0-9-]{3,64}$`), `farmer_id` → farmers (RESTRICT, indexed), `name`, `crop_type`, `boundary_geojson` (Polygon or MultiPolygon, WGS 84), `latitude`, `longitude`, `area_hectares` (> 0), timestamps. Deleting a field deletes its observations (cascade).

### claims
`id` (UUID or `CLM-<field>` for seeds), `farmer_id` and `field_id` (both RESTRICT, indexed), `reported_planting_date`, `status` (default `PENDING`), `submitted_at`, `reviewer_notes`, `idempotency_key` (unique, nullable), timestamps. Index `ix_claim_status_submitted (status, submitted_at)`.

Status values: `PENDING`, `WITHIN_TOLERANCE`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `HUMAN_REVIEW`. Not enforced by a database constraint; enforced in the API schema only for the review endpoint.

### satellite_observations
Unique `(field_id, acquisition_date, data_source)`. `ndvi` nullable; `cloud_coverage` is a percentage (scene-level for Earth Engine). `is_demo_data` separates synthetic from real rows. Seeded rows use `data_source = SYNTHETIC_DEMO_SERIES`; live rows use `COPERNICUS/S2_SR_HARMONIZED`.

### verifications
One row per verification run; many per claim. Keeps estimator and policy versions so old results stay interpretable. Deleted with the claim (cascade).

### voice_sessions
Unique `(provider, provider_session_id)`. `provider` is `bolna` or `simulator`. `claim_id` is set by the simulator, and for real calls by `link_voice_session` (matching the claim key `voice:<provider_session_id>`, in either order). It stays empty when no claim was made during the call or the agent used a different `session_id`.

### audit_logs
Append-only by convention. Actions in use: `claim.created`, `claim.verified`, `voice.simulated`, `voice.webhook.processed`.

## Constraints worth knowing

- `farmers.phone_number` is stored as `+` and digits and is unique **by application check only** (`register_farm`), not by a database constraint; `farmers.phone_number` is nullable because seeded demo farmers have none. A unique index would need a migration.
- A claim cannot be created for a field that does not belong to the stated farmer (service-level check).
- No constraint prevents several claims for the same field and season. TBD.
- `geoalchemy2` is a declared dependency, but boundaries are stored as plain JSON, not as PostGIS geometry.

## Seed data (demo mode)

| Field | Farmer | Reported date | Observations | Expected outcome |
|---|---|---|---|---|
| TX-001 | Alma Torres (`F-ALMA`) | 2025-05-25 | 7 | `WITHIN_TOLERANCE` |
| TX-002 | Nora Bennett (`F-NORA`) | 2025-07-04 | 7 | `REVIEW_REQUIRED` |
| TX-003 | Dev Shah (`F-DEV`, `hi`) | 2025-05-31 | 1 (58% cloud) | `INSUFFICIENT_EVIDENCE` |
