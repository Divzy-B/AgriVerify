# AgriVerify

AgriVerify is a voice-assisted crop-verification workspace. It helps collect
farm details, manage claims, inspect evidence, and route uncertain cases to a
human reviewer.

> **Important:** AgriVerify is decision-support software, not an insurance
> decision engine. Voice and satellite results never approve, deny, or
> guarantee insurance coverage. A qualified human must make every real-world
> coverage decision.

## What is included

- Firebase phone-number sign-in with one-time SMS codes.
- Farm registration, claim creation, verification records, audit events, and
  PDF reports.
- Demo satellite evidence for safe demonstrations and testing.
- Optional Google Earth Engine integration for appropriately authorised
  live-data work.
- Bolna voice-agent tools, webhook processing, and a text voice simulator.
- FastAPI backend, Next.js frontend, PostgreSQL support, and Cloud Run
  deployment support.

## Full project flow

~~~mermaid
flowchart LR
    A[Farmer or reviewer] --> B[AgriVerify website]
    B --> C[Firebase phone OTP]
    C --> D[FastAPI backend]
    D --> E[(PostgreSQL)]
    D --> F[Evidence analysis]
    F --> G[Demo observations or authorised Earth Engine data]
    D --> H[Human review queue]
    I[Bolna voice agent] --> J[Voice tools and webhook]
    J --> D
~~~

1. A person signs in with a phone number. Firebase sends and verifies the SMS
   one-time password (OTP).
2. A farmer or reviewer registers a farm with the farmer's phone number, crop,
   field name, location, area, and language.
3. The application stores the farmer and field in the database. At present, a
   field registered by latitude, longitude, and area is represented by an
   approximate square boundary. It is not a legal survey boundary.
4. A claim can be created for that field.
5. The backend runs evidence analysis:
   - **Demo mode:** clearly labelled synthetic observations.
   - **Live mode:** Google Earth Engine data only when its use is authorised
     and production credentials are configured.
6. The dashboard displays evidence and an outcome such as within tolerance,
   review required, or insufficient evidence.
7. A human reviewer makes every real-world coverage decision and can export a
   report.
8. The optional Bolna agent can collect intake information by voice, call
   backend tools, and send call outcomes to the webhook.

## Architecture

| Part | Technology | Responsibility |
| --- | --- | --- |
| Frontend | Next.js / React | Website, OTP UI, dashboard, registration, and claims |
| Backend | FastAPI / Python | REST API, Firebase token validation, reports, and voice webhook |
| Database | SQLite locally, PostgreSQL in production | Farmers, fields, claims, reviews, and audit records |
| Authentication | Firebase Authentication | Phone-number OTP and browser identity |
| Evidence | Demo data or Google Earth Engine | Field evidence analysis |
| Voice | Bolna | Optional voice intake and tool/webhook integration |
| Hosting | Cloud Run plus static hosting | Public API and website |

## Repository layout

~~~text
backend/             FastAPI application, Alembic migrations, Dockerfile
frontend/            Next.js application
docs/                Architecture, API, satellite, voice, and demo documents
docs/deploy/gcp/     Google Cloud deployment background
video/               Optional Remotion video assets
.env.example         Backend environment-variable template
docker-compose.yml   Optional local Docker setup
~~~

## Run locally - step by step

### 1. Install prerequisites

Install these once:

- Python 3.11 or newer
- Node.js 20 or newer
- npm
- Git

Optional:

- Docker Desktop for local PostgreSQL through Docker Compose
- Firebase for real SMS OTP testing
- Bolna for voice-agent testing
- Google Earth Engine only for authorised live-data experiments

### 2. Get the code

Open PowerShell and run:

~~~powershell
git clone https://github.com/YOUR-GITHUB-USERNAME/Bolna_AI_Project.git
cd Bolna_AI_Project
~~~

If the project is already on your computer, update it instead:

~~~powershell
git pull --ff-only github main
~~~

### 3. Create the backend environment file

At the repository root, create your private local environment file:

~~~powershell
Copy-Item .env.example .env
~~~

For a simple local demo, keep these settings in .env:

~~~dotenv
AGRIVERIFY_DEMO_MODE=true
DATABASE_URL=sqlite:///./agriverify.db
ALLOWED_ORIGINS=http://localhost:3000
REQUIRE_FIREBASE_AUTH=false
AUTO_CREATE_SCHEMA=true
VOICE_PROVIDER=bolna
~~~

REQUIRE_FIREBASE_AUTH=false is appropriate only for a local demo. Enable it
for an internet-facing deployment.

### 4. Install and start the backend

From the repository root:

~~~powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\backend\requirements.txt
cd backend
python -m uvicorn app.main:app --reload --port 8000
~~~

Leave this terminal running. The API is now at:

~~~text
http://127.0.0.1:8000
~~~

In a second PowerShell terminal, confirm it is healthy:

