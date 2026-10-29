from pathlib import Path
import os
import json
import re
import sqlite3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .database import initialize_database, get_connection
from .analytics import interpret_question, run_analytics

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
app = FastAPI(title="Sales Insight Assistant", version="1.0.0", description="Natural-language questions answered using safe, predefined database analytics.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173","http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)

def get_intent(question: str) -> tuple[dict, str]:
    """Try optional LLM classification; fall back to a transparent local interpreter."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            import httpx
            prompt = (
                "Classify the user's sales analytics question into exactly one intent. "
                "Allowed intents: total_revenue, top_product, top_region, monthly_trend, compare_months, product_breakdown, unknown. "
                "Return JSON only with keys intent and months (array of month names, if applicable). "
                "Never produce SQL. If unsure use unknown. User question: " + question
            )
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": os.getenv("OPENAI_MODEL","gpt-4o-mini"), "temperature": 0, "response_format": {"type":"json_object"}, "messages":[{"role":"system","content":"You classify intent only. Never output SQL."},{"role":"user","content":prompt}]},
                timeout=8.0
            )
            response.raise_for_status()
            data = response.json()
            parsed = json.loads(data["choices"][0]["message"]["content"])
            allowed = {"total_revenue","top_product","top_region","monthly_trend","compare_months","product_breakdown","unknown"}
            if parsed.get("intent") in allowed:
                if parsed["intent"] == "compare_months":
                    # Month values are accepted only if they are known month names.
                    valid_months = {"january","february","march","april","may","june","july","august","september","october","november","december"}
                    months = [m for m in parsed.get("months",[]) if isinstance(m,str) and m.lower() in valid_months][:2]
                    return {"intent":"compare_months","months":months}, "LLM"
                return {"intent": parsed["intent"]}, "LLM"
        except Exception:
            pass
    return interpret_question(question), "rule-based fallback"

@app.on_event("startup")
def startup():
    initialize_database()

@app.get("/api/health")
def health():
    return {"status":"ok"}

@app.get("/api/summary")
def summary():
    conn = get_connection()
    try:
        conn.row_factory = sqlite3.Row
        total = conn.execute("SELECT COUNT(*) AS n FROM sales").fetchone()["n"]
        completed = conn.execute("SELECT COUNT(*) AS n FROM sales WHERE status='Completed'").fetchone()["n"]
        invalid = conn.execute("SELECT COUNT(*) AS n FROM sales WHERE quantity IS NULL OR quantity <= 0 OR unit_price IS NULL OR unit_price <= 0").fetchone()["n"]
        return {"loaded_records":total,"completed_records":completed,"records_excluded_from_revenue":invalid}
    finally:
        conn.close()

@app.post("/api/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    intent, method = get_intent(question)
    conn = get_connection()
    try:
        result = run_analytics(conn, intent)
        result["interpretation_method"] = method
        result["question"] = question
        return result
    except (sqlite3.Error, ValueError) as exc:
        raise HTTPException(status_code=500, detail="Unable to complete the analysis. Check server logs.") from exc
    finally:
        conn.close()
