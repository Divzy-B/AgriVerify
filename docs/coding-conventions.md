# Coding Conventions

Derived from the existing code, so new code matches it. Last reviewed: 2026-10-29. Items not evidenced in the code are `TBD`.

## Backend (Python 3.11+)

- FastAPI with SQLAlchemy 2.0 typed models (`Mapped[...]`, `mapped_column`) and Pydantic v2 schemas (`ConfigDict(from_attributes=True)`).
- Routes are thin: validate, call a service, return a schema. Rules go in `services/` or `verification/`.
- Business-rule failures raise `ValueError` in services; the route converts them to `HTTPException(422)`. Missing records raise `404`.
- IDs: UUID strings by default; human-readable IDs (`TX-001`, `CLM-TX-001`) only for seeds and fields. Field and farm IDs are upper-cased on lookup.
- Every state-changing operation that matters writes an `AuditLog` row (`<entity>.<action>`).
- Estimator and rule classes carry a `version` string that is stored with every result. Change the string whenever behaviour changes.
- Idempotent endpoints take an idempotency key or a provider session id and use a database unique constraint, not only an application check.
- Integrations fail closed: raise a named exception (`EarthEngineUnavailable`) and show it; never substitute fake data.
- Configuration is read only through `get_settings()`. No secrets in code.
- Dates are `datetime.date`; timestamps are timezone-aware.
- Dependencies are pinned exactly in `requirements.txt`.

## Frontend (TypeScript)

- Next.js App Router, one client page. Tailwind plus `globals.css`; icons from `lucide-react`; charts from `recharts`.
- Server data goes through `lib/api.ts`; each call returns `{data, source: "live" | "preview"}` so screens can show provenance.
- Status values map to colours and badges in one place (`colors`, `StatusBadge`).
- Synthetic data is always labelled in the UI.
- Naming: components `PascalCase`, helpers `camelCase`, screens named by the `Screen` union.
- Type checks: `npm run typecheck`.

## Honesty rules (product-level)

- Never describe satellite output as proof of planting, or a status as insurance approval.
- Never present demo values as real, or an estimate as an exact date.
- Keep the human-review disclaimer on reports and on the dashboard.

## Testing

- `pytest -q` from `backend/`. API tests use `TestClient(app)` inside a `with` block so startup seeding runs; verification tests cover the estimator, rule and date normalization.
- Add a test with every new rule or endpoint. Cover the failure path, not only the success path.
- Frontend: `npm run typecheck` and `npm run build`. No unit tests exist yet.
- Current gaps: no tests for the Bolna adapter, Earth Engine path, PDF output, auth, or the frontend.

## Git and commits

TBD. No convention is recorded in this repository.

## Error handling

- Return `{"detail": "..."}` with a specific, actionable message.
- Log with the `agriverify` logger; do not log secrets or full transcripts.
