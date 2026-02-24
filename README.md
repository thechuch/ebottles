# eBottles — Landing Page Prototype + AI Chatbot

Two tools for [eBottles](https://www.ebottles.com) (child-resistant packaging):

## 1. Landing Page Prototype

**Live preview:** [https://thechuch.github.io/ebottles/](https://thechuch.github.io/ebottles/)

Interactive split-screen landing page where visitors choose between **Cannabis** (dark navy theme) and **Wellness** (light cream theme) packaging.

**How it works:**
- Default: 50/50 split
- Hover: hovered side expands to ~77%, other shrinks
- Click: selected side takes over 100%, then navigates to themed home page
- Mobile: panels stack vertically

**For Shopify developers** — see code comments for section/block mapping. CSS variables in `css/variables.css` map to Shopify `settings_schema.json`.

**Swapping in real photos:**
1. Place images in `images/` folder
2. In `index.html`, replace each `<div class="split-screen__placeholder ...">` block with:
   ```html
   <img src="images/your-photo.jpg" alt="..." style="width:100%;height:100%;object-fit:cover;">
   ```
3. Remove placeholder CSS from `css/landing.css` (gradient + bottle shape rules)
4. No JavaScript changes needed

**Files:**
```
index.html          → Split-screen landing page
cannabis.html       → Cannabis home page (minimal)
wellness.html       → Wellness home page (minimal)
css/variables.css   → Theme colors (maps to Shopify settings)
css/landing.css     → All styles + animations
js/landing.js       → Hover/click/mobile logic
```

---

## 2. AI Lead Intake Chatbot

Embeddable widget that captures packaging inquiries using GPT-4o, stores leads in Google Sheets, and sends email notifications.

**Details:** See [`chatbot/README.md`](chatbot/README.md)

**Files:** `chatbot/frontend/` (widget JS) + `chatbot/backend/` (Python/FastAPI API)