~~~powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
~~~

Expected demo result includes:

~~~text
status                  ok
demo_mode               True
~~~

### 5. Configure the frontend

Create frontend/.env.local. Do not commit this file.

~~~dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
~~~

For a local demo without real Firebase OTP, leave the Firebase fields blank.
For real OTP, copy the six Firebase web-app values from:

**Firebase Console -> Project settings -> Your apps -> AgriVerify Web -> SDK
setup and configuration**

Do not add measurementId; the frontend does not use it.

### 6. Install and start the frontend

In a second terminal:

~~~powershell
cd frontend
npm install
npm run dev
~~~

Open:

~~~text
http://localhost:3000
~~~

### 7. Try the local demo

1. Open the dashboard.
2. Choose **Register Farm**.
3. Enter a unique phone number with country code, a field name, crop,
   latitude, longitude, and area.
4. Register the farm.
5. Open the field or create a claim.
6. Run verification and inspect the evidence.
7. Open the report or review queue.

When AGRIVERIFY_DEMO_MODE=true, evidence is synthetic and must only be used
for a demo.

## Environment variables

Use .env.example as the complete backend template.

| Variable | Local demo value | Production purpose |
| --- | --- | --- |
| AGRIVERIFY_DEMO_MODE | true | Set to false only for authorised live-data work |
| DATABASE_URL | SQLite URL | Cloud SQL / PostgreSQL connection URL |
| ALLOWED_ORIGINS | http://localhost:3000 | Comma-separated public frontend domains |
| REQUIRE_FIREBASE_AUTH | false | Set to true for public deployments |
| FIREBASE_PROJECT_ID | blank | Firebase project used to validate ID tokens |
| AUTO_CREATE_SCHEMA | true | Usually false in production after migrations |
| BOLNA_API_KEY | blank | Bolna API credential |
| BOLNA_AGENT_ID | blank | Bolna agent identifier |
| BOLNA_WEBHOOK_SECRET | blank | Shared value validated on webhook requests |
| EARTH_ENGINE_PROJECT | blank | Google Cloud project used by Earth Engine |
| EARTH_ENGINE_SERVICE_ACCOUNT | blank | Production service-account email, if used |
| EARTH_ENGINE_PRIVATE_KEY_JSON | blank | Server-side key JSON, stored only in a secret manager |

Never commit .env, .env.local, service-account JSON, database passwords,
Firebase admin keys, Bolna keys, or webhook secrets.

## Firebase phone OTP setup

Configure Firebase before real SMS OTP can work:

