# Quick Start — Personal Finance Advisor Bot

## 1. Install

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

## 2. Configure

Copy `.env.example` to `.env` and add:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

The application works in local/demo mode even when the API key is empty.

## 3. Run

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## 4. Test

Use:

- Income: `50000`
- Rent: `12000`
- Food: `6000`
- Transport: `3000`
- Dining: `2000`
- Entertainment: `1500`
- Utilities: `3000`
- Savings: `5000`
- Goal: `Emergency fund`

Then click **Analyse My Finances**.

## 5. Public testing

Set `NGROK_AUTHTOKEN` and run:

```bash
python run_public.py
```

Copy the public HTTPS URL.

## 6. API health

```text
http://127.0.0.1:5000/api/health
```
