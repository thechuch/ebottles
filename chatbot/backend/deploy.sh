#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# eBottles AI Lead Intake — Cloud Run Deploy Script
# Usage: ./deploy.sh [--project PROJECT_ID] [--region REGION] [--env-file PATH]
# ============================================================

SERVICE="ebottles-backend"
REGION="us-central1"
PROJECT=""
ENV_FILE=".env"
IMAGE=""

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --project)  PROJECT="$2";   shift 2 ;;
    --region)   REGION="$2";    shift 2 ;;
    --env-file) ENV_FILE="$2";  shift 2 ;;
    -h|--help)
      echo "Usage: ./deploy.sh [--project PROJECT_ID] [--region REGION] [--env-file PATH]"
      echo ""
      echo "Options:"
      echo "  --project   GCP project ID (default: current gcloud project)"
      echo "  --region    Cloud Run region (default: us-central1)"
      echo "  --env-file  Path to .env file (default: .env)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Preflight checks ---
if ! command -v gcloud &>/dev/null; then
  echo "Error: gcloud CLI not found. Install it from https://cloud.google.com/sdk/docs/install"
  exit 1
fi

if ! gcloud auth print-access-token &>/dev/null; then
  echo "Error: Not authenticated. Run: gcloud auth login"
  exit 1
fi

if [[ -z "$PROJECT" ]]; then
  PROJECT=$(gcloud config get-value project 2>/dev/null)
  if [[ -z "$PROJECT" ]]; then
    echo "Error: No project set. Use --project flag or run: gcloud config set project PROJECT_ID"
    exit 1
  fi
fi

IMAGE="gcr.io/${PROJECT}/${SERVICE}"

echo "============================================"
echo "  eBottles Backend — Cloud Run Deploy"
echo "============================================"
echo "  Project:  $PROJECT"
echo "  Region:   $REGION"
echo "  Service:  $SERVICE"
echo "  Image:    $IMAGE"
echo "============================================"
echo ""

# --- Step 1: Enable required APIs (idempotent) ---
echo "[1/4] Enabling Cloud Run and Cloud Build APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  --project="$PROJECT" --quiet

# --- Step 2: Build image with Cloud Build ---
echo ""
echo "[2/4] Building Docker image via Cloud Build..."
gcloud builds submit \
  --tag "$IMAGE" \
  --project="$PROJECT" \
  --quiet

# --- Step 3: Deploy to Cloud Run ---
echo ""
echo "[3/4] Deploying to Cloud Run..."

DEPLOY_CMD=(
  gcloud run deploy "$SERVICE"
  --image "$IMAGE"
  --region "$REGION"
  --project "$PROJECT"
  --platform managed
  --allow-unauthenticated
  --port 8080
  --memory 512Mi
  --cpu 1
  --min-instances 0
  --max-instances 3
  --timeout 60
  --quiet
)

# Load env vars from .env file if it exists
if [[ -f "$ENV_FILE" ]]; then
  echo "   Loading env vars from $ENV_FILE"
  ENV_VARS=""
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip comments and empty lines
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    # Skip lines without =
    [[ "$line" != *"="* ]] && continue
    # Get key and value
    key="${line%%=*}"
    value="${line#*=}"
    # Skip if value is empty
    [[ -z "$value" ]] && continue
    # Append to env vars string
    if [[ -z "$ENV_VARS" ]]; then
      ENV_VARS="${key}=${value}"
    else
      ENV_VARS="${ENV_VARS},${key}=${value}"
    fi
  done < "$ENV_FILE"

  if [[ -n "$ENV_VARS" ]]; then
    DEPLOY_CMD+=(--set-env-vars "$ENV_VARS")
  fi
else
  echo "   Warning: No $ENV_FILE found. Deploy will use existing env vars on the service."
  echo "   Copy .env.example to .env and fill in values, then re-deploy."
fi

"${DEPLOY_CMD[@]}"

# --- Step 4: Verify deployment ---
echo ""
echo "[4/4] Verifying deployment..."
SERVICE_URL=$(gcloud run services describe "$SERVICE" \
  --region="$REGION" \
  --project="$PROJECT" \
  --format="value(status.url)")

echo ""
echo "   Service URL: $SERVICE_URL"
echo "   Health check: $SERVICE_URL/health"
echo ""

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/health" 2>/dev/null || true)

if [[ "$HTTP_STATUS" == "200" ]]; then
  echo "   Health check passed!"
else
  echo "   Warning: Health check returned HTTP $HTTP_STATUS"
  echo "   The service may still be starting up. Try again in a few seconds:"
  echo "   curl ${SERVICE_URL}/health"
fi

echo ""
echo "============================================"
echo "  Deploy complete!"
echo ""
echo "  Service URL: $SERVICE_URL"
echo "  Health:      $SERVICE_URL/health"
echo "  Lead intake: POST $SERVICE_URL/lead-intake"
echo "  Transcribe:  POST $SERVICE_URL/transcribe"
echo ""
echo "  Next: Update your Shopify widget script tag:"
echo "  data-backend-url=\"$SERVICE_URL\""
echo "============================================"
