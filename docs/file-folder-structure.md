# File and Folder Structure

Last reviewed: 2026-10-29.

```
Bolna_AI_Project/
├── README.md                     overview, quick start, limitations
├── .env.example                  variable names (copy to .env)
├── docker-compose.yml            api + frontend + PostgreSQL
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt          pinned Python dependencies
│   ├── alembic.ini
│   ├── alembic/                  migration environment
│   │   └── versions/0001_initial_schema.py
│   ├── app/
│   │   ├── main.py               FastAPI app: routes, auth, startup
│   │   ├── models.py             SQLAlchemy tables
│   │   ├── schemas.py            Pydantic request/response models
│   │   ├── db.py                 engine, session, Base
│   │   ├── core/config.py        settings
│   │   ├── services/
│   │   │   ├── claims.py         create + verify claims
│   │   │   ├── data.py           demo seed data
│   │   │   ├── date_normalization.py
│   │   │   ├── registration.py   farmer + field registration
│   │   │   └── reports.py        PDF report
│   │   ├── verification/engine.py   estimator + review rule
│   │   ├── satellite/
│   │   │   ├── earth_engine.py   Earth Engine adapter
│   │   │   └── indices.py
│   │   └── voice/
│   │       ├── base.py           provider interface
│   │       ├── service.py        lookup, create claim, simulate, webhook
│   │       ├── providers/bolna.py
│   │       └── prompts/farmer_intake.md   agent prompt
│   └── tests/
│       ├── conftest.py           shared empty in-memory database fixture
│       ├── test_api.py
│       ├── test_live_observations.py   live fetch, tolerance, date checks (Earth Engine mocked)
│       ├── test_registration.py
│       └── test_verification.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json              Next.js 15, React 19, Tailwind 3, Recharts
│   ├── next.config.ts, tsconfig.json, tailwind.config.ts, postcss.config.mjs
│   ├── app/                      layout.tsx, page.tsx, globals.css
│   └── lib/api.ts                API client + preview data
├── docs/                         this documentation set
└── .openai/hosting.json          hosting metadata (purpose TBD)
```

## Documents in `docs/`

| File | Purpose |
|---|---|
| `product-requirements-document.md` | goals, scope, requirement status |
| `technical-design-document.md` | estimator, rule, lifecycle, gaps |
| `system-architecture-document.md` | layers, data flow, deployment, security |
| `database-schema.md` | tables, ER diagram, seed data |
| `api-specification.md` | endpoints and shapes |
| `component-map.md` | components and dependency rules |
| `flow.md` | per-entry-point execution |
| `decision.md` | decision log |
| `environment-config-reference.md` | variables and setup |
| `coding-conventions.md` | style and testing |
| `tech-stack.md` | technologies and rationale |
| `ui-ux-wireframes.md` | screens and states |
| `data-extraction-specification.md` | satellite data extraction |
| `file-folder-structure.md` | this file |
| `mvp-todo.md` | open work for the MVP, by phase |
| `SATELLITE_SETUP.md`, `VOICE_PROVIDER_SETUP.md`, `DEMO_SCRIPT.md` | operational guides |

## Ownership rules

- Business rules live in `services/` and `verification/`, never in `main.py` or the frontend.
- Anything vendor-specific lives under `satellite/` or `voice/providers/`.
- Generated or local files (`.env`, `*.db`, `.venv/`, `node_modules/`, `.next/`) are not committed.
