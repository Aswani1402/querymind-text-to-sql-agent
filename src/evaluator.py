from pathlib import Path
import time

import pandas as pd

from query_pipeline import run_querymind


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_PATH = PROJECT_ROOT / "data" / "evaluation_questions.csv"
RESULTS_PATH = PROJECT_ROOT / "outputs" / "evaluation_results.csv"


def load_evaluation_questions(path: Path = EVALUATION_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Evaluation file not found at: {path}")

    return pd.read_csv(path)


def _contains_expected_keywords(sql: str, expected_keywords: str) -> bool:
    if not expected_keywords:
        return True

    sql_text = (sql or "").lower()
    keywords = [
        keyword.strip().lower()
        for keyword in str(expected_keywords).split("|")
        if keyword.strip()
    ]

    return all(keyword in sql_text for keyword in keywords)


def run_evaluation(
    use_mock: bool = True,
    db_path=None,
    database_mode: str = "default",
    database_name: str = "chinook.db"
) -> tuple[dict, pd.DataFrame]:
    questions_df = load_evaluation_questions()
    results = []

    for _, row in questions_df.iterrows():
        question = row["question"]
        start_time = time.time()

        try:
            result = run_querymind(
                question,
                use_mock=use_mock,
                db_path=db_path,
                database_mode=database_mode,
                database_name=database_name
            )
            latency = result["execution_time"]
            success = result["success"]
            error = result["error"]
            final_sql = result["final_sql"]
            correction_attempts = result["correction_attempts"]
            model_used = result["model_used"]
        except Exception as error_obj:
            latency = round(time.time() - start_time, 4)
            success = False
            error = str(error_obj)
            final_sql = ""
            correction_attempts = 0
            model_used = "error"

        keyword_match = _contains_expected_keywords(
            final_sql,
            row.get("expected_keywords", "")
        )

        results.append({
            "question": question,
            "difficulty": row.get("difficulty", ""),
            "notes": row.get("notes", ""),
            "success": success,
            "keyword_match": keyword_match,
            "correction_attempts": correction_attempts,
            "execution_time": latency,
            "model_used": model_used,
            "final_sql": final_sql,
            "error": error
        })

    results_df = pd.DataFrame(results)
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(RESULTS_PATH, index=False)

    total_questions = len(results_df)
    success_count = int(results_df["success"].sum()) if total_questions else 0
    correction_success_count = int(
        ((results_df["success"]) & (results_df["correction_attempts"] > 0)).sum()
    ) if total_questions else 0

    metrics = {
        "total_questions": total_questions,
        "execution_success_rate": float(round(success_count / total_questions, 4))
        if total_questions else 0,
        "correction_success_count": correction_success_count,
        "average_latency": float(round(results_df["execution_time"].mean(), 4))
        if total_questions else 0,
        "failed_questions_count": int((~results_df["success"]).sum())
        if total_questions else 0,
        "results_path": str(RESULTS_PATH)
    }

    return metrics, results_df


if __name__ == "__main__":
    evaluation_metrics, evaluation_results = run_evaluation(use_mock=True)
    print(evaluation_metrics)
    print(evaluation_results)
