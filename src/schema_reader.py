import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "chinook.db"
DB_PATH = DEFAULT_DB_PATH


def resolve_db_path(db_path=None) -> Path:
    """
    Resolve a SQLite database path.

    If db_path is None, use the default Chinook database.
    """
    if db_path is None:
        return DEFAULT_DB_PATH

    return Path(db_path)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def get_connection(db_path=None):
    """
    Create a SQLite database connection.
    """
    resolved_path = resolve_db_path(db_path)

    if not resolved_path.exists():
        raise FileNotFoundError(
            f"Database not found at {_display_path(resolved_path)}. "
            "Use the default data/chinook.db file or upload a valid SQLite database."
        )

    try:
        conn = sqlite3.connect(resolved_path)
        conn.execute("SELECT name FROM sqlite_master LIMIT 1")
        return conn
    except sqlite3.DatabaseError as error:
        raise ValueError(
            f"Invalid SQLite database file: {_display_path(resolved_path)}. "
            "Please upload a valid .db, .sqlite, or .sqlite3 file."
        ) from error


def get_table_names(conn):
    """
    Return all user-created table names from the SQLite database.
    """
    query = """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name;
    """

    cursor = conn.cursor()
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]


def get_columns(conn, table_name):
    """
    Return column details for a table.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({_quote_identifier(table_name)})")
    columns = cursor.fetchall()

    column_info = []
    for col in columns:
        column_info.append({
            "cid": col[0],
            "name": col[1],
            "type": col[2] or "UNKNOWN",
            "not_null": bool(col[3]),
            "default_value": col[4],
            "primary_key": bool(col[5])
        })

    return column_info


def get_foreign_keys(conn, table_name):
    """
    Return foreign key details for a table.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({_quote_identifier(table_name)})")
    foreign_keys = cursor.fetchall()

    fk_info = []
    for fk in foreign_keys:
        fk_info.append({
            "from_column": fk[3],
            "to_table": fk[2],
            "to_column": fk[4]
        })

    return fk_info


def get_schema_text(db_path=None):
    """
    Convert database schema into prompt-friendly text.
    """
    conn = get_connection(db_path)

    try:
        tables = get_table_names(conn)
        schema_lines = []

        for table in tables:
            schema_lines.append(f"Table: {table}")

            columns = get_columns(conn, table)
            column_text = []

            for col in columns:
                pk = " PRIMARY KEY" if col["primary_key"] else ""
                not_null = " NOT NULL" if col["not_null"] else ""
                column_text.append(f"{col['name']} {col['type']}{pk}{not_null}")

            schema_lines.append("Columns: " + ", ".join(column_text))

            foreign_keys = get_foreign_keys(conn, table)
            if foreign_keys:
                for fk in foreign_keys:
                    schema_lines.append(
                        f"Foreign key: {table}.{fk['from_column']} -> "
                        f"{fk['to_table']}.{fk['to_column']}"
                    )
            else:
                schema_lines.append("Foreign keys: None")

            schema_lines.append("")

        return "\n".join(schema_lines)
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        schema = get_schema_text()
        print(schema)
    except (FileNotFoundError, ValueError) as error:
        print(error)
        raise SystemExit(1) from error
