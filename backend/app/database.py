from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "sales.db"
CSV_PATH = ROOT.parent / "data" / "sales_data.csv"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_database(csv_path=None):
    csv_path = Path(csv_path) if csv_path else CSV_PATH
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]
    required = ["transaction_id","order_date","product","category","region","sales_channel","quantity","unit_price","discount_amount","status"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

    df = df[required].copy()
    df["order_date"] = pd.to_datetime(df["order_date"], format="%d-%m-%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    for col in ["quantity", "unit_price", "discount_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["transaction_id","product","category","region","sales_channel","status"]:
        df[col] = df[col].astype("string").str.strip()
    # Keep imperfect rows for traceability; analytics exclude rows with invalid date, quantity or price.
    df["discount_amount"] = df["discount_amount"].fillna(0)
    conn = get_connection()
    try:
        conn.execute("DROP TABLE IF EXISTS sales")
        conn.execute("""
            CREATE TABLE sales (
                transaction_id TEXT PRIMARY KEY,
                order_date TEXT,
                product TEXT,
                category TEXT,
                region TEXT,
                sales_channel TEXT,
                quantity REAL,
                unit_price REAL,
                discount_amount REAL NOT NULL DEFAULT 0,
                status TEXT
            )
        """)
        for _, r in df.iterrows():
            conn.execute("""INSERT OR REPLACE INTO sales VALUES (?,?,?,?,?,?,?,?,?,?)""", tuple(
                None if pd.isna(r[c]) else (float(r[c]) if c in ["quantity","unit_price","discount_amount"] else r[c])
                for c in required
            ))
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        invalid = conn.execute("""SELECT COUNT(*) FROM sales WHERE order_date IS NULL OR quantity IS NULL OR quantity <= 0 OR unit_price IS NULL OR unit_price <= 0""").fetchone()[0]
        returned = conn.execute("SELECT COUNT(*) FROM sales WHERE lower(status) = 'returned'").fetchone()[0]
        return {"loaded_records": total, "records_with_invalid_analytics_fields": invalid, "returned_records": returned}
    finally:
        conn.close()
