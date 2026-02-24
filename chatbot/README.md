# eBottles AI Lead Intake Widget

An AI-powered lead intake widget for eBottles. Captures packaging inquiries, extracts structured data using GPT-4o, stores leads in Google Sheets, and sends email notifications.

## Features

- **Floating widget** - Embeddable via single script tag
- **Voice input** - Record audio, transcribed via OpenAI Whisper
- **AI extraction** - GPT-4o extracts product types, volumes, timelines, compliance needs
- **Google Sheets** - All leads stored with structured + raw data
- **Email notifications** - Sales team notified on each submission

## Project Structure

```
ebottlesformbot/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Settings
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # OpenAI, Sheets, Gmail
│   │   └── models/           # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── demo.html             # Demo page
│   └── widget.js             # Embeddable widget
└── README.md
```

## Quick Start

### 1. Set up environment

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure environment variables

Create `backend/.env`:

```env
OPENAI_API_KEY=sk-your-key-here
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
# Recommended alternatives:
# GOOGLE_SERVICE_ACCOUNT_JSON_B64=base64_encoded_json
# GOOGLE_SERVICE_ACCOUNT_JSON_PATH=/path/to/secret/service-account.json
GOOGLE_SHEET_ID=your-sheet-id
NOTIFICATION_EMAIL=sales@ebottles.com
ADMIN_NOTIFICATION_EMAILS=estevan@circlesmall.com,sasha@circlesmall.com
ALLOWED_ORIGINS=http://localhost:5173,https://www.ebottles.com
DEBUG=true

# Optional: protect endpoints with a shared API key
API_KEY=your-random-shared-secret
```

### 3. Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8080
```

### 4. Serve the frontend

```bash
cd frontend
python -m http.server 5173
```

Open http://localhost:5173/demo.html

## Google Cloud Setup

### Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select project `ebottles`
3. Go to IAM & Admin → Service Accounts
4. Create service account with:
   - Google Sheets API access
   - Gmail API access (if using email notifications)
5. Create JSON key and paste into `GOOGLE_SERVICE_ACCOUNT_JSON`

### Create Google Sheet

1. Create a new Google Sheet
2. Share it with the service account email
3. Copy the Sheet ID from the URL and set `GOOGLE_SHEET_ID`

## Deploy to Cloud Run

```bash
cd backend

# Build and deploy
gcloud run deploy ebottles-ai-intake \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "OPENAI_API_KEY=sk-...,GOOGLE_SHEET_ID=..."
```

## Embed on Website

Add this script tag to any page:

```html
<script 
  src="https://your-domain.com/widget.js" 
  data-backend-url="https://ebottles-ai-intake-xyz.a.run.app"
  data-calendly-url="https://calendly.com/ebottles"
  data-api-key="your-random-shared-secret">
</script>
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/lead-intake` | POST | Submit lead form |
| `/transcribe` | POST | Transcribe audio file |
| `/health` | GET | Health check |

## AI Extraction Schema

The AI extracts:
- `product_types` - Array of packaging products
- `intended_use` - What the packaging is for
- `markets` - Geographic regions/states
- `estimated_monthly_volume` - Units per month
- `timeline` - Project urgency
- `sustainability_interest` - Eco-friendly interest
- `priority_band` - Lead priority (high/medium/low)
- `ai_summary` - 2-3 sentence summary for sales

## Security Notes

- Never commit `.env` files
- Rotate API keys if exposed
- Use Cloud Run secrets for production
- CORS is restricted to allowed origins

