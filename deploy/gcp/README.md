# Production deployment: Mumbai Cloud Run + Cloud SQL

This folder is the production deployment plan for the Google Cloud project
`agriverify-satellite`. It uses:

- Cloud Run service in `asia-south1` (Mumbai)
- Cloud SQL for PostgreSQL in the same region
- Secret Manager for database and Bolna secrets
- Firebase ID tokens for browser API authentication
- Cloud Run's service account / application-default credentials for Earth Engine

Do not upload `.env`, a Firebase service-account JSON file, or any Bolna key to
GitHub, Cloud Run source uploads, or the browser.

> **Earth Engine use:** this project's Earth Engine registration was previously
> configured for the non-commercial Community tier. Do not set
> `AGRIVERIFY_DEMO_MODE=false` for a public insurance operation unless you have
> completed the appropriate commercial Earth Engine registration. A public
> non-commercial research/demo can retain demo mode until that is resolved.

## 1. One-time services and service account

Run the following in **Google Cloud Shell** after setting the project:

```bash
gcloud config set project agriverify-satellite
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com iamcredentials.googleapis.com

gcloud iam service-accounts create agriverify-api \
  --display-name="AgriVerify Cloud Run API"

gcloud projects add-iam-policy-binding agriverify-satellite \
  --member="serviceAccount:agriverify-api@agriverify-satellite.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
gcloud projects add-iam-policy-binding agriverify-satellite \
  --member="serviceAccount:agriverify-api@agriverify-satellite.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

For live Earth Engine, authorize that same runtime service account for the
Earth Engine project and grant the minimum Earth Engine / Service Usage roles
required by your organization. Keep this keyless: Cloud Run supplies
application-default credentials automatically.

## 2. Create Cloud SQL

In **Cloud SQL** click **Create instance** → **PostgreSQL**. Use these values:

| Setting | Value |
| --- | --- |
| Instance ID | `agriverify-db` |
| Region | `asia-south1` (Mumbai) |
| Edition | Enterprise |
| Preset | Sandbox for initial testing |
| Availability | Single zone for initial testing |
| Database version | PostgreSQL 16 or a currently supported Enterprise version |
| Database name | `agriverify` |
| Application user | `agriverify_app` |

Enable automatic backups and deletion protection before holding real farmer
data. Creating the instance is billable and may take several minutes.

Once it is ready, copy its **Instance connection name**, in the form
`agriverify-satellite:asia-south1:agriverify-db`.

## 3. Put runtime secrets in Secret Manager

Create three secrets in **Security → Secret Manager**. Do not paste any value
into source code.

| Secret name | Value |
| --- | --- |
| `agriverify-database-url` | `postgresql+psycopg://agriverify_app:URL_ENCODED_PASSWORD@/agriverify?host=/cloudsql/INSTANCE_CONNECTION_NAME` |
| `agriverify-bolna-api-key` | Your rotated Bolna API key |
| `agriverify-bolna-webhook-secret` | A long, newly generated random secret |

Replace `URL_ENCODED_PASSWORD` and `INSTANCE_CONNECTION_NAME` before saving.
If the password includes special characters, URL-encode it.

## 4. Build and deploy the API

From a machine containing this repository and the Google Cloud CLI, run this
from the repository root. Replace the instance connection name before running:

```bash
PROJECT_ID=agriverify-satellite
REGION=asia-south1
SERVICE=agriverify-api
SQL_INSTANCE=agriverify-satellite:asia-south1:agriverify-db
IMAGE=$REGION-docker.pkg.dev/$PROJECT_ID/agriverify/agriverify-api:latest

gcloud artifacts repositories create agriverify \
  --repository-format=docker --location=$REGION 2>/dev/null || true
gcloud builds submit backend --tag=$IMAGE

gcloud run deploy $SERVICE \
  --image=$IMAGE --region=$REGION --platform=managed \
  --allow-unauthenticated --port=8080 \
  --service-account=agriverify-api@$PROJECT_ID.iam.gserviceaccount.com \
  --add-cloudsql-instances=$SQL_INSTANCE \
  --set-env-vars="AGRIVERIFY_DEMO_MODE=true,AUTO_CREATE_SCHEMA=false,REQUIRE_FIREBASE_AUTH=true,FIREBASE_PROJECT_ID=$PROJECT_ID,EARTH_ENGINE_PROJECT=$PROJECT_ID,VOICE_PROVIDER=bolna,ALLOWED_ORIGINS=https://agriverify-voice-intelligence.divyabharambe25.chatgpt.site" \
  --set-secrets="DATABASE_URL=agriverify-database-url:latest,BOLNA_API_KEY=agriverify-bolna-api-key:latest,BOLNA_WEBHOOK_SECRET=agriverify-bolna-webhook-secret:latest"
```

Cloud Run must be publicly reachable because the browser and Bolna call it.
The API itself still rejects browser dashboard requests without a valid Firebase
ID token, and Bolna routes require `X-Webhook-Secret`.

## 5. Run the initial migration once

Create and execute a Cloud Run Job from the exact API image. This prevents web
instances racing to alter the database on startup.

```bash
gcloud run jobs create agriverify-migrate \
  --image=$IMAGE --region=$REGION \
  --service-account=agriverify-api@$PROJECT_ID.iam.gserviceaccount.com \
  --add-cloudsql-instances=$SQL_INSTANCE \
  --set-secrets="DATABASE_URL=agriverify-database-url:latest" \
  --command=alembic --args=upgrade,head
gcloud run jobs execute agriverify-migrate --region=$REGION --wait
```

If the job already exists after a later release, use `gcloud run jobs update`
with the same settings, then execute it again.

## 6. Connect the public frontend

Set this value only during the static frontend production build, then redeploy
the static site:

```text
NEXT_PUBLIC_API_BASE_URL=https://YOUR_CLOUD_RUN_URL/api/v1
```

Keep the six `NEXT_PUBLIC_FIREBASE_*` values already used by the frontend.
They are web configuration values; do not put backend credentials in them.

Add the final public dashboard host to Firebase Authentication → Settings →
Authorized domains. The existing ChatGPT-hosted dashboard domain must remain
there while it is used.

## 7. Post-deployment verification

```bash
curl https://YOUR_CLOUD_RUN_URL/api/v1/health
```

The result should say `earth_engine_configured: true`, and
`voice_configured: true` only after the associated configuration is complete.
Change `AGRIVERIFY_DEMO_MODE` to `false` only after the appropriate Earth
Engine registration is in place.
Then sign in through the dashboard, register a test field, and verify that its
request carries a Firebase bearer token.

Finally, configure Bolna Tools and webhook URLs with
`https://YOUR_CLOUD_RUN_URL/api/v1/voice/...` and supply the same
`X-Webhook-Secret` that is stored in Secret Manager.
