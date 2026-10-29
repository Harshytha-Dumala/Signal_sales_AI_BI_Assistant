import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.analytics import interpret_question, run_analytics
import sqlite3

def make_db():
    c = sqlite3.connect(":memory:")
    c.execute("""CREATE TABLE sales(transaction_id TEXT, order_date TEXT, product TEXT, category TEXT, region TEXT, sales_channel TEXT, quantity REAL, unit_price REAL, discount_amount REAL, status TEXT)""")
    c.executemany("INSERT INTO sales VALUES (?,?,?,?,?,?,?,?,?,?)", [
        ("1","2026-01-03","Mouse","Accessories","North","Online",2,100,0,"Completed"),
        ("2","2026-02-03","Keyboard","Accessories","South","Retail",1,300,0,"Completed"),
        ("3","2026-02-04","Mouse","Accessories","North","Retail",1,100,10,"Completed"),
        ("4","2026-02-05","Monitor","Electronics","West","Retail",1,500,0,"Returned"),
        ("5","2026-02-06","Broken","Other","West","Retail",0,None,0,"Completed"),
    ])
    return c

def test_total_revenue_excludes_returned_and_invalid():
    result = run_analytics(make_db(), {"intent":"total_revenue"})
    assert result["value"] == 590.0

def test_top_product():
    result = run_analytics(make_db(), {"intent":"top_product"})
    assert result["supporting_data"][0]["product"] == "Keyboard"

def test_monthly_trend():
    result = run_analytics(make_db(), {"intent":"monthly_trend"})
    assert len(result["supporting_data"]) == 2

def test_question_interpretation():
    assert interpret_question("What is the total revenue?")["intent"] == "total_revenue"

def test_unknown_question_is_safe():
    result = run_analytics(make_db(), interpret_question("Tell me a joke"))
    assert result["intent"] == "unknown"