1. Open [Firebase Console](https://console.firebase.google.com/).
2. Select the Firebase project.
3. Go to **Authentication -> Sign-in method -> Phone** and enable it.
4. Go to **Authentication -> Settings -> SMS region policy**.
5. Choose **Allow** and include every country where SMS will be sent, such as
   India and/or the United States.
6. Register a web app named **AgriVerify Web** in
   **Project settings -> Your apps**.
7. Copy the six web configuration values into frontend/.env.local for local
   development, or into your hosting environment for public builds.
8. Add the public website hostname in
   **Authentication -> Settings -> Authorised domains**.
9. Rebuild the frontend after changing any NEXT_PUBLIC_ value.

New Firebase projects can have a low daily SMS limit. Review the Firebase
Authentication Usage page and Google Cloud billing before inviting users.

## Bolna voice setup

Bolna is optional. The web workflow works without it.

1. Create and save a Bolna agent.
2. Configure the agent to collect farmer identity, field/crop details, and
   planting or claim information.
3. Configure the documented AgriVerify tools in Bolna.
4. Set the webhook URL to:

~~~text
https://YOUR_API_HOST/api/v1/voice/webhooks/bolna
~~~

5. Store the Bolna API key, agent ID, and webhook secret in a local .env for
   development or Google Secret Manager in production.
6. Configure the same webhook secret in Bolna as the custom request header
   expected by the backend.

See [docs/VOICE_PROVIDER_SETUP.md](docs/VOICE_PROVIDER_SETUP.md) for tool
contracts and expected webhook payloads.

## Satellite evidence modes

### Demo mode

Demo mode is recommended for class presentations, UI testing, and development.
It uses synthetic observations and labels them as demo data.

~~~dotenv
AGRIVERIFY_DEMO_MODE=true
~~~

### Live-data mode

Live mode requires all of the following:

1. Appropriate Earth Engine registration and usage rights for the use case.
2. A production identity, such as a service account or workload identity.
3. Credentials stored in a secret manager, never Git or browser code.
4. AGRIVERIFY_DEMO_MODE=false.
5. Testing analysis over known fields and dates.

Local earthengine authenticate proves access only on one computer. It is not a
deployment credential. See [docs/SATELLITE_SETUP.md](docs/SATELLITE_SETUP.md).

Do not use live mode for a commercial public product unless the Earth Engine
registration and billing arrangement permit it.

## Deploy publicly

The public deployment has two independent parts:

~~~mermaid
flowchart LR
    A[Build frontend] --> B[Static website hosting]
    B --> C[Cloud Run API URL]
    C --> D[Cloud Run FastAPI]
    D --> E[Cloud SQL PostgreSQL]
    D --> F[Firebase token verification]
    D --> G[Bolna webhook and tools]
~~~

### Production checklist

1. Create a PostgreSQL Cloud SQL instance and application database.
2. Store the database URL and third-party credentials in Google Secret Manager.
3. Build the backend container and deploy it to Cloud Run.
4. Run Alembic migrations before serving traffic.
5. Confirm GET /api/v1/health returns status: ok.
6. Configure Cloud Run:
   - REQUIRE_FIREBASE_AUTH=true
   - FIREBASE_PROJECT_ID=YOUR_PROJECT_ID
   - AUTO_CREATE_SCHEMA=false
   - production ALLOWED_ORIGINS
7. Attach the Cloud SQL instance and grant the Cloud Run service account:
   - Cloud SQL Client
   - Secret Manager Secret Accessor
   - Firebase Auth Viewer when Firebase tokens are required
8. Build the frontend with:

~~~dotenv
NEXT_PUBLIC_API_BASE_URL=https://YOUR_CLOUD_RUN_SERVICE_URL/api/v1
~~~

9. Publish the generated frontend/out directory using your static host.
10. Add the published hostname to Firebase Authorised Domains.
11. Point the Bolna webhook and tools to the public HTTPS API URL.
12. Test the full workflow before inviting users.

Deployment background is in
[docs/deploy/gcp/README.md](docs/deploy/gcp/README.md). Use current Google
Cloud CLI help while deploying because command flags can change.

### Build the static frontend

After setting production values in frontend/.env.local or CI:

~~~powershell
npm --prefix frontend install
npm --prefix frontend run build
~~~

The static site is generated in:

~~~text
frontend/out
~~~

Publish that directory with the hosting provider. A static public website
cannot use localhost; it must use the public Cloud Run API URL.

## End-to-end test checklist

After deployment, test:

1. Open https://YOUR_API_HOST/api/v1/health.
2. Open the public website in a private/incognito browser window.
3. Enter a real test phone number and receive a new Firebase SMS code.
4. Sign in successfully.
5. Register a farm with a unique phone number.
6. Create and view a claim.
7. Run a demo verification and inspect its evidence and report.
8. If Bolna is enabled, make a controlled test call and confirm its webhook
   reaches the API.
9. Confirm unapproved browser origins are blocked by CORS.
10. Confirm the review queue, audit records, and report are available to the
    right authenticated user.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| npm cannot find package.json | Run npm inside frontend, or use npm --prefix frontend. |
| Website says **Local API unavailable** | Start the local backend, or rebuild the public frontend with NEXT_PUBLIC_API_BASE_URL set to the public Cloud Run URL. |
| Firebase error auth/billing-not-enabled | Enable required Firebase/Google Cloud billing, then wait a few minutes. |
| Firebase says a domain is not authorised | Add the exact hostname in Firebase Authentication -> Settings -> Authorised domains. |
| reCAPTCHA has already been rendered | Refresh once. If it continues, restart the frontend dev server after checking the latest code. |
| Cloud Run says relation fields does not exist | Run the Alembic migration Cloud Run job, then redeploy the API. |
| Health says voice_configured false | Add valid Bolna values as Cloud Run secrets and attach them to the service. |
| Earth Engine is not configured | Keep demo mode on, or configure authorised production credentials server-side. |
| Duplicate farmer phone error | Each phone number can register one farmer. Select that farmer to add another field. |

## Current limitations and responsible use

- Demo observations are not live satellite data.
- The latitude/longitude/area registration workflow creates an approximate
  square, not a precise field polygon. Add draw/upload boundary support before
  real verification use.
- The application is not a substitute for an insurance policy, agronomist,
  survey, or human claims reviewer.
- Public production use should add role-based permissions, consent records,
  rate limits, monitoring, backups, audit retention, and a security review.
- Keep Firebase, Google Cloud, Bolna, and Earth Engine use within provider
  terms and the requirements for your organisation and location.

## Helpful documentation

- [System architecture](docs/system-architecture-document.md)
- [Application flow](docs/flow.md)
- [API specification](docs/api-specification.md)
- [Environment reference](docs/environment-config-reference.md)
- [Satellite setup](docs/SATELLITE_SETUP.md)
- [Voice provider setup](docs/VOICE_PROVIDER_SETUP.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Project decisions](docs/decision.md)

## Before pushing code

Run these commands from the repository root:

~~~powershell
git status
git diff --check
git add README.md
git commit -m "docs: expand project setup guide"
git push github main
~~~

Review git status before committing. Do not add .env, .env.local, or
credential files.
