import sqlite3
import time

import pandas as pd

from schema_reader import DEFAULT_DB_PATH, resolve_db_path
from sql_validator import validate_sql


DB_PATH = DEFAULT_DB_PATH


def execute_sql(sql: str, db_path=None, validate: bool = True):
    """
    Validate and execute a SQL query on the Chinook SQLite database.

    Returns:
        dict with success status, dataframe, error message, final SQL, and execution time.
    """
    resolved_path = resolve_db_path(db_path)

    if not resolved_path.exists():
        raise FileNotFoundError(f"Database not found at: {resolved_path}")

    final_sql = sql

    if validate:
        validation = validate_sql(sql)

        if not validation["valid"]:
            return {
                "success": False,
                "data": None,
                "sql": None,
                "error": validation["error"],
                "execution_time": 0
            }

        final_sql = validation["sql"]

    start_time = time.time()

    try:
        conn = sqlite3.connect(resolved_path)

        try:
            df = pd.read_sql_query(final_sql, conn)
            execution_time = round(time.time() - start_time, 4)
        finally:
            conn.close()

        return {
            "success": True,
            "data": df,
            "sql": final_sql,
            "error": None,
            "execution_time": execution_time
        }

    except Exception as e:
        execution_time = round(time.time() - start_time, 4)

        return {
            "success": False,
            "data": None,
            "sql": final_sql,
            "error": str(e),
            "execution_time": execution_time
        }


if __name__ == "__main__":
    test_queries = [
        """
        SELECT BillingCountry, SUM(Total) AS total_revenue
        FROM Invoice
        GROUP BY BillingCountry
        ORDER BY total_revenue DESC;
        """,

        """
        SELECT customer_name, total_amount
        FROM invoices;
        """,

        """
        DROP TABLE Customer;
        """
    ]

    for test_sql in test_queries:
        print("\n==============================")
        print("Original SQL:")
        print(test_sql.strip())

        result = execute_sql(test_sql)

        print("Success:", result["success"])
        print("Final SQL:", result["sql"])
        print("Execution time:", result["execution_time"])

        if result["success"]:
            print(result["data"])
        else:
            print("Error:", result["error"])
