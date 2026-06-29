import re


def clean_sql_output(raw_output: str) -> str:
    """
    Clean LLM-generated SQL output.

    Removes:
    - markdown code fences
    - ```sql
    - ```
    - extra text before/after SQL
    """

    if not raw_output:
        return ""

    sql = raw_output.strip()

    # Remove markdown code fences
    sql = sql.replace("```sql", "")
    sql = sql.replace("```SQL", "")
    sql = sql.replace("```", "")

    # Remove common prefixes
    prefixes = [
        "SQL:",
        "Query:",
        "SQLite SQL:",
        "Corrected SQL:",
        "Here is the SQL:",
        "Here is the corrected SQL:"
    ]

    for prefix in prefixes:
        if sql.strip().lower().startswith(prefix.lower()):
            sql = sql.strip()[len(prefix):].strip()

    # Try to keep only from SELECT or WITH onward
    match = re.search(r"\b(SELECT|WITH)\b", sql, re.IGNORECASE)
    if match:
        sql = sql[match.start():]

    # Remove explanation after semicolon if present
    if ";" in sql:
        sql = sql.split(";")[0] + ";"

    return sql.strip()


if __name__ == "__main__":
    test_outputs = [
        "```sql\nSELECT * FROM Customer;\n```",
        "SQL: SELECT * FROM Invoice;",
        "Here is the SQL:\nSELECT FirstName, LastName FROM Customer;",
        "SELECT * FROM Track;\nThis query returns all tracks.",
        "```SQL\nSELECT BillingCountry, SUM(Total) FROM Invoice GROUP BY BillingCountry;\n```"
    ]

    for output in test_outputs:
        print("\nRaw:")
        print(output)
        print("Cleaned:")
        print(clean_sql_output(output))