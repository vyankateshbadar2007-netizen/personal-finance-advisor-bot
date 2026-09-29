# Personal Finance Advisor Bot

AI-powered personal financial planning assistant built for the SkillWallet project workflow.

## What it does

The application combines:

- Monthly income tracking
- Category-based expense tracking
- Daily/weekly/monthly expense logging
- Personalized monthly budget generation
- Spending analysis
- Saving suggestions
- Goal-based planning
- Monthly financial reporting
- Flask backend
- SQLAlchemy + SQLite persistence
- Gemini AI integration
- Optional Google Sheets tracking
- LocalStorage browser history
- Ngrok public tunnelling

## SkillWallet project mapping

### Epic 1 — Model Selection and Architecture
- Gemini API key configuration
- Model selection
- Application architecture
- Development environment setup

### Epic 2 — Core Functionalities
- Budget generator
- Spending analyser
- Saving suggestions
- Flask backend

### Epic 3 — App.py
- Home route `/`
- Analysis route `/analyse`
- Generation route `/generate`
- Prompt helpers
- JSON extraction
- AI + local fallback

### Epic 4 — Frontend
- Single-page responsive UI
- Dynamic result rendering
- Charts/visual indicators and structured cards
- Async Fetch API submission

### Epic 5 — Deployment
- Local Flask deployment
- Local testing
- Ngrok public deployment

### Conclusion
- Documentation and final project notes

## Architecture

```text
Browser
  |
  | AJAX / Fetch
  v
Flask
  |
  +--> Validation + prompt construction
  |
  +--> SQLAlchemy
  |      |
  |      +--> SQLite
  |
  +--> Gemini API
  |
  +--> Google Apps Script / Sheets (optional)
  |
  +--> Local rule-based fallback
```

## Project structure

```text
personal-finance-advisor-bot/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── run_public.py
├── google_apps_script.gs
├── index.html
├── README.md
├── QUICKSTART.md
├── IMPLEMENTATION_SUMMARY.md
├── DEPLOYMENT_CHECKLIST.md
├── PROJECT_DELIVERY_SUMMARY.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

## Installation

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your Gemini API key.

Run:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Gemini AI

The SkillWallet brief specifies Gemini AI and names `gemini-2.0-flash`. Google's current model catalog marks `gemini-2.0-flash` as shut down, so this implementation uses the configurable `GEMINI_MODEL` variable and defaults to `gemini-2.5-flash`. Change it in `.env` when a different supported model is required.

The integration uses the current Google GenAI Python SDK pattern:

```python
from google import genai

client = genai.Client(api_key=...)
response = client.models.generate_content(
    model="...",
    contents="..."
)
```

## Google Sheets

A ready-to-copy Apps Script template is included in `google_apps_script.gs`. Create a Google Sheet, open Extensions -> Apps Script, paste the template, deploy it as a web app, and then set:

```env
GOOGLE_SHEETS_WEBHOOK_URL=https://your-web-app-url
```

Google Sheets is an optional cloud tracking layer. SQLite remains the local persistence layer so the application still works when Sheets is not configured.

## Ngrok

Set:

```env
NGROK_AUTHTOKEN=your_token
```

Run:

```bash
python run_public.py
```

The terminal prints a public HTTPS URL.

## API

### GET `/api/health`

Returns app/database/AI configuration status.

### POST `/analyse`

Request:

```json
{
  "income": 50000,
  "goal": "emergency fund",
  "expenses": {
    "rent": 12000,
    "food": 6000,
    "transport": 3000,
    "dining": 2000,
    "entertainment": 1500,
    "utilities": 3000,
    "savings": 5000
  },
  "expense_logs": []
}
```

Returns:

```json
{
  "success": true,
  "source": "gemini",
  "budget": [],
  "analysis": [],
  "suggestions": [],
  "summary": {},
  "report_id": 1,
  "cloud_sync": false
}
```

### POST `/generate`

Compatibility endpoint for focused financial questions. Accepts either `question` or `product_info`.

## Local fallback

The full core workflow remains usable without a Gemini key:

- Budget generation
- Category analysis
- Saving suggestions
- Monthly summary
- LocalStorage history
- SQLite persistence

The UI labels this as Rule-Based / Demo mode.

## Financial disclaimer

This project is an educational financial planning tool. It does not provide guaranteed financial outcomes, professional financial advice, investment recommendations, or any bank decision.

## Hardware requirements

Processor:
- Intel Core i5 (8th Gen or above) / AMD Ryzen 5 or equivalent

RAM:
- Minimum 8 GB
- Recommended 16 GB

Storage:
- 256 GB SSD or 500 GB HDD minimum

Internet:
- Stable high-speed internet, minimum 10 Mbps; 20 Mbps recommended for cloud/API workflows

## Software requirements

- Windows 10/11, macOS Monterey or later, or Linux
- Python 3.8+
- Latest Chrome, Firefox, or Edge
- VS Code or preferred IDE
- Git
- AWS CLI where required by the broader lab workflow
- Ngrok for public tunnelling

## Future enhancements

- Predictive spending analytics
- Goal-based savings tracking
- Investment planning views
- Household/shared budgets
- Authentication
- Advanced monthly trend charts
- Multi-month financial health monitoring
