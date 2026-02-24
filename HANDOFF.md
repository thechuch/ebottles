# eBottles Developer Handoff

> **Prototype repo:** [github.com/thechuch/ebottles](https://github.com/thechuch/ebottles)
> **Live demo:** [thechuch.github.io/ebottles](https://thechuch.github.io/ebottles/)
> **Date:** February 2026

This document covers everything needed to take the eBottles split-screen landing page prototype and implement it in Shopify, plus deploy the AI lead intake backend.

---

## Table of Contents

1. [The Creative Concept](#1-the-creative-concept)
2. [File to Shopify Mapping](#2-file-to-shopify-mapping)
3. [Image Swap Instructions](#3-image-swap-instructions)
4. [Chatbot Widget Guide](#4-chatbot-widget-guide)
5. [Backend Architecture](#5-backend-architecture)
6. [Environment Variables](#6-environment-variables)
7. [Email Service Note](#7-email-service-note)
8. [Backend Hosting](#8-backend-hosting)
9. [Cloud Run Deployment](#9-cloud-run-deployment)
10. [Client Provisioning Checklist](#10-client-provisioning-checklist)
11. [Testing Checklist](#11-testing-checklist)

---

## 1. The Creative Concept

The landing page is a **split-screen "choose your direction"** experience. Visitors see two panels side by side — Cannabis (dark navy, left) and Wellness (light, right). Hover expands one side; click navigates to that category's home page.

### The Image Reveal Trick

The key visual effect: **products appear stationary while the background zone slides**. This is done by photographing products identically against both backgrounds, then using CSS overflow clipping.

```
VIEWPORT (100vw)
+-----------------------------------------------------+
|                                                     |
|  CANNABIS PANEL (50%)  |  WELLNESS PANEL (50%)      |
|  overflow: hidden      |  overflow: hidden           |
|                        |                             |
|  +---IMAGE A (100vw, dark bg)---+                   |
|  |  [bottle] [jar] [dropper]    |  (clipped)        |
|  +------------------------------+                   |
|                        |                             |
|                        |  +---IMAGE B (100vw, light bg)---+
|                        |  |  [bottle] [jar] [dropper]     |
|                        |  +-------------------------------+
|                        |                             |
+-----------------------------------------------------+
         DIVIDER ^

Both images span the full viewport width (100vw).
Both are positioned so products sit at the same absolute X coordinates.
Each panel clips its image via overflow:hidden.

ON HOVER (cannabis expands to 77%):
+----------------------------------------------+------+
|  CANNABIS (77%)                              | W(23)|
|  More of image A is revealed                 |      |
+----------------------------------------------+------+
         DIVIDER slides right ^

Products stay put. Only the clip boundary moves.
```

### How the offset works

- Cannabis panel's image wrapper: `left: 0` (naturally aligned to viewport left)
- Wellness panel's image wrapper: pulled left by a **negative offset** equal to the cannabis panel's pixel width
- This offset is calculated in `js/landing.js` via `updateWellnessOffset()` on a `requestAnimationFrame` loop during transitions
- Result: both images effectively start at the viewport's left edge, so the products line up

### Photography requirements

To make this illusion work, you need:
- **Two product photos** — same products, same positions, different backgrounds
- Dark background (navy `#01426A`) for Cannabis zone
- Light background (`#F2F2F2`) for Wellness zone
- Products must be in **identical pixel positions** across both images
- Minimum 1920px wide (full viewport width)
- Products should be centered or slightly left-of-center for best effect

### Interaction states

| State | CSS Class | Behavior |
|-------|-----------|----------|
| Default | (none) | 50/50 split |
| Hover cannabis | `.is-hover-cannabis` | Left 77%, right 23% |
| Hover wellness | `.is-hover-wellness` | Right 77%, left 23% |
| Click cannabis | `.is-clicked-cannabis` | Left 100%, right fades to 0%, navigates after 850ms |
| Click wellness | `.is-clicked-wellness` | Right 100%, left fades to 0%, navigates after 850ms |
| Mobile | `@media (max-width: 768px)` | Vertical stack, tap only (no hover) |

---

## 2. File to Shopify Mapping

| Prototype File | Shopify Equivalent | Notes |
|---|---|---|
| `index.html` | `templates/index.json` + `sections/landing-split.liquid` | Section with 2 blocks. Each block: `image` (image_picker), `target_url` (url), `label_text` (text) |
| `cannabis.html` | `templates/collection.cannabis.json` | Body class: `template-{{ template.suffix }}` triggers `theme-cannabis` styles |
| `wellness.html` | `templates/collection.wellness.json` | Same pattern, `theme-wellness` |
| `css/variables.css` | Inline `<style>` in `layout/theme.liquid` | Generated from `settings_schema.json` (see below) |
| `css/base.css` | `assets/base.css` | Standard reset; may merge with existing theme reset |
| `css/landing.css` | `assets/section-landing-split.css` | Load only on landing page |
| `js/landing.js` | `assets/section-landing-split.js` | Load with `defer`. **Note:** replace `setTimeout(850)` at line 96 with `transitionend` event |
| `chatbot/frontend/widget.js` | `assets/widget.js` or hosted on backend domain | Self-contained; see Widget Guide below |
| `images/widget-icon-*.svg` | `assets/widget-icon-*.svg` | Branded chat bubble icons |

### settings_schema.json mapping

Every CSS variable in `variables.css` maps to a Shopify theme setting:

```json
{
  "name": "Split Landing Colors",
  "settings": [
    { "type": "color", "id": "color_cannabis_background", "label": "Cannabis Background", "default": "#01426A" },
    { "type": "color", "id": "color_cannabis_text", "label": "Cannabis Text", "default": "#E5ECF0" },
    { "type": "color", "id": "color_cannabis_accent", "label": "Cannabis Accent", "default": "#75CEDE" },
    { "type": "color", "id": "color_wellness_background", "label": "Wellness Background", "default": "#F2F2F2" },
    { "type": "color", "id": "color_wellness_text", "label": "Wellness Text", "default": "#01426A" },
    { "type": "color", "id": "color_wellness_accent", "label": "Wellness Accent", "default": "#75CEDE" }
  ]
}
```

In `theme.liquid`:
```liquid
<style>
  :root {
    --color-cannabis-bg: {{ settings.color_cannabis_background }};
    --color-cannabis-text: {{ settings.color_cannabis_text }};
    --color-cannabis-accent: {{ settings.color_cannabis_accent }};
    --color-wellness-bg: {{ settings.color_wellness_background }};
    --color-wellness-text: {{ settings.color_wellness_text }};
    --color-wellness-accent: {{ settings.color_wellness_accent }};
  }
</style>
```

### Brand colors (from eBottles Figma widget assets)

| Color | Hex | Usage |
|-------|-----|-------|
| Navy | `#01426A` | Cannabis bg, wellness text, widget primary |
| Teal | `#75CEDE` | Accent on all pages, logo "e", widget highlights |
| Light | `#F2F2F2` | Wellness bg |
| Ice | `#E5ECF0` | Cannabis text, wellness bg-alt |

---

## 3. Image Swap Instructions

The prototype uses CSS gradients and SVG bottle shapes as placeholders. To swap in real photography:

### Step 1: In `index.html`, replace each placeholder block

Find (cannabis panel):
```html
<div class="split-screen__placeholder split-screen__placeholder--cannabis">
  <div class="placeholder-bottles">
    <div class="bottle bottle--tall"></div>
    <!-- ...more bottles... -->
  </div>
</div>
```

Replace with:
```html
<img src="images/cannabis-products.jpg"
     alt="Cannabis packaging products"
     style="width:100%; height:100%; object-fit:cover;">
```

Same for the wellness panel.

### Step 2: In Shopify (section block)

```liquid
{{ block.settings.image | image_url: width: 1920 | image_tag:
   style: 'width:100%; height:100%; object-fit:cover;',
   alt: block.settings.label_text }}
```

### Step 3: Remove placeholder CSS

Delete everything in `landing.css` from line 124 (`.split-screen__placeholder`) through line 243 (end of `.bottle` rules). These are only the CSS gradient placeholders.

### Step 4: No JS changes needed

The offset logic in `landing.js` works identically with `<img>` tags.

---

## 4. Chatbot Widget Guide

The widget (`chatbot/frontend/widget.js`) is a **self-contained IIFE** — no dependencies, no external CSS. It creates its own DOM, injects its own styles, and manages all state internally.

### Embedding

Add before `</body>`:

```html
<script
  src="chatbot/frontend/widget.js"
  data-backend-url="https://your-backend-url.com"
  data-calendly-url="https://calendly.com/ebottles"
  data-api-key="your-shared-secret"
  data-icon-src="images/widget-icon-light.svg">
</script>
```

### Data attributes

| Attribute | Required | Description |
|-----------|----------|-------------|
| `data-backend-url` | Yes (for production) | Base URL of the FastAPI backend |
| `data-calendly-url` | No | Calendly link shown after successful submission |
| `data-api-key` | No | Shared secret sent as `X-API-KEY` header |
| `data-icon-src` | No | Path to custom SVG icon (replaces default chat bubble) |

### Icon variants

- **`widget-icon-light.svg`** — Light gray bubble with navy lock. Use on **dark** pages (cannabis).
- **`widget-icon-dark.svg`** — Navy bubble with light lock. Use on **light** pages (wellness).

When `data-icon-src` is set, the button becomes just the floating SVG icon (no pill shape, no text label).

### Shopify snippet

Create `snippets/ebottles-widget.liquid`:

```liquid
<script
  src="{{ 'widget.js' | asset_url }}"
  data-backend-url="{{ settings.widget_backend_url }}"
  data-calendly-url="{{ settings.widget_calendly_url }}"
  data-api-key="{{ settings.widget_api_key }}"
  data-icon-src="{{ settings.widget_icon | asset_url }}">
</script>
```

Include in `theme.liquid` before `</body>`:
```liquid
{% render 'ebottles-widget' %}
```

### What the widget does

1. Floating branded icon button (bottom-right)
2. Click opens modal with lead intake form:
   - Free-text project description (40 char minimum)
   - Voice dictation button (records audio, sends to Whisper API for transcription)
   - Contact fields: name, company, email, phone, role dropdown
3. Submit sends to `POST /lead-intake`
4. Success state shows confirmation + Calendly scheduling link
5. Without a backend, the widget renders fully but shows a graceful error on submit

---

## 5. Backend Architecture

**Stack:** Python 3.12 + FastAPI + Uvicorn

```
chatbot/backend/
  Dockerfile
  requirements.txt
  app/
    main.py              # FastAPI app, CORS, health check
    config.py            # Env var management (Pydantic Settings)
    security.py          # Optional X-API-KEY gate
    models/
      schemas.py         # Request/response Pydantic models
    routes/
      lead_intake.py     # POST /lead-intake
      transcribe.py      # POST /transcribe
    services/
      openai_service.py  # GPT-5.1 extraction + Whisper transcription
      sheets_service.py  # Google Sheets append
      gmail_service.py   # Email notifications (see Section 7)
```

### API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check (`{"status": "healthy"}`) |
| `POST` | `/lead-intake` | Process lead submission |
| `POST` | `/transcribe` | Audio file to text (Whisper) |

### POST /lead-intake flow

```
Request body (JSON):
  freeform_note: string (40+ chars)
  contact: { name, company, email, phone? }
  role: string?
  metadata: { source, page_url }

Step 1: AI EXTRACTION (non-fatal)
  GPT-5.1 extracts structured data:
  - product_types, intended_use, markets
  - estimated_monthly_volume, timeline
  - budget_sensitivity, priority_band
  - ai_summary (2-3 sentences for sales)
  Falls back to truncated summary if AI fails.

Step 2: GOOGLE SHEETS APPEND (fatal)
  23-column row: timestamp, lead_id, contact,
  raw note, extracted fields, status.
  If this fails -> returns 500 (cannot lose the lead).

Step 3: SALES NOTIFICATION EMAIL (non-fatal)
  Sends to notification_email + admin list.
  Priority emoji in subject (high/medium/low).

Step 4: LEAD CONFIRMATION EMAIL (non-fatal)
  Sends confirmation to submitter's email.

Response:
  { status: "ok", lead_id: "LEAD-XXXXXXXX", message: "..." }
```

### POST /transcribe flow

```
Request: multipart/form-data with "audio" file
  Accepted: webm, mp3, wav, m4a, ogg (10MB max)

Sends to OpenAI Whisper API (whisper-1 model).

Response:
  { status: "ok", text: "transcribed text" }
```

### Mock service fallback

If Google credentials are not configured, the backend uses `MockSheetsService` and `MockGmailService` which log instead of making real API calls. This means the backend runs without crashing even without credentials — useful for local development and frontend testing.

---

## 6. Environment Variables

Copy `chatbot/backend/.env.example` to `.env` and fill in real values.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | `""` | OpenAI API key (needs GPT-5.1 + Whisper access) |
| `OPENAI_MODEL` | No | `"gpt-5.1"` | Model for lead extraction |
| `OPENAI_TIMEOUT_S` | No | `30.0` | Timeout for OpenAI calls |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes* | `""` | Raw JSON string of service account |
| `GOOGLE_SERVICE_ACCOUNT_JSON_B64` | Yes* | `""` | Base64-encoded JSON (preferred for env vars) |
| `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` | Yes* | `""` | File path to JSON (preferred for Cloud Run) |
| `GOOGLE_SHEET_ID` | Yes | `""` | ID from the Google Sheet URL |
| `NOTIFICATION_EMAIL` | No | `"sales@ebottles.com"` | Primary sales notification recipient |
| `NOTIFICATION_FROM_EMAIL` | No | `"noreply@ebottles.com"` | Sender email |
| `ADMIN_NOTIFICATION_EMAILS` | No | `""` | Comma-separated extra recipients |
| `ALLOWED_ORIGINS` | Yes | localhost | Comma-separated CORS origins |
| `API_KEY` | No | `""` | Shared secret (empty = no auth) |
| `DEBUG` | No | `false` | Verbose logging |

*Only one of the three `GOOGLE_SERVICE_ACCOUNT_JSON*` variables is needed.

---

## 7. Email Service Note

The backend currently uses **Gmail API with Google Workspace domain-wide delegation** for sending emails. This requires:
- A Google Workspace domain (not consumer Gmail)
- Domain-wide delegation enabled in the Workspace Admin Console
- A real mailbox for the "from" address

**If the client does not use Google Workspace** (e.g., uses Microsoft 365 / Teams), the Gmail service will not work. Recommended alternatives:

| Service | Pros | Setup Time |
|---------|------|-----------|
| **Resend** | Simple API, good free tier (100 emails/day), modern DX | ~30 min |
| **SendGrid** | Battle-tested, generous free tier (100/day), good docs | ~1 hour |
| **Postmark** | Best deliverability, focused on transactional email | ~1 hour |

The swap is straightforward: replace `gmail_service.py` with a new service that calls the chosen provider's API. The `send_notification()` and `send_lead_confirmation()` method signatures stay the same. The mock fallback pattern already handles the case where email is not configured.

The Google Sheets integration is **not affected** — it only needs a Google Cloud service account (no Workspace required).

---

## 8. Backend Hosting

The backend needs a Python host. GitHub Pages and Netlify cannot run it.

| Platform | Pros | Cons | Cost |
|----------|------|------|------|
| **Google Cloud Run** (recommended) | Dockerfile ready, native Google Sheets/Gmail integration, auto-scales to zero, health check compatible | Requires GCP account, cold starts (~2-5s) | Free tier: 2M requests/month |
| **Railway** | GitHub deploy, simple UI, auto-detects Dockerfile | No native Google integration, no free tier | ~$5-10/month |
| **Render** | Free tier available, Dockerfile support | Free tier spins down (30s+ cold starts) | Free or $7/month |
| **Fly.io** | Global edge, Dockerfile native | More complex CLI | Free for 3 VMs |

**Recommendation:** Cloud Run. The Dockerfile is already optimized for it, the health check endpoint works with Cloud Run probes, and credentials can be mounted as secret volumes.

---

## 9. Cloud Run Deployment

### Prerequisites
1. [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) installed
2. A Google Cloud project with billing enabled
3. Cloud Run API, Sheets API enabled

### Steps

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs
gcloud services enable run.googleapis.com sheets.googleapis.com

# 3. Create a service account for Sheets
gcloud iam service-accounts create ebottles-sheets \
  --display-name="eBottles Sheets Writer"

# 4. Download the service account key
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=ebottles-sheets@YOUR_PROJECT.iam.gserviceaccount.com

# 5. Store it as a Cloud Run secret
gcloud secrets create sa-json --data-file=sa-key.json
rm sa-key.json  # don't leave keys on disk

# 6. Create the Google Sheet and share it (Editor) with:
#    ebottles-sheets@YOUR_PROJECT.iam.gserviceaccount.com
#    Copy the Sheet ID from the URL.

# 7. Deploy
gcloud run deploy ebottles-ai-intake \
  --source chatbot/backend/ \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "OPENAI_API_KEY=sk-xxx,GOOGLE_SHEET_ID=xxx,ALLOWED_ORIGINS=https://www.ebottles.com,API_KEY=your-shared-secret" \
  --set-secrets "GOOGLE_SERVICE_ACCOUNT_JSON_PATH=/secrets/sa/key.json:sa-json:latest" \
  --update-secrets "/secrets/sa/key.json=sa-json:latest"

# 8. Verify
curl https://SERVICE_URL/health
# Should return: {"status":"healthy","service":"ebottles-ai-intake"}

# 9. Update the widget's data-backend-url to the Cloud Run URL
```

---

## 10. Client Provisioning Checklist

Everything the client (eBottles) needs to provide or set up:

### API Keys and Credentials
- [ ] OpenAI API key with GPT-5.1 and Whisper access
- [ ] Google Cloud project (for Sheets integration)
- [ ] Google Cloud service account JSON key
- [ ] Google Sheet created and shared with the service account email (Editor access)
- [ ] Google Sheet ID (from URL: `docs.google.com/spreadsheets/d/{THIS_ID}/`)

### Email (choose one)
- [ ] Resend API key + verified domain, **OR**
- [ ] SendGrid API key + verified sender, **OR**
- [ ] Google Workspace with domain-wide delegation (complex, not recommended)

### Content
- [ ] Two product photos for split-screen (dark bg + light bg, identical positions, 1920px+ wide)
- [ ] eBottles logo file (SVG preferred, for Shopify header)
- [ ] Calendly URL for the widget success state

### Hosting
- [ ] Backend hosting decision (Cloud Run recommended)
- [ ] Domain or subdomain for backend API (e.g., `api.ebottles.com`)
- [ ] CORS origins list (Shopify storefront domains)

### Security
- [ ] Shared API key for widget-to-backend authentication

---

## 11. Testing Checklist

### Frontend
- [ ] Landing page loads at 50/50 split
- [ ] Hover left: expands to ~77%, products stay stationary
- [ ] Hover right: same, reversed
- [ ] Click left: takes 100%, navigates to cannabis page
- [ ] Click right: takes 100%, navigates to wellness page
- [ ] Mobile (768px): panels stack vertically, tap only
- [ ] Logo "e" uses teal accent `#75CEDE`
- [ ] CSS variables match brand colors

### Widget
- [ ] Branded icon appears bottom-right on both home pages
- [ ] Light icon on dark page, dark icon on light page
- [ ] Click opens modal form
- [ ] Form validates (40-char min, required fields)
- [ ] Voice button requests microphone permission
- [ ] Without backend: graceful error message on submit

### Backend
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `POST /lead-intake` returns `{status: "ok", lead_id: "LEAD-..."}` with valid payload
- [ ] `POST /transcribe` returns transcribed text from audio file
- [ ] Lead appears as new row in Google Sheet
- [ ] Sales notification email received
- [ ] Confirmation email received by lead
- [ ] CORS allows requests from Shopify domain (no browser console errors)
- [ ] `X-API-KEY` enforcement works when `API_KEY` is set
- [ ] Mock services activate when credentials are absent (no crash)

### Production
- [ ] Backend cold start time acceptable (<5 seconds)
- [ ] Widget `data-backend-url` points to production backend
- [ ] All env vars set in hosting platform
- [ ] HTTPS on both frontend and backend
