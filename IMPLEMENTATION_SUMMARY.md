# Implementation Summary — Personal Finance Advisor Bot

## Core functionality

### Budget Generator
`local_advice()` and `build_prompt()` produce a category-based monthly plan from income and spending.

### Spending Analyser
Each category is compared with the project guideline thresholds in `CATEGORY_TIPS` and classified as:
- `on_track`
- `watch`
- `overspent`

### Saving Suggestions
The system returns 3–5 actionable recommendations with rupee amounts where practical.

### Monthly Report
The summary includes:
- Income
- Total expenses
- Savings
- Savings rate
- Largest expense
- Goal
- Next-month action

## Flask

Routes:
- `/`
- `/analyse`
- `/generate`
- `/api/health`
- `/api/history`

## Persistence

SQLAlchemy models:
- `ExpenseEntry`
- `AnalysisReport`

Database:
- SQLite by default

Browser:
- LocalStorage history for quick client-side review

## AI

Primary AI:
- Gemini

Fallback:
- Deterministic local financial planning engine

The backend validates input and creates a structured prompt. `extract_json()` handles direct JSON, fenced JSON, and raw JSON object extraction.

## Frontend

- Responsive single-page interface
- Async Fetch API
- Dynamic budget cards
- Spending analysis chips
- Saving suggestions
- Monthly report
- Mobile navigation
- Loading states
- Toast notifications
- Local history management
