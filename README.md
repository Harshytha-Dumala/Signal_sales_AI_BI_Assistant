# SignalSales — Mini AI Business Intelligence Assistant

A small natural-language sales analytics app built for the Graduate Engineer Trainee assessment.

## Features
- Loads the supplied sales CSV into SQLite.
- React interface with suggested business questions.
- FastAPI backend accepts a question and returns a structured answer plus supporting figures.
- Supports total revenue, highest-revenue product, monthly trend, highest-revenue region, and month-to-month comparison.
- Safe query design: the LLM classifies intent only; it never writes SQL. Analytics use predefined, read-only SQL templates.
- Optional OpenAI-compatible intent classification. If no API key is configured or the model call fails, a transparent rule-based interpreter is used.
- Handles missing/invalid price, quantity and date values by excluding them from revenue analytics. Returned transactions are not counted as completed revenue.
- Five automated tests.

## Revenue definition
`net revenue = quantity × unit_price − discount_amount`

Only records with `status = Completed`, positive quantity, and a known positive unit price are included. The original row remains in the database for traceability, but invalid rows are excluded from revenue calculations. This is an explicit assessment assumption; explain it during review.

## Requirements
- Python 3.10+
- Node.js 18+ and npm

## Run on Windows

### 1. Backend
Open a terminal in the project folder:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

API starts at `http://127.0.0.1:8000`. API documentation: `http://127.0.0.1:8000/docs`.

### 2. Frontend
Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://127.0.0.1:5173`).

### Optional LLM classification
Copy `backend/.env.example` to `backend/.env` and set `OPENAI_API_KEY`. Keep the key private and never commit `.env`. Without a key, the app still works using the local rule-based interpreter. The LLM only returns an allowed intent and optional month names; backend SQL remains predefined.

### Run tests
From the `backend` folder with its virtual environment activated:

```powershell
pytest -q
```

## Architecture
1. React sends the question to `POST /api/ask`.
2. FastAPI optionally asks an LLM to classify the question into a small allowlist of intents. If unavailable, a rule-based interpreter is used.
3. The backend validates the returned intent and runs a predefined read-only SQL query against SQLite.
4. The API returns the answer, supporting figures, calculation definition and interpretation method.
5. React displays the answer and evidence.

## API
- `GET /api/health` — health check.
- `GET /api/summary` — row counts and data-quality summary.
- `POST /api/ask` — body: `{"question":"What is the total revenue?"}`.

## Sample questions
- What is the total revenue?
- Which product generated the highest revenue?
- What is the monthly revenue trend?
- Which region generated the highest sales?
- Compare revenue between January and February.

## Known limitations
- This is a small assessment project, not a production system.
- Question interpretation intentionally supports a small set of analytics.
- Month comparison assumes the provided dataset's year; it compares month numbers.
- No authentication or deployment pipeline is included.
- The UI shows a table for supporting figures; charting can be added later if time permits.

## AI usage and engineering decisions
- AI can map natural language to a fixed intent, but it cannot generate executable SQL.
- The backend owns calculations, validation, and database access.
- The fallback interpreter makes the project usable without an API key and makes behavior easy to explain.
- Tests cover revenue correctness, product ranking, monthly grouping, question interpretation, and safe handling of unknown questions.
