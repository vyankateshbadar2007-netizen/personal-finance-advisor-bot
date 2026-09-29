import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'finance_advisor.db'}")
GOOGLE_SHEETS_WEBHOOK_URL = os.getenv("GOOGLE_SHEETS_WEBHOOK_URL", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
# The SkillWallet brief names gemini-2.0-flash. That model is now shut down in Google's
# current catalog, so the default is a currently supported Flash model. Override via .env.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "2048"))

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_SORT_KEYS"] = False
CORS(app)

engine = create_engine(DATABASE_URL, future=True, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ExpenseEntry(Base):
    __tablename__ = "expense_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_date: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(40))
    amount: Mapped[float] = mapped_column(Float)
    frequency: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(String(160), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    income: Mapped[float] = mapped_column(Float)
    goal: Mapped[str] = mapped_column(String(80))
    total_expenses: Mapped[float] = mapped_column(Float)
    savings: Mapped[float] = mapped_column(Float)
    budget_json: Mapped[str] = mapped_column(Text)
    analysis_json: Mapped[str] = mapped_column(Text)
    suggestions_json: Mapped[str] = mapped_column(Text)
    summary_json: Mapped[str] = mapped_column(Text)
    ai_source: Mapped[str] = mapped_column(String(30), default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)

CATEGORY_TIPS = {
    "rent": {"max_pct": 30, "tip": "Keep rent at or below about 30% of monthly income."},
    "food": {"max_pct": 15, "tip": "Try to keep food spending under 15% of monthly income."},
    "transport": {"max_pct": 10, "tip": "Keep transport near 10% of monthly income where practical."},
    "dining": {"max_pct": 5, "tip": "Dining is a flexible category; use a clear monthly cap."},
    "entertainment": {"max_pct": 8, "tip": "Treat entertainment as a controlled discretionary expense."},
    "utilities": {"max_pct": 10, "tip": "Monitor utilities and investigate unusual increases."},
    "savings": {"min_pct": 20, "tip": "Target at least 20% toward savings when cash flow permits."},
}

GOAL_DESCRIPTIONS = {
    "emergency fund": "Build a cash buffer for unexpected expenses.",
    "vacation": "Create a predictable travel fund without disrupting essentials.",
    "gadget purchase": "Set a focused purchase target while protecting essentials.",
    "investment": "Build a steady monthly surplus for long-term investing.",
}


def clean_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if number >= 0 else default
    except (TypeError, ValueError):
        return default


def validate_payload(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors = []
    income = clean_float(data.get("income"))
    goal = str(data.get("goal", "")).strip().lower()
    expenses = data.get("expenses") or {}
    if income <= 0:
        errors.append("Monthly income must be greater than 0.")
    if goal not in GOAL_DESCRIPTIONS:
        errors.append("A valid financial goal is required.")

    normalized_expenses = {}
    for category in CATEGORY_TIPS:
        normalized_expenses[category] = clean_float(expenses.get(category, 0))

    logs = data.get("expense_logs") or []
    normalized_logs = []
    for row in logs:
        category = str(row.get("category", "")).strip().lower()
        amount = clean_float(row.get("amount", 0))
        frequency = str(row.get("frequency", "monthly")).strip().lower()
        if amount <= 0:
            continue
        if category not in CATEGORY_TIPS or category == "savings":
            errors.append(f"Unsupported expense category: {category or 'unknown'}.")
            continue
        if frequency not in {"daily", "weekly", "monthly"}:
            errors.append(f"Unsupported frequency for {category}.")
            continue
        normalized_logs.append({
            "date": str(row.get("date", date.today().isoformat()))[:20],
            "category": category,
            "amount": amount,
            "frequency": frequency,
            "note": str(row.get("note", ""))[:160],
        })

    has_expense = any(v > 0 for v in normalized_expenses.values()) or bool(normalized_logs)
    if not has_expense:
        errors.append("Income and at least one expense entry are required.")

    return {
        "income": income,
        "goal": goal,
        "expenses": normalized_expenses,
        "expense_logs": normalized_logs,
    }, errors


def normalize_expenses(payload: dict[str, Any]) -> dict[str, float]:
    totals = dict(payload["expenses"])
    for row in payload["expense_logs"]:
        multiplier = {"daily": 30.0, "weekly": 4.33, "monthly": 1.0}[row["frequency"]]
        totals[row["category"]] = totals.get(row["category"], 0.0) + row["amount"] * multiplier
    return totals


def budget_targets(income: float) -> list[dict[str, Any]]:
    items = []
    for category in ("rent", "food", "transport", "dining", "entertainment", "utilities"):
        pct = CATEGORY_TIPS[category]["max_pct"]
        items.append({
            "category": category,
            "recommended_amount": round(income * pct / 100),
            "recommended_percent": pct,
            "reason": CATEGORY_TIPS[category]["tip"],
        })
    items.append({
        "category": "savings",
        "recommended_amount": round(income * CATEGORY_TIPS["savings"]["min_pct"] / 100),
        "recommended_percent": CATEGORY_TIPS["savings"]["min_pct"],
        "reason": CATEGORY_TIPS["savings"]["tip"],
    })
    return items


def local_advice(payload: dict[str, Any]) -> dict[str, Any]:
    income = payload["income"]
    goal = payload["goal"]
    actual = normalize_expenses(payload)
    total_expenses = sum(actual.values())
    current_savings = actual.get("savings", 0.0)
    non_savings = max(0.0, total_expenses - current_savings)
    cash_surplus = max(0.0, income - non_savings)
    budget = budget_targets(income)

    analysis = []
    for item in budget:
        amount = actual.get(item["category"], 0.0)
        pct = round((amount / income * 100) if income else 0, 1)
        status = "on_track"
        if item["category"] == "savings":
            if amount < income * 0.10:
                status = "overspent"
            elif amount < item["recommended_amount"]:
                status = "watch"
        else:
            if pct > item["recommended_percent"]:
                status = "overspent"
            elif pct > item["recommended_percent"] * 0.85:
                status = "watch"
        messages = {
            "on_track": "Spending is currently within the suggested range.",
            "watch": "Spending is close to the suggested guideline.",
            "overspent": "Spending is above the suggested guideline and deserves attention.",
        }
        analysis.append({
            "category": item["category"],
            "actual_amount": round(amount),
            "percent_of_income": pct,
            "status": status,
            "message": messages[status],
        })

    suggestions: list[str] = []
    overspent = [x for x in analysis if x["status"] == "overspent" and x["category"] != "savings"]
    for item in overspent[:3]:
        cap = next(x["recommended_amount"] for x in budget if x["category"] == item["category"])
        reduction = max(0, item["actual_amount"] - cap)
        suggestions.append(
            f"Reduce {item['category']} by about ₹{reduction:,.0f} and redirect the freed amount toward your {goal}."
        )

    if len(suggestions) < 3:
        suggestions.extend([
            f"Protect a savings target of at least ₹{income * 0.20:,.0f} per month when your cash flow permits.",
            f"Review your largest flexible expense every week and set a simple spending ceiling for {goal}.",
            f"Use a separate bucket for your {goal} so planned money is less likely to be spent casually.",
        ])

    largest = max((x for x in analysis if x["category"] != "savings"), key=lambda x: x["actual_amount"], default={
        "category": "—", "actual_amount": 0
    })
    savings = max(0.0, income - non_savings)
    savings_rate = round((savings / income * 100) if income else 0, 1)
    narrative = (
        f"Your current cash flow leaves room for a {savings_rate}% savings rate. "
        f"The largest expense is {largest['category']}. Keep priority spending stable and direct the clearest reductions toward your {goal}."
        if savings_rate >= 20
        else
        f"Your current savings rate is {savings_rate}%, below the 20% guideline used by this planner. "
        f"Start with the categories marked as overspending and direct the recovered amount toward your {goal}."
    )

    summary = {
        "total_income": round(income),
        "total_expenses": round(total_expenses),
        "savings": round(savings),
        "savings_rate": savings_rate,
        "largest_expense_category": largest["category"],
        "largest_expense_amount": round(largest["actual_amount"]),
        "goal": goal,
        "narrative": narrative,
        "next_month_action": f"Start next month with a ₹{max(income * 0.20, savings):,.0f} target for your {goal}.",
    }

    return {
        "success": True,
        "source": "local",
        "budget": budget,
        "analysis": analysis,
        "suggestions": suggestions[:5],
        "summary": summary,
    }


def build_prompt(payload: dict[str, Any]) -> str:
    actual = normalize_expenses(payload)
    income = payload["income"]
    expense_lines = "\n".join(
        f"- {category}: ₹{actual.get(category, 0):,.0f}"
        for category in CATEGORY_TIPS
    )
    category_rules = "\n".join(
        f"- {category}: {info.get('max_pct', info.get('min_pct'))}% guideline. {info['tip']}"
        for category, info in CATEGORY_TIPS.items()
    )
    return f"""
You are a personal finance planning assistant for an educational budgeting application.
Use the user's actual numbers, but do not present any output as guaranteed financial advice.
Goal: {payload['goal']}
Goal description: {GOAL_DESCRIPTIONS[payload['goal']]}
Monthly income: ₹{income:,.0f}

Monthly/normalized expenses:
{expense_lines}

Budget guidelines:
{category_rules}

Create a structured monthly financial plan. Return ONLY valid JSON with this exact shape:
{{
  "budget": [
    {{
      "category": "rent|food|transport|dining|entertainment|utilities|savings",
      "recommended_amount": 0,
      "recommended_percent": 0,
      "reason": "short reason"
    }}
  ],
  "analysis": [
    {{
      "category": "rent|food|transport|dining|entertainment|utilities|savings",
      "actual_amount": 0,
      "percent_of_income": 0,
      "status": "on_track|watch|overspent",
      "message": "short explanation"
    }}
  ],
  "suggestions": ["3 to 5 actionable suggestions with rupee amounts where possible"],
  "summary": {{
    "total_income": 0,
    "total_expenses": 0,
    "savings": 0,
    "savings_rate": 0,
    "largest_expense_category": "category",
    "largest_expense_amount": 0,
    "goal": "{payload['goal']}",
    "narrative": "short monthly report",
    "next_month_action": "one clear next step"
  }}
}}
"""


def extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty AI response")

    candidates = [text]
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        candidates.insert(0, fence.group(1))

    object_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if object_match:
        candidates.append(object_match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    raise ValueError("Could not parse valid JSON from AI response")


class GeminiModel:
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.client = None
        if api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except Exception as exc:
                app.logger.warning("Gemini SDK unavailable: %s", exc)

    def generate_content(self, prompt: str) -> str:
        if not self.client:
            raise RuntimeError("Gemini API is not configured")
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "temperature": AI_TEMPERATURE,
                "max_output_tokens": AI_MAX_OUTPUT_TOKENS,
                "response_mime_type": "application/json",
            },
        )
        return response.text or ""


gemini_model = GeminiModel(GEMINI_API_KEY, GEMINI_MODEL)


def call_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    raw = gemini_model.generate_content(build_prompt(payload))
    result = extract_json(raw)

    required_keys = {"budget", "analysis", "suggestions", "summary"}
    if not required_keys.issubset(result):
        raise ValueError("AI response missing required keys")

    result["success"] = True
    result["source"] = "gemini"
    return result


def save_report(payload: dict[str, Any], result: dict[str, Any]) -> tuple[int, bool]:
    summary = result.get("summary", {})
    report = AnalysisReport(
        income=payload["income"],
        goal=payload["goal"],
        total_expenses=float(summary.get("total_expenses", 0)),
        savings=float(summary.get("savings", 0)),
        budget_json=json.dumps(result.get("budget", [])),
        analysis_json=json.dumps(result.get("analysis", [])),
        suggestions_json=json.dumps(result.get("suggestions", [])),
        summary_json=json.dumps(summary),
        ai_source=result.get("source", "local"),
    )
    with SessionLocal() as session:
        session.add(report)
        for row in payload["expense_logs"]:
            session.add(ExpenseEntry(
                entry_date=row["date"],
                category=row["category"],
                amount=row["amount"],
                frequency=row["frequency"],
                note=row["note"],
            ))
        session.commit()
        report_id = report.id

    cloud_sync = send_to_google_sheets(payload, result, report_id)
    return report_id, cloud_sync


def send_to_google_sheets(payload: dict[str, Any], result: dict[str, Any], report_id: int) -> bool:
    if not GOOGLE_SHEETS_WEBHOOK_URL:
        return False
    body = {
        "timestamp": datetime.utcnow().isoformat(),
        "report_id": report_id,
        "income": payload["income"],
        "goal": payload["goal"],
        "expenses": normalize_expenses(payload),
        "budget": result.get("budget", []),
        "analysis": result.get("analysis", []),
        "suggestions": result.get("suggestions", []),
        "summary": result.get("summary", {}),
        "ai_source": result.get("source", "local"),
    }
    try:
        response = requests.post(GOOGLE_SHEETS_WEBHOOK_URL, json=body, timeout=8)
        return response.ok
    except requests.RequestException as exc:
        app.logger.warning("Google Sheets sync failed: %s", exc)
        return False


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "app": "Personal Finance Advisor Bot",
        "gemini_configured": bool(GEMINI_API_KEY),
        "gemini_model": GEMINI_MODEL,
        "google_sheets_configured": bool(GOOGLE_SHEETS_WEBHOOK_URL),
        "database": "SQLite/SQLAlchemy",
    })


@app.post("/analyse")
def analyse():
    data = request.get_json(silent=True) or {}
    payload, errors = validate_payload(data)
    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    try:
        result = call_gemini(payload) if GEMINI_API_KEY else local_advice(payload)
    except Exception as exc:
        app.logger.warning("Gemini analysis failed; using local fallback: %s", exc)
        result = local_advice(payload)
        result["ai_error"] = "Gemini unavailable; rule-based analysis used."

    report_id, cloud_sync = save_report(payload, result)
    result["report_id"] = report_id
    result["cloud_sync"] = cloud_sync
    return jsonify(result)


@app.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}
    question = str(data.get("product_info") or data.get("question") or "").strip()
    tone = str(data.get("tone") or "clear").strip()
    platform = str(data.get("platform") or "Personal Finance Advisor Bot").strip()
    if not question:
        return jsonify({"success": False, "error": "Question is required."}), 400
    if len(question) > 2000:
        return jsonify({"success": False, "error": "Question is too long."}), 400

    prompt = f"""
You are the AI assistant inside {platform}.
Answer the user's financial planning question in a {tone} tone.
Question: {question}
Provide practical, educational guidance and avoid guarantees. Keep the answer focused and easy to scan.
"""
    try:
        if GEMINI_API_KEY:
            text = gemini_model.generate_content(prompt)
            source = "gemini"
        else:
            text = local_question_answer(question)
            source = "local"
    except Exception:
        text = local_question_answer(question)
        source = "local"
    return jsonify({"success": True, "content": text, "source": source})


