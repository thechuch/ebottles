# eBottles Backend — Cloud Run Deployment Guide

Quick-start for deploying the AI lead intake backend. For full architecture details, see [HANDOFF.md](../../HANDOFF.md) in the repo root.

---

## Prerequisites

1. **Google Cloud SDK** — [Install gcloud CLI](https://cloud.google.com/sdk/docs/install)
2. **Authenticate:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

## First-Time Setup

Enable the required APIs (the deploy script does this automatically, but you can also run it manually):

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

## Team Access

Grant project access to team members (run once, requires Owner or IAM Admin role):

```bash
# Kyryl — Cloud Run developer (deploy, manage, view logs)
gcloud projects add-iam-policy-binding 259750349050 \
  --member="user:kyryl@circlesmall.com" \
  --role="roles/run.developer"

# Pavlo — Cloud Run developer
gcloud projects add-iam-policy-binding 259750349050 \
  --member="user:pavlo@circlesmall.com" \
  --role="roles/run.developer"

# Also grant Cloud Build permissions so they can build/deploy
gcloud projects add-iam-policy-binding 259750349050 \
  --member="user:kyryl@circlesmall.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding 259750349050 \
  --member="user:pavlo@circlesmall.com" \
  --role="roles/cloudbuild.builds.editor"
```

Or use the Cloud Console UI: [IAM & Admin](https://console.cloud.google.com/iam-admin/iam?project=259750349050)

### What these roles allow

| Role | Can do |
|------|--------|
| `roles/run.developer` | Deploy, update, delete Cloud Run services. View logs. |
| `roles/cloudbuild.builds.editor` | Submit builds (required for `gcloud builds submit`). |

## Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in real values
```

**Required values to get running:**
- `OPENAI_API_KEY` — Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- `GOOGLE_SHEET_ID` — The ID from the spreadsheet URL: `docs.google.com/spreadsheets/d/{THIS_ID}/`
- One of the Google service account credential options (see `.env.example` for details)
- `ALLOWED_ORIGINS` — Your Shopify store domain (e.g., `https://ebottles.com,https://ebottles.myshopify.com`)

## Deploy

From the `chatbot/backend/` directory:

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
1. Enable required GCP APIs
2. Build the Docker image via Cloud Build (no local Docker needed)
3. Deploy to Cloud Run (us-central1, scale-to-zero, max 3 instances)
4. Load env vars from your `.env` file
5. Run a health check and print the service URL

### Options

```bash
./deploy.sh --project my-project-id    # Override GCP project
./deploy.sh --region europe-west1      # Deploy to a different region
./deploy.sh --env-file .env.prod       # Use a different env file
```

## Verify

After deploy, test the endpoints:

```bash
# Health check
curl https://YOUR-SERVICE-URL/health

# Test lead intake (should return success or validation error)
curl -X POST https://YOUR-SERVICE-URL/lead-intake \
  -H "Content-Type: application/json" \
  -d '{
    "freeform_note": "We need child-resistant dropper bottles for CBD tinctures, approximately 10,000 units per month starting Q2.",
    "contact": {
      "name": "Test User",
      "company": "Test Co",
      "email": "test@example.com"
    }
  }'
```

## Update the Shopify Widget

Once deployed, update the widget script tag on each Shopify page:

```html
<script
  src="{{ 'widget.js' | asset_url }}"
  data-backend-url="https://YOUR-SERVICE-URL"
  ...>
</script>
```

Add the Shopify domain to `ALLOWED_ORIGINS` in your `.env` and re-deploy.

## View Logs

```bash
gcloud run services logs read ebottles-backend --region=us-central1 --limit=50
```

Or in the browser: [Cloud Run Console](https://console.cloud.google.com/run?project=259750349050)

## Re-deploy After Code Changes

Just run `./deploy.sh` again. It rebuilds the image and updates the service with zero downtime.

## Cost

At low volume (5-50 leads/day), Cloud Run costs **under $1-2/month** thanks to scale-to-zero. You only pay when requests are actively being processed.
