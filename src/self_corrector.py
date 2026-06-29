from schema_reader import get_schema_text
from prompt_builder import build_sql_correction_prompt
from sql_cleaner import clean_sql_output
from sql_generator import call_gemini_with_retry


def correct_sql(
    user_question: str,
    failed_sql: str,
    error_message: str,
    schema_text: str | None = None
) -> dict:
    """
    Correct a failed SQL query using Gemini and database error feedback.

    This uses retry + fallback handling from sql_generator.py,
    so temporary Gemini 503/high-demand errors will not immediately crash the app.
    """

    if schema_text is None:
        schema_text = get_schema_text()

    prompt = build_sql_correction_prompt(
        user_question=user_question,
        schema_text=schema_text,
        failed_sql=failed_sql,
        error_message=error_message
    )

    raw_output, model_used = call_gemini_with_retry(prompt)

    corrected_sql = clean_sql_output(raw_output)

    return {
        "raw_output": raw_output,
        "corrected_sql": corrected_sql,
        "model_used": model_used
    }


if __name__ == "__main__":
    question = "Show the top 5 customers by total invoice amount."

    failed_sql = """
    SELECT customer_name, SUM(total_amount) AS total_spent
    FROM invoices
    GROUP BY customer_name
    ORDER BY total_spent DESC
    LIMIT 5;
    """

    error_message = "no such table: invoices"

    result = correct_sql(
        user_question=question,
        failed_sql=failed_sql,
        error_message=error_message
    )

    print("Model used:")
    print(result["model_used"])

    print("\nCorrected SQL:")
    print(result["corrected_sql"])