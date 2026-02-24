# eBottles — Документ передачі для розробників

> **Репозиторій прототипу:** [github.com/thechuch/ebottles](https://github.com/thechuch/ebottles)
> **Демо:** [thechuch.github.io/ebottles](https://thechuch.github.io/ebottles/)
> **Дата:** Лютий 2026

Цей документ містить все необхідне для реалізації прототипу лендінг-сторінки eBottles у Shopify та розгортання бекенду для прийому лідів з AI.

---

## Зміст

1. [Креативна концепція](#1-креативна-концепція)
2. [Маппінг файлів до Shopify](#2-маппінг-файлів-до-shopify)
3. [Заміна зображень](#3-заміна-зображень)
4. [Гід по віджету чат-бота](#4-гід-по-віджету-чат-бота)
5. [Архітектура бекенду](#5-архітектура-бекенду)
6. [Змінні середовища](#6-змінні-середовища)
7. [Примітка щодо email-сервісу](#7-примітка-щодо-email-сервісу)
8. [Хостинг бекенду](#8-хостинг-бекенду)
9. [Розгортання на Cloud Run](#9-розгортання-на-cloud-run)
10. [Чекліст для клієнта](#10-чекліст-для-клієнта)
11. [Чекліст тестування](#11-чекліст-тестування)

---

## 1. Креативна концепція

Лендінг-сторінка — це **розділений екран "обери свій напрямок"**. Відвідувачі бачать дві панелі поруч — Cannabis (темно-синій, ліворуч) та Wellness (світлий, праворуч). Наведення розширює одну сторону; клік переходить на домашню сторінку категорії.

### Трюк з відкриттям зображення

Ключовий візуальний ефект: **продукти залишаються нерухомими, а фонова зона ковзає**. Це досягається за допомогою ідентичних фото продуктів на обох фонах та CSS-обрізки через overflow.

```
VIEWPORT (100vw)
+-----------------------------------------------------+
|                                                     |
|  ПАНЕЛЬ CANNABIS (50%)  |  ПАНЕЛЬ WELLNESS (50%)    |
|  overflow: hidden       |  overflow: hidden          |
|                         |                            |
|  +---ЗОБРАЖЕННЯ A (100vw, темний фон)---+           |
|  |  [пляшка] [банка] [дозатор]          | (обрізано) |
|  +--------------------------------------+           |
|                         |                            |
|                         | +---ЗОБРАЖЕННЯ B (100vw, світлий фон)---+
|                         | |  [пляшка] [банка] [дозатор]           |
|                         | +---------------------------------------+
|                         |                            |
+-----------------------------------------------------+
         РОЗДІЛЬНИК ^

Обидва зображення займають повну ширину viewport (100vw).
Обидва розташовані так, що продукти знаходяться на тих самих X-координатах.
Кожна панель обрізає своє зображення через overflow:hidden.

ПРИ НАВЕДЕННІ (cannabis розширюється до 77%):
+----------------------------------------------+------+
|  CANNABIS (77%)                              | W(23)|
|  Більше зображення A стає видимим            |      |
+----------------------------------------------+------+
         РОЗДІЛЬНИК зсувається праворуч ^

Продукти залишаються на місці. Зсувається лише межа обрізки.
```

### Як працює зсув

- Image wrapper панелі Cannabis: `left: 0` (природно вирівняний до лівого краю viewport)
- Image wrapper панелі Wellness: зсунутий вліво на **від'ємне значення**, що дорівнює ширині панелі Cannabis у пікселях
- Цей зсув розраховується в `js/landing.js` через `updateWellnessOffset()` у циклі `requestAnimationFrame` під час переходів
- Результат: обидва зображення фактично починаються з лівого краю viewport, тому продукти збігаються

### Вимоги до фотографій

Щоб ілюзія працювала, потрібно:
- **Два фото продуктів** — ті самі продукти, ті самі позиції, різні фони
- Темний фон (navy `#01426A`) для зони Cannabis
- Світлий фон (`#F2F2F2`) для зони Wellness
- Продукти повинні бути в **ідентичних піксельних позиціях** на обох зображеннях
- Мінімум 1920px завширшки (повна ширина viewport)
- Продукти повинні бути по центру або трохи лівіше центру

### Стани взаємодії

| Стан | CSS-клас | Поведінка |
|------|----------|-----------|
| За замовчуванням | (немає) | Поділ 50/50 |
| Наведення на Cannabis | `.is-hover-cannabis` | Ліва 77%, права 23% |
| Наведення на Wellness | `.is-hover-wellness` | Права 77%, ліва 23% |
| Клік на Cannabis | `.is-clicked-cannabis` | Ліва 100%, права зникає до 0%, навігація через 850мс |
| Клік на Wellness | `.is-clicked-wellness` | Права 100%, ліва зникає до 0%, навігація через 850мс |
| Мобільний | `@media (max-width: 768px)` | Вертикальний стек, тільки тап (без наведення) |

---

## 2. Маппінг файлів до Shopify

| Файл прототипу | Еквівалент у Shopify | Примітки |
|---|---|---|
| `index.html` | `templates/index.json` + `sections/landing-split.liquid` | Секція з 2 блоками. Кожен блок: `image` (image_picker), `target_url` (url), `label_text` (text) |
| `cannabis.html` | `templates/collection.cannabis.json` | Body class: `template-{{ template.suffix }}` активує стилі `theme-cannabis` |
| `wellness.html` | `templates/collection.wellness.json` | Та сама схема, `theme-wellness` |
| `css/variables.css` | Inline `<style>` у `layout/theme.liquid` | Генерується з `settings_schema.json` (див. нижче) |
| `css/base.css` | `assets/base.css` | Стандартний reset; може об'єднатися з існуючим reset теми |
| `css/landing.css` | `assets/section-landing-split.css` | Завантажувати тільки на лендінгу |
| `js/landing.js` | `assets/section-landing-split.js` | Завантажувати з `defer`. **Увага:** замініть `setTimeout(850)` на рядку 96 на подію `transitionend` |
| `chatbot/frontend/widget.js` | `assets/widget.js` або хост на домені бекенду | Самодостатній; див. Гід по віджету нижче |
| `images/widget-icon-*.svg` | `assets/widget-icon-*.svg` | Брендовані іконки чат-бульбашки |

### Маппінг settings_schema.json

Кожна CSS-змінна у `variables.css` відповідає налаштуванню теми Shopify:

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

У `theme.liquid`:
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

### Кольори бренду (з Figma-ассетів eBottles)

| Колір | Hex | Використання |
|-------|-----|-------------|
| Navy | `#01426A` | Фон Cannabis, текст Wellness, основний колір віджету |
| Teal | `#75CEDE` | Акцент на всіх сторінках, логотип "e", підсвітка віджету |
| Light | `#F2F2F2` | Фон Wellness |
| Ice | `#E5ECF0` | Текст Cannabis, альтернативний фон Wellness |

---

## 3. Заміна зображень

Прототип використовує CSS-градієнти та SVG-силуети пляшок як заглушки. Для заміни реальними фото:

### Крок 1: В `index.html` замініть кожен блок-заглушку

Знайдіть (панель Cannabis):
```html
<div class="split-screen__placeholder split-screen__placeholder--cannabis">
  <div class="placeholder-bottles">
    <div class="bottle bottle--tall"></div>
    <!-- ...інші пляшки... -->
  </div>
</div>
```

Замініть на:
```html
<img src="images/cannabis-products.jpg"
     alt="Cannabis packaging products"
     style="width:100%; height:100%; object-fit:cover;">
```

Те саме для панелі Wellness.

### Крок 2: У Shopify (блок секції)

```liquid
{{ block.settings.image | image_url: width: 1920 | image_tag:
   style: 'width:100%; height:100%; object-fit:cover;',
   alt: block.settings.label_text }}
```

### Крок 3: Видаліть CSS заглушок

Видаліть все в `landing.css` з рядка 124 (`.split-screen__placeholder`) по рядок 243 (кінець правил `.bottle`). Це тільки CSS-градієнтні заглушки.

### Крок 4: Зміни в JS не потрібні

Логіка зсуву в `landing.js` працює ідентично з тегами `<img>`.

---

## 4. Гід по віджету чат-бота

Віджет (`chatbot/frontend/widget.js`) — це **самодостатній IIFE** — без залежностей, без зовнішнього CSS. Він створює власний DOM, інжектить власні стилі та керує всім станом внутрішньо.

### Вбудовування

Додайте перед `</body>`:

```html
<script
  src="chatbot/frontend/widget.js"
  data-backend-url="https://your-backend-url.com"
  data-calendly-url="https://calendly.com/ebottles"
  data-api-key="your-shared-secret"
  data-icon-src="images/widget-icon-light.svg">
</script>
```

### Data-атрибути

| Атрибут | Обов'язковий | Опис |
|---------|-------------|------|
| `data-backend-url` | Так (для продакшну) | Базова URL бекенду FastAPI |
| `data-calendly-url` | Ні | Посилання Calendly після успішної відправки |
| `data-api-key` | Ні | Спільний секрет, відправляється як заголовок `X-API-KEY` |
| `data-icon-src` | Ні | Шлях до SVG-іконки (замінює стандартну бульбашку чату) |

### Варіанти іконок

- **`widget-icon-light.svg`** — Світла бульбашка з темним замком. Використовуйте на **темних** сторінках (Cannabis).
- **`widget-icon-dark.svg`** — Темна бульбашка зі світлим замком. Використовуйте на **світлих** сторінках (Wellness).

Коли встановлено `data-icon-src`, кнопка стає просто плаваючою SVG-іконкою (без форми пілюлі, без текстової мітки).

### Сніпет Shopify

Створіть `snippets/ebottles-widget.liquid`:

```liquid
<script
  src="{{ 'widget.js' | asset_url }}"
  data-backend-url="{{ settings.widget_backend_url }}"
  data-calendly-url="{{ settings.widget_calendly_url }}"
  data-api-key="{{ settings.widget_api_key }}"
  data-icon-src="{{ settings.widget_icon | asset_url }}">
</script>
```

Підключіть у `theme.liquid` перед `</body>`:
```liquid
{% render 'ebottles-widget' %}
```

### Що робить віджет

1. Плаваюча брендована іконка-кнопка (внизу праворуч)
2. Клік відкриває модальне вікно з формою прийому лідів:
   - Вільний текстовий опис проєкту (мінімум 40 символів)
   - Кнопка голосової диктовки (записує аудіо, відправляє на Whisper API для транскрипції)
   - Контактні поля: ім'я, компанія, email, телефон, випадаючий список ролей
3. Відправка надсилає на `POST /lead-intake`
4. Стан успіху показує підтвердження + посилання для запису через Calendly
5. Без бекенду віджет повністю відображається, але показує коректне повідомлення про помилку при відправці

---

## 5. Архітектура бекенду

**Стек:** Python 3.12 + FastAPI + Uvicorn

```
chatbot/backend/
  Dockerfile
  requirements.txt
  app/
    main.py              # FastAPI додаток, CORS, health check
    config.py            # Управління змінними середовища (Pydantic Settings)
    security.py          # Опціональна перевірка X-API-KEY
    models/
      schemas.py         # Pydantic моделі запитів/відповідей
    routes/
      lead_intake.py     # POST /lead-intake
      transcribe.py      # POST /transcribe
    services/
      openai_service.py  # Екстракція GPT-5.1 + транскрипція Whisper
      sheets_service.py  # Запис у Google Sheets
      gmail_service.py   # Email-повідомлення (див. Розділ 7)
```

### API ендпоінти

| Метод | Шлях | Призначення |
|-------|------|-------------|
| `GET` | `/` | Інформація про сервіс |
| `GET` | `/health` | Перевірка стану (`{"status": "healthy"}`) |
| `POST` | `/lead-intake` | Обробка відправки ліда |
| `POST` | `/transcribe` | Аудіофайл у текст (Whisper) |

### Потік POST /lead-intake

```
Тіло запиту (JSON):
  freeform_note: string (40+ символів)
  contact: { name, company, email, phone? }
  role: string?
  metadata: { source, page_url }

Крок 1: AI ЕКСТРАКЦІЯ (не фатальна)
  GPT-5.1 витягує структуровані дані:
  - product_types, intended_use, markets
  - estimated_monthly_volume, timeline
  - budget_sensitivity, priority_band
  - ai_summary (2-3 речення для відділу продажів)
  При збої AI — повертається скорочене резюме.

Крок 2: ЗАПИС У GOOGLE SHEETS (фатальний)
  Рядок з 23 колонок: timestamp, lead_id, контакти,
  сирий текст, витягнуті поля, статус.
  Якщо збій -> повертає 500 (не можна втратити лід).

Крок 3: EMAIL ВІДДІЛУ ПРОДАЖІВ (не фатальний)
  Надсилає на notification_email + список адмінів.
  Емодзі пріоритету в темі (високий/середній/низький).

Крок 4: EMAIL ПІДТВЕРДЖЕННЯ ЛІДУ (не фатальний)
  Надсилає підтвердження на email відправника.

Відповідь:
  { status: "ok", lead_id: "LEAD-XXXXXXXX", message: "..." }
```

### Потік POST /transcribe

```
Запит: multipart/form-data з файлом "audio"
  Прийнятні формати: webm, mp3, wav, m4a, ogg (макс. 10МБ)

Відправляє на OpenAI Whisper API (модель whisper-1).

Відповідь:
  { status: "ok", text: "транскрибований текст" }
```

### Фолбек на мок-сервіси

Якщо облікові дані Google не налаштовані, бекенд використовує `MockSheetsService` та `MockGmailService`, які логують замість реальних API-викликів. Це означає, що бекенд працює без помилок навіть без облікових даних — зручно для локальної розробки та тестування фронтенду.

---

## 6. Змінні середовища

Скопіюйте `chatbot/backend/.env.example` у `.env` та заповніть реальними значеннями.

| Змінна | Обов'язкова | За замовчуванням | Опис |
|--------|------------|------------------|------|
| `OPENAI_API_KEY` | Так | `""` | API-ключ OpenAI (потрібен доступ до GPT-5.1 + Whisper) |
| `OPENAI_MODEL` | Ні | `"gpt-5.1"` | Модель для екстракції лідів |
| `OPENAI_TIMEOUT_S` | Ні | `30.0` | Таймаут для запитів OpenAI |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Так* | `""` | JSON-рядок сервісного акаунта |
| `GOOGLE_SERVICE_ACCOUNT_JSON_B64` | Так* | `""` | Base64-закодований JSON (рекомендовано для env vars) |
| `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` | Так* | `""` | Шлях до JSON-файлу (рекомендовано для Cloud Run) |
| `GOOGLE_SHEET_ID` | Так | `""` | ID з URL Google Sheet |
| `NOTIFICATION_EMAIL` | Ні | `"sales@ebottles.com"` | Основний отримувач повідомлень |
| `NOTIFICATION_FROM_EMAIL` | Ні | `"noreply@ebottles.com"` | Email відправника |
| `ADMIN_NOTIFICATION_EMAILS` | Ні | `""` | Додаткові отримувачі через кому |
| `ALLOWED_ORIGINS` | Так | localhost | CORS-джерела через кому |
| `API_KEY` | Ні | `""` | Спільний секрет (порожній = без автентифікації) |
| `DEBUG` | Ні | `false` | Детальне логування |

*Потрібна лише одна з трьох змінних `GOOGLE_SERVICE_ACCOUNT_JSON*`.

---

## 7. Примітка щодо email-сервісу

Бекенд наразі використовує **Gmail API з делегуванням на рівні домену Google Workspace** для відправки листів. Це вимагає:
- Домен Google Workspace (не споживчий Gmail)
- Увімкнене делегування на рівні домену в консолі адміністратора Workspace
- Реальну поштову скриньку для адреси відправника

**Якщо клієнт не використовує Google Workspace** (наприклад, використовує Microsoft 365 / Teams), сервіс Gmail працювати не буде. Рекомендовані альтернативи:

| Сервіс | Переваги | Час налаштування |
|--------|----------|-----------------|
| **Resend** | Простий API, хороший безкоштовний план (100 листів/день), сучасний DX | ~30 хв |
| **SendGrid** | Перевірений часом, щедрий безкоштовний план (100/день), хороша документація | ~1 година |
| **Postmark** | Найкраща доставляємість, орієнтований на транзакційні листи | ~1 година |

Заміна проста: замініть `gmail_service.py` новим сервісом, який викликає API обраного провайдера. Сигнатури методів `send_notification()` та `send_lead_confirmation()` залишаються тими самими. Паттерн фолбеку на мок вже обробляє випадок, коли email не налаштований.

Інтеграція з Google Sheets **не зачіпається** — потрібен лише сервісний акаунт Google Cloud (без Workspace).

---

## 8. Хостинг бекенду

Бекенд потребує хост для Python. GitHub Pages та Netlify не можуть його запустити.

| Платформа | Переваги | Недоліки | Вартість |
|-----------|----------|----------|----------|
| **Google Cloud Run** (рекомендовано) | Dockerfile готовий, нативна інтеграція з Google Sheets, авто-масштабування до нуля, сумісний health check | Потрібен акаунт GCP, холодний старт (~2-5с) | Безкоштовно: 2М запитів/місяць |
| **Railway** | Деплой через GitHub, простий UI, авто-визначення Dockerfile | Немає нативної інтеграції з Google, без безкоштовного плану | ~$5-10/міс |
| **Render** | Є безкоштовний план, підтримка Dockerfile | Безкоштовний план вимикається (30с+ холодний старт) | Безкоштовно або $7/міс |
| **Fly.io** | Глобальний edge, нативний Dockerfile | Складніший CLI | Безкоштовно для 3 VM |

**Рекомендація:** Cloud Run. Dockerfile вже оптимізований для нього, ендпоінт health check працює з пробами Cloud Run, а облікові дані можна монтувати як секретні томи.

---

## 9. Розгортання на Cloud Run

### Передумови
1. [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) встановлений
2. Проєкт Google Cloud з увімкненим білінгом
3. Увімкнені API: Cloud Run, Sheets

### Кроки

```bash
# 1. Автентифікація
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Увімкнення API
gcloud services enable run.googleapis.com sheets.googleapis.com

# 3. Створення сервісного акаунта для Sheets
gcloud iam service-accounts create ebottles-sheets \
  --display-name="eBottles Sheets Writer"

# 4. Завантаження ключа сервісного акаунта
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=ebottles-sheets@YOUR_PROJECT.iam.gserviceaccount.com

# 5. Збереження як секрет Cloud Run
gcloud secrets create sa-json --data-file=sa-key.json
rm sa-key.json  # не залишайте ключі на диску

# 6. Створіть Google Sheet та надайте доступ (Редактор):
#    ebottles-sheets@YOUR_PROJECT.iam.gserviceaccount.com
#    Скопіюйте Sheet ID з URL.

# 7. Деплой
gcloud run deploy ebottles-ai-intake \
  --source chatbot/backend/ \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "OPENAI_API_KEY=sk-xxx,GOOGLE_SHEET_ID=xxx,ALLOWED_ORIGINS=https://www.ebottles.com,API_KEY=your-shared-secret" \
  --set-secrets "GOOGLE_SERVICE_ACCOUNT_JSON_PATH=/secrets/sa/key.json:sa-json:latest" \
  --update-secrets "/secrets/sa/key.json=sa-json:latest"

# 8. Перевірка
curl https://SERVICE_URL/health
# Повинен повернути: {"status":"healthy","service":"ebottles-ai-intake"}

# 9. Оновіть data-backend-url віджету на URL Cloud Run
```

---

## 10. Чекліст для клієнта

Все, що клієнт (eBottles) повинен надати або налаштувати:

### API-ключі та облікові дані
- [ ] API-ключ OpenAI з доступом до GPT-5.1 та Whisper
- [ ] Проєкт Google Cloud (для інтеграції зі Sheets)
- [ ] JSON-ключ сервісного акаунта Google Cloud
- [ ] Створена Google Sheet з наданим доступом сервісному акаунту (Редактор)
- [ ] ID Google Sheet (з URL: `docs.google.com/spreadsheets/d/{ЦЕЙ_ID}/`)

### Email (оберіть один)
- [ ] API-ключ Resend + верифікований домен, **АБО**
- [ ] API-ключ SendGrid + верифікований відправник, **АБО**
- [ ] Google Workspace з делегуванням на рівні домену (складно, не рекомендовано)

### Контент
- [ ] Два фото продуктів для розділеного екрану (темний фон + світлий фон, ідентичні позиції, 1920px+ завширшки)
- [ ] Файл логотипу eBottles (бажано SVG, для шапки Shopify)
- [ ] URL Calendly для стану успіху віджету

### Хостинг
- [ ] Рішення щодо хостингу бекенду (рекомендовано Cloud Run)
- [ ] Домен або піддомен для API бекенду (наприклад, `api.ebottles.com`)
- [ ] Список CORS-джерел (домени Shopify-магазину)

### Безпека
- [ ] Спільний API-ключ для автентифікації віджет-бекенд

---

## 11. Чекліст тестування

### Фронтенд
- [ ] Лендінг завантажується з поділом 50/50
- [ ] Наведення ліворуч: розширюється до ~77%, продукти залишаються нерухомими
- [ ] Наведення праворуч: те саме, у зворотному напрямку
- [ ] Клік ліворуч: займає 100%, перехід на сторінку Cannabis
- [ ] Клік праворуч: займає 100%, перехід на сторінку Wellness
- [ ] Мобільний (768px): панелі вертикально, тільки тап
- [ ] Літера "e" в логотипі використовує акцент teal `#75CEDE`
- [ ] CSS-змінні відповідають кольорам бренду

### Віджет
- [ ] Брендована іконка з'являється внизу праворуч на обох сторінках
- [ ] Світла іконка на темній сторінці, темна іконка на світлій
- [ ] Клік відкриває модальну форму
- [ ] Форма валідує (мін. 40 символів, обов'язкові поля)
- [ ] Кнопка голосу запитує дозвіл на мікрофон
- [ ] Без бекенду: коректне повідомлення про помилку при відправці

### Бекенд
- [ ] `GET /health` повертає `{"status": "healthy"}`
- [ ] `POST /lead-intake` повертає `{status: "ok", lead_id: "LEAD-..."}` з валідним payload
- [ ] `POST /transcribe` повертає транскрибований текст з аудіофайлу
- [ ] Лід з'являється як новий рядок у Google Sheet
- [ ] Email-повідомлення отримане відділом продажів
- [ ] Email підтвердження отриманий лідом
- [ ] CORS дозволяє запити з домену Shopify (без помилок CORS у консолі браузера)
- [ ] Перевірка `X-API-KEY` працює, коли `API_KEY` встановлено
- [ ] Мок-сервіси активуються при відсутності облікових даних (без збоїв)

### Продакшн
- [ ] Час холодного старту бекенду прийнятний (<5 секунд)
- [ ] `data-backend-url` віджету вказує на продакшн бекенд
- [ ] Всі змінні середовища встановлені на хостинг-платформі
- [ ] HTTPS на фронтенді та бекенді
