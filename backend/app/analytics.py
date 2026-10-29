"""Safe, predefined analytics. User text is never executed as SQL."""
from datetime import datetime
from typing import Optional
import sqlite3
import re

def _rows(conn, sql, params=()):
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(sql, params).fetchall()]

def interpret_question(question: str) -> dict:
    """Small transparent intent interpreter used when no LLM key is configured."""
    q = question.lower().strip()
    if not q:
        return {"intent": "unknown", "reason": "Please enter a question."}

    # Keep month comparison ahead of generic monthly trend detection.
    if any(x in q for x in ["change between", "compare", "compared with", "difference between"]) and "month" in q:
        months = re.findall(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", q)
        if len(months) >= 2:
            return {"intent": "compare_months", "months": months[:2]}
        return {"intent": "compare_months", "months": []}
    if any(x in q for x in ["monthly trend", "month by month", "revenue trend", "monthly revenue"]):
        return {"intent": "monthly_trend"}
    if any(x in q for x in ["highest revenue product", "product generated the highest", "top product", "best selling product", "which product", "highest revenue"]):
        return {"intent": "top_product"}
    if any(x in q for x in ["which region", "highest sales region", "top region", "region generated", "sales by region"]):
        return {"intent": "top_region"}
    if any(x in q for x in ["total revenue", "revenue total", "overall revenue", "how much revenue", "total sales"]):
        return {"intent": "total_revenue"}
    if any(x in q for x in ["show products", "list products", "what products"]):
        return {"intent": "product_breakdown"}
    return {"intent": "unknown", "reason": "I couldn't map that question to a supported sales analysis."}

def run_analytics(conn: sqlite3.Connection, intent: dict) -> dict:
    kind = intent.get("intent")
    # Revenue uses completed transactions with positive quantity and a known, positive unit price.
    base = "FROM sales WHERE status = 'Completed' AND quantity > 0 AND unit_price IS NOT NULL AND unit_price > 0"
    if kind == "total_revenue":
        row = _rows(conn, f"SELECT ROUND(COALESCE(SUM(quantity * unit_price - discount_amount),0),2) AS revenue, COUNT(*) AS transactions {base}")[0]
        return {"intent": kind, "answer": f"Total revenue is {row['revenue']:,.2f}.", "value": row["revenue"], "supporting_data": row, "definition": "Completed transactions only; revenue = quantity × unit price − discount."}
    if kind == "top_product":
        rows = _rows(conn, f"SELECT product, ROUND(SUM(quantity * unit_price - discount_amount),2) AS revenue, SUM(quantity) AS units_sold {base} GROUP BY product ORDER BY revenue DESC, product ASC LIMIT 5")
        if not rows: return {"intent": kind, "answer": "No valid completed sales were found.", "supporting_data": []}
        r = rows[0]
        return {"intent": kind, "answer": f"{r['product']} generated the highest revenue: {r['revenue']:,.2f}.", "value": r["revenue"], "supporting_data": rows, "definition": "Ranked by revenue from valid completed transactions."}
    if kind == "top_region":
        rows = _rows(conn, f"SELECT region, ROUND(SUM(quantity * unit_price - discount_amount),2) AS revenue, COUNT(*) AS transactions {base} GROUP BY region ORDER BY revenue DESC, region ASC")
        if not rows: return {"intent": kind, "answer": "No valid completed sales were found.", "supporting_data": []}
        r = rows[0]
        return {"intent": kind, "answer": f"{r['region']} generated the highest sales revenue: {r['revenue']:,.2f}.", "value": r["revenue"], "supporting_data": rows, "definition": "Regions are ranked by net revenue from valid completed transactions."}
    if kind == "monthly_trend":
        rows = _rows(conn, f"SELECT strftime('%Y-%m', order_date) AS month, ROUND(SUM(quantity * unit_price - discount_amount),2) AS revenue {base} GROUP BY month ORDER BY month")
        return {"intent": kind, "answer": f"Monthly revenue trend contains {len(rows)} month(s).", "supporting_data": rows, "definition": "Grouped by order month; completed valid transactions only."}
    if kind == "compare_months":
        months = intent.get("months", [])
        if len(months) < 2:
            return {"intent": kind, "answer": "Please name two months, for example: Compare revenue between January and February.", "supporting_data": []}
        month_map = {m.lower(): f"{i:02d}" for i,m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"],1)}
        m1, m2 = months[0].lower(), months[1].lower()
        if m1 not in month_map or m2 not in month_map:
            return {"intent": kind, "answer": "I couldn't recognize both months.", "supporting_data": []}
        vals = []
        for m in [m1,m2]:
            row = _rows(conn, f"SELECT ROUND(COALESCE(SUM(quantity * unit_price - discount_amount),0),2) AS revenue {base} AND strftime('%m', order_date) = ?", (month_map[m],))[0]
            vals.append({"month": m.title(), "revenue": row["revenue"]})
        diff = round(vals[1]["revenue"] - vals[0]["revenue"], 2)
        direction = "increased" if diff > 0 else "decreased" if diff < 0 else "did not change"
        return {"intent": kind, "answer": f"Revenue {direction} by {abs(diff):,.2f} from {vals[0]['month']} to {vals[1]['month']}.", "value": diff, "supporting_data": vals, "definition": "Difference = second named month revenue − first named month revenue."}
    if kind == "product_breakdown":
        rows = _rows(conn, f"SELECT product, ROUND(SUM(quantity * unit_price - discount_amount),2) AS revenue {base} GROUP BY product ORDER BY revenue DESC")
        return {"intent": kind, "answer": f"Found {len(rows)} products with valid completed sales.", "supporting_data": rows}
    return {"intent": "unknown", "answer": intent.get("reason", "I couldn't understand that question."), "supporting_data": [], "suggestions": ["What is the total revenue?", "Which product generated the highest revenue?", "What is the monthly revenue trend?", "Which region generated the highest sales?", "Compare revenue between January and February."]}
