from schema_reader import get_schema_text


def build_sql_generation_prompt(user_question: str, schema_text: str) -> str:
    """
    Build a schema-aware prompt for generating SQLite SQL.
    """

    prompt = f"""
You are an expert Text-to-SQL assistant.

Your task is to convert the user's natural language question into a valid SQLite SELECT query.

DATABASE SCHEMA:
{schema_text}

USER QUESTION:
{user_question}

RULES:
1. Generate only SQLite SQL.
2. Use only the tables and columns shown in the schema.
3. Do not invent table names or column names.
4. Only generate read-only SELECT queries.
5. Do not generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, or DETACH.
6. Use JOINs when relationships are needed.
7. Use meaningful aliases when helpful.
8. Add LIMIT when the user asks for top results.
9. Return only the SQL query.
10. Do not include markdown, explanation, or code fences.

SQL:
"""
    return prompt.strip()


def build_sql_correction_prompt(
    user_question: str,
    schema_text: str,
    failed_sql: str,
    error_message: str
) -> str:
    """
    Build a prompt for correcting failed SQL using database error feedback.
    """

    prompt = f"""
You are an expert SQLite Text-to-SQL correction assistant.

The previous SQL query failed. Correct it using only the provided database schema.

DATABASE SCHEMA:
{schema_text}

ORIGINAL USER QUESTION:
{user_question}

FAILED SQL:
{failed_sql}

DATABASE ERROR:
{error_message}

RULES:
1. Return only the corrected SQLite SQL query.
2. Use only the tables and columns shown in the schema.
3. Do not invent table names or column names.
4. Only generate read-only SELECT queries.
5. Do not generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, or DETACH.
6. Do not include markdown, explanation, or code fences.

CORRECTED SQL:
"""
    return prompt.strip()


if __name__ == "__main__":
    schema = get_schema_text()

    question = "Show the top 5 customers by total invoice amount."

    prompt = build_sql_generation_prompt(question, schema)

    print(prompt)