@app.get("/api/history")
def api_history():
    with SessionLocal() as session:
        reports = session.scalars(select(AnalysisReport).order_by(AnalysisReport.created_at.desc()).limit(30)).all()
        return jsonify({
            "success": True,
            "history": [{
                "id": report.id,
                "created_at": report.created_at.isoformat(),
                "income": report.income,
                "goal": report.goal,
                "total_expenses": report.total_expenses,
                "savings": report.savings,
                "source": report.ai_source,
            } for report in reports]
        })


def local_question_answer(question: str) -> str:
    q = question.lower()
    if "credit" in q:
        return "Focus on timely repayments, keeping revolving credit use controlled, and reviewing your credit report for errors. Improvements usually take consistent habits rather than a single action."
    if "emi" in q or "debt" in q:
        return "Compare your current EMI burden with monthly income, avoid taking on avoidable new debt, and review whether your repayment plan still fits your cash flow."
    if "save" in q or "saving" in q:
        return "Start with a fixed monthly savings target, automate it where practical, and reduce one or two flexible expense categories rather than cutting essential spending first."
    if "budget" in q:
        return "Track the biggest fixed and flexible categories separately, set spending ceilings before the month starts, and review actuals weekly so small overruns do not compound."
    return "Use your income, essential expenses, flexible spending, and financial goal to build a realistic monthly plan. Focus on consistent tracking and small changes you can maintain."

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
