from schema_reader import get_schema_text
from sql_executor import execute_sql
from self_corrector import correct_sql


def test_forced_self_correction():
    """
    Force a bad SQL query, execute it, correct it, and execute again.
    This proves the self-correction loop works.
    """

    schema_text = get_schema_text()

    question = "Show the top 5 customers by total invoice amount."

    bad_sql = """
    SELECT customer_name, SUM(total_amount) AS total_spent
    FROM invoices
    GROUP BY customer_name
    ORDER BY total_spent DESC
    LIMIT 5;
    """

    print("Original Question:")
    print(question)

    print("\nBad SQL:")
    print(bad_sql)

    first_result = execute_sql(bad_sql)

    print("\nFirst Execution Success:", first_result["success"])
    print("First Error:", first_result["error"])

    if not first_result["success"]:
        correction = correct_sql(
            user_question=question,
            failed_sql=first_result["sql"] or bad_sql,
            error_message=first_result["error"],
            schema_text=schema_text
        )

        corrected_sql = correction["corrected_sql"]

        print("\nCorrected SQL:")
        print(corrected_sql)

        second_result = execute_sql(corrected_sql)

        print("\nSecond Execution Success:", second_result["success"])
        print("Final SQL:", second_result["sql"])
        print("Execution Time:", second_result["execution_time"])

        if second_result["success"]:
            print("\nFinal Result:")
            print(second_result["data"])
        else:
            print("\nFinal Error:")
            print(second_result["error"])


if __name__ == "__main__":
    test_forced_self_correction()