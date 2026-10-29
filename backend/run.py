from app.database import initialize_database
import uvicorn

if __name__ == "__main__":
    print("Loading sales CSV into SQLite...")
    print(initialize_database())
    print("Starting API at http://127.0.0.1:8000")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
