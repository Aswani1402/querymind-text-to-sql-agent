import csv
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT_DIR / "outputs" / "query_logs.csv"


FIELDNAMES = [
    "timestamp",
    "database_mode",
    "database_name",
    "question",
    "generated_sql",
    "final_sql",
    "success",
    "error",
    "correction_attempts",
    "execution_time",
    "model_used",
    "explanation"
]


def ensure_log_file():
    """
    Create query_logs.csv with headers if it does not exist.
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0:
        with open(LOG_PATH, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
        return

    with open(LOG_PATH, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        existing_fieldnames = reader.fieldnames or []
        rows = list(reader)

    if existing_fieldnames != FIELDNAMES:
        with open(LOG_PATH, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in FIELDNAMES})


def log_query(result: dict):
    """
    Save one QueryMind run result to query_logs.csv.
    """
    ensure_log_file()

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "database_mode": result.get("database_mode"),
        "database_name": result.get("database_name"),
        "question": result.get("question"),
        "generated_sql": result.get("generated_sql"),
        "final_sql": result.get("final_sql"),
        "success": result.get("success"),
        "error": result.get("error"),
        "correction_attempts": result.get("correction_attempts"),
        "execution_time": result.get("execution_time"),
        "model_used": result.get("model_used"),
        "explanation": result.get("explanation")
    }

    with open(LOG_PATH, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writerow(row)


if __name__ == "__main__":
    sample_result = {
        "question": "Show top 5 customers by revenue.",
        "database_mode": "default",
        "database_name": "chinook.db",
        "generated_sql": "SELECT * FROM Customer;",
        "final_sql": "SELECT * FROM Customer LIMIT 100;",
        "success": True,
        "error": None,
        "correction_attempts": 0,
        "execution_time": 0.01,
        "model_used": "offline_mock",
        "explanation": "Sample explanation."
    }

    log_query(sample_result)
    print(f"Log saved to: {LOG_PATH}")
