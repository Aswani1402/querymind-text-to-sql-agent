import re

try:
    import sqlglot
    from sqlglot import exp
except ImportError:
    sqlglot = None
    exp = None


BLOCKED_KEYWORDS = [
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "PRAGMA",
    "ATTACH",
    "DETACH",
    "REPLACE",
    "VACUUM"
]


def clean_sql_for_validation(sql: str) -> str:
    """
    Normalize SQL text for safety validation.
    """
    if not sql:
        return ""

    sql = sql.strip()
    sql = sql.replace("\n", " ")
    sql = re.sub(r"\s+", " ", sql)

    return sql


def is_select_query(sql: str) -> bool:
    """
    Allow only SELECT queries or WITH ... SELECT queries.
    """
    cleaned = clean_sql_for_validation(sql).upper()

    if cleaned.startswith("SELECT "):
        return True

    if cleaned.startswith("WITH ") and " SELECT " in cleaned:
        return True

    return False


def has_blocked_keywords(sql: str) -> bool:
    """
    Check for destructive or unsafe SQL keywords.
    """
    cleaned = clean_sql_for_validation(sql).upper()

    for keyword in BLOCKED_KEYWORDS:
        pattern = r"\b" + keyword + r"\b"
        if re.search(pattern, cleaned):
            return True

    return False


def has_multiple_statements(sql: str) -> bool:
    """
    Block multiple SQL statements.
    Example:
    SELECT * FROM Customer; DROP TABLE Customer;
    """
    cleaned = sql.strip()

    if cleaned.endswith(";"):
        cleaned = cleaned[:-1]

    return ";" in cleaned


def parse_with_sqlglot(sql: str):
    """
    Parse SQL with SQLGlot when available.
    """
    if sqlglot is None:
        return {
            "available": False,
            "valid": True,
            "error": None,
            "expression": None
        }

    try:
        expressions = sqlglot.parse(sql, read="sqlite")
    except Exception as error:
        return {
            "available": True,
            "valid": False,
            "error": f"SQL parsing failed: {error}",
            "expression": None
        }

    expressions = [expression for expression in expressions if expression is not None]

    if len(expressions) != 1:
        return {
            "available": True,
            "valid": False,
            "error": "Multiple SQL statements are not allowed.",
            "expression": None
        }

    expression = expressions[0]

    if not isinstance(expression, exp.Select):
        return {
            "available": True,
            "valid": False,
            "error": "Only SELECT queries are allowed."
        }

    return {
        "available": True,
        "valid": True,
        "error": None,
        "expression": expression
    }


def add_limit_if_missing(sql: str, limit: int = 100) -> str:
    """
    Add LIMIT to SELECT queries if no LIMIT exists.
    """
    cleaned = sql.strip().rstrip(";")

    if re.search(r"\bLIMIT\b", cleaned, re.IGNORECASE):
        return cleaned + ";"

    return f"{cleaned} LIMIT {limit};"


def validate_sql(sql: str, add_limit: bool = True, limit: int = 100):
    """
    Validate SQL query before execution.

    Returns:
        dict:
        {
            "valid": bool,
            "sql": final_sql_or_none,
            "error": error_message_or_none
        }
    """
    if not sql or not sql.strip():
        return {
            "valid": False,
            "sql": None,
            "error": "SQL query is empty."
        }

    if has_multiple_statements(sql):
        return {
            "valid": False,
            "sql": None,
            "error": "Multiple SQL statements are not allowed."
        }

    if has_blocked_keywords(sql):
        return {
            "valid": False,
            "sql": None,
            "error": "Unsafe SQL keyword detected. Only read-only SELECT queries are allowed."
        }

    if not is_select_query(sql):
        return {
            "valid": False,
            "sql": None,
            "error": "Only SELECT queries are allowed."
        }

    parsed = parse_with_sqlglot(sql)
    if parsed["available"] and not parsed["valid"]:
        return {
            "valid": False,
            "sql": None,
            "error": parsed["error"]
        }

    final_sql = add_limit_if_missing(sql, limit) if add_limit else sql.strip()

    return {
        "valid": True,
        "sql": final_sql,
        "error": None
    }


if __name__ == "__main__":
    test_queries = [
        "SELECT * FROM Customer;",
        "SELECT * FROM Invoice",
        "DROP TABLE Customer;",
        "DELETE FROM Customer WHERE CustomerId = 1;",
        "SELECT * FROM Customer; DROP TABLE Customer;",
        "WITH top_customers AS (SELECT * FROM Customer) SELECT * FROM top_customers;"
    ]

    for query in test_queries:
        result = validate_sql(query)
        print("\nSQL:", query)
        print("Valid:", result["valid"])
        print("Final SQL:", result["sql"])
        print("Error:", result["error"])
