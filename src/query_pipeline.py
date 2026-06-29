from schema_reader import get_schema_text
from sql_executor import execute_sql
from logger import log_query
from mock_sql_generator import generate_mock_sql
from answer_formatter import generate_simple_explanation


def run_querymind(
    question: str,
    max_corrections: int = 2,
    use_mock: bool = False,
    db_path=None,
    database_mode: str = "default",
    database_name: str = "chinook.db"
) -> dict:
    """
    Run QueryMind pipeline:
    question -> SQL generation -> validation -> execution -> correction if failed.

    use_mock=True runs an offline demo mode without calling Gemini API.
    """
    if database_mode != "default":
        use_mock = False

    schema_text = None

    if use_mock:
        generation_result = generate_mock_sql(question)
    else:
        from sql_generator import generate_sql

        schema_text = get_schema_text(db_path)
        generation_result = generate_sql(
            user_question=question,
            schema_text=schema_text
        )

    generated_sql = generation_result["sql"]

    execution_result = execute_sql(generated_sql, db_path=db_path)

    correction_attempts = 0
    corrected_sql_list = []

    while (
        not execution_result["success"]
        and correction_attempts < max_corrections
        and not use_mock
    ):
        correction_attempts += 1

        from self_corrector import correct_sql

        if schema_text is None:
            schema_text = get_schema_text(db_path)

        correction_result = correct_sql(
            user_question=question,
            failed_sql=execution_result["sql"] or generated_sql,
            error_message=execution_result["error"],
            schema_text=schema_text
        )

        corrected_sql = correction_result["corrected_sql"]
        corrected_sql_list.append(corrected_sql)

        execution_result = execute_sql(corrected_sql, db_path=db_path)

    data = execution_result["data"]
    row_count = len(data) if data is not None else None
    explanation = generate_simple_explanation(
        question=question,
        final_sql=execution_result["sql"] or generated_sql,
        success=execution_result["success"],
        row_count=row_count
    )

    final_result = {
        "question": question,
        "database_mode": database_mode,
        "database_name": database_name,
        "raw_model_output": generation_result["raw_output"],
        "model_used": generation_result.get("model_used", "unknown"),
        "generated_sql": generated_sql,
        "corrected_sql_list": corrected_sql_list,
        "final_sql": execution_result["sql"],
        "success": execution_result["success"],
        "data": data,
        "error": execution_result["error"],
        "execution_time": execution_result["execution_time"],
        "correction_attempts": correction_attempts,
        "explanation": explanation
    }

    log_query(final_result)

    return final_result


if __name__ == "__main__":
    test_questions = [
        "Show the top 5 customers by total invoice amount.",
        "Which genre generated the highest revenue?",
        "Show customers who have spent more than 40 dollars.",
        "Find the number of invoices by year.",
        "Which employees support the most customers?"
    ]

    for question in test_questions:
        print("\n====================================")
        print("Question:", question)

        result = run_querymind(question, use_mock=True)

        print("\nModel used:")
        print(result["model_used"])

        print("\nGenerated SQL:")
        print(result["generated_sql"])

        print("\nFinal SQL:")
        print(result["final_sql"])

        print("\nSuccess:", result["success"])
        print("Correction attempts:", result["correction_attempts"])
        print("Execution time:", result["execution_time"])

        if result["success"]:
            print("\nResult:")
            print(result["data"])
        else:
            print("\nFinal Error:")
            print(result["error"])
