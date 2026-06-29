import sys
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
UPLOAD_DIR = ROOT_DIR / "outputs" / "uploaded_databases"

if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from evaluator import RESULTS_PATH, run_evaluation
from logger import LOG_PATH
from query_pipeline import run_querymind
from schema_reader import DEFAULT_DB_PATH, get_schema_text
from visualizer import suggest_chart


def friendly_error_message(error: Exception) -> str:
    message = str(error)
    lowered = message.lower()

    api_unavailable_terms = [
        "429",
        "503",
        "resource_exhausted",
        "quota",
        "rate limit",
        "rate-limit",
        "unavailable"
    ]

    if any(term in lowered or term in message for term in api_unavailable_terms):
        return (
            "Gemini API is currently unavailable or quota is exhausted. "
            "Use Offline demo mode with Chinook, "
            "wait for quota reset, or use another API key."
        )

    if "api" in lowered or "gemini" in lowered:
        return f"Gemini API is unavailable: {message}"

    return f"Something went wrong: {message}"


def show_friendly_error(error: Exception) -> None:
    st.error(friendly_error_message(error))
    with st.expander("Technical error details"):
        st.code(str(error))


def save_uploaded_database(uploaded_file) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(uploaded_file.name).name
    destination = UPLOAD_DIR / safe_name

    with open(destination, "wb") as file:
        file.write(uploaded_file.getbuffer())

    st.session_state["uploaded_db_path"] = str(destination)
    st.session_state["uploaded_db_name"] = safe_name
    return destination


def get_selected_database():
    database_choice = st.sidebar.radio(
        "Database mode",
        [
            "Use default Chinook database",
            "Upload SQLite database"
        ]
    )

    if database_choice == "Use default Chinook database":
        st.sidebar.caption("Using data/chinook.db")
        return "default", DEFAULT_DB_PATH, "chinook.db"

    uploaded_file = st.sidebar.file_uploader(
        "Upload SQLite database",
        type=["db", "sqlite", "sqlite3"]
    )

    if uploaded_file is not None:
        selected_path = save_uploaded_database(uploaded_file)
        st.sidebar.success(f"Uploaded: {selected_path.name}")
        return "uploaded", selected_path, selected_path.name

    stored_path = st.session_state.get("uploaded_db_path")
    stored_name = st.session_state.get("uploaded_db_name")
    if stored_path and Path(stored_path).exists():
        st.sidebar.info(f"Using uploaded file: {stored_name}")
        return "uploaded", Path(stored_path), stored_name

    st.sidebar.warning("Upload a .db, .sqlite, or .sqlite3 file to use this mode.")
    return "uploaded", None, "No uploaded database selected"


st.set_page_config(
    page_title="QueryMind",
    page_icon="QM",
    layout="wide"
)


st.title("QueryMind")
st.subheader("Self-Correcting Text-to-SQL AI Data Analyst")

st.write(
    "Ask business questions in natural language. QueryMind generates SQL, "
    "validates it, executes it on the selected SQLite database, and returns results."
)


page = st.sidebar.radio(
    "Navigation",
    [
        "Ask Question",
        "Database Schema",
        "Query Logs",
        "Evaluation",
        "About / Limitations"
    ]
)

database_mode, selected_db_path, database_name = get_selected_database()


if page == "Ask Question":
    st.header("Ask a Database Question")

    st.caption(f"Database mode: {database_mode}")
    st.caption(f"Database: {database_name}")

    sample_questions = [
        "Show the top 5 customers by total invoice amount.",
        "Which genre generated the highest revenue?",
        "Show customers who have spent more than 40 dollars.",
        "Find the number of invoices by year.",
        "Which employees support the most customers?",
        "Show total sales by billing country.",
        "What are the top 10 most expensive tracks?",
        "Which countries have the highest number of customers?",
        "Which artist has the most tracks?"
    ]

    selected_sample = ""
    if database_mode == "default":
        selected_sample = st.selectbox(
            "Try a sample Chinook question",
            [""] + sample_questions
        )

    user_question = st.text_area(
        "Enter your question",
        value=selected_sample,
        height=100,
        placeholder="Example: Show the top 5 customers by total invoice amount."
    )

    if database_mode == "default":
        generation_mode = st.radio(
            "SQL generation mode",
            ["Offline demo mode", "Gemini API mode"],
            index=0,
            help=(
                "Offline mode uses predefined Chinook SQL. "
                "Gemini API mode generates SQL dynamically."
            )
        )
    else:
        generation_mode = "Gemini API mode"
        st.warning(
            "Uploaded databases require Gemini API mode because offline demo SQL "
            "only supports Chinook."
        )

    use_mock = generation_mode == "Offline demo mode"

    run_button = st.button("Generate SQL and Run Query")

    if run_button:
        if not user_question.strip():
            st.warning("Please enter a question.")
        elif database_mode == "uploaded" and selected_db_path is None:
            st.error("Please upload a valid SQLite database before running a query.")
        else:
            with st.spinner("Generating SQL, validating, and executing..."):
                try:
                    result = run_querymind(
                        user_question,
                        use_mock=use_mock,
                        db_path=selected_db_path,
                        database_mode=database_mode,
                        database_name=database_name
                    )

                    st.subheader("Question")
                    st.write(result["question"])

                    st.subheader("Generated SQL")
                    st.code(result["generated_sql"], language="sql")

                    if result["corrected_sql_list"]:
                        st.subheader("Correction Attempts")
                        for i, corrected_sql in enumerate(
                            result["corrected_sql_list"], start=1
                        ):
                            st.write(f"Attempt {i}")
                            st.code(corrected_sql, language="sql")

                    st.subheader("Final SQL")
                    st.code(result["final_sql"], language="sql")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Success", str(result["success"]))
                    col2.metric("Correction Attempts", result["correction_attempts"])
                    col3.metric("Execution Time", result["execution_time"])

                    st.info(f"Model used: {result.get('model_used', 'unknown')}")

                    if result["success"]:
                        st.subheader("Result Table")
                        st.dataframe(result["data"], use_container_width=True)

                        st.subheader("Plain-English Explanation")
                        st.write(result["explanation"])

                        figure = suggest_chart(result["data"])
                        if figure is not None:
                            st.subheader("Visualization")
                            st.plotly_chart(figure, use_container_width=True)
                    else:
                        st.error(result["error"])
                        st.subheader("Plain-English Explanation")
                        st.write(result["explanation"])

                except Exception as error:
                    show_friendly_error(error)


elif page == "Database Schema":
    st.header("Database Schema")
    st.caption(f"Database: {database_name}")

    if database_mode == "uploaded" and selected_db_path is None:
        st.warning("Upload a SQLite database to view its schema.")
    else:
        try:
            schema_text = get_schema_text(selected_db_path)
            st.code(schema_text, language="text")
        except Exception as error:
            show_friendly_error(error)


elif page == "Query Logs":
    st.header("Query Logs")

    if LOG_PATH.exists() and LOG_PATH.stat().st_size > 0:
        logs_df = pd.read_csv(LOG_PATH)
        if "timestamp" in logs_df.columns:
            logs_df = logs_df.sort_values("timestamp", ascending=False)

        st.dataframe(logs_df, use_container_width=True)
        st.download_button(
            "Download logs CSV",
            data=logs_df.to_csv(index=False),
            file_name="query_logs.csv",
            mime="text/csv"
        )
    else:
        st.info("No query logs found yet. Run some questions first.")


elif page == "Evaluation":
    st.header("Evaluation")

    if database_mode == "default":
        evaluation_use_mock = st.checkbox(
            "Use offline demo mode",
            value=True,
            help="Runs Chinook evaluation questions without Gemini API."
        )
    else:
        evaluation_use_mock = False
        st.warning(
            "Offline demo mode only supports Chinook sample questions. "
            "Uploaded databases require API-based SQL generation."
        )

    if st.button("Run Evaluation"):
        if database_mode == "uploaded" and selected_db_path is None:
            st.error("Please upload a valid SQLite database before running evaluation.")
        else:
            with st.spinner("Running evaluation..."):
                try:
                    metrics, results_df = run_evaluation(
                        use_mock=evaluation_use_mock,
                        db_path=selected_db_path,
                        database_mode=database_mode,
                        database_name=database_name
                    )

                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("Total", metrics["total_questions"])
                    col2.metric(
                        "Success Rate",
                        f"{metrics['execution_success_rate'] * 100:.1f}%"
                    )
                    col3.metric(
                        "Correction Successes",
                        metrics["correction_success_count"]
                    )
                    col4.metric("Avg Latency", metrics["average_latency"])
                    col5.metric("Failures", metrics["failed_questions_count"])

                    st.dataframe(results_df, use_container_width=True)
                    st.download_button(
                        "Download evaluation CSV",
                        data=results_df.to_csv(index=False),
                        file_name="evaluation_results.csv",
                        mime="text/csv"
                    )
                    st.caption(f"Saved to {RESULTS_PATH}")
                except Exception as error:
                    show_friendly_error(error)


elif page == "About / Limitations":
    st.header("About QueryMind")

    st.write(
        """
        QueryMind currently supports SQLite databases. It includes Chinook as the
        default demo database and allows users to upload custom SQLite database
        files. For each selected database, QueryMind extracts schema metadata
        dynamically and uses it for schema-aware SQL generation.
        """
    )

    st.subheader("Current MVP Features")

    st.markdown(
        """
        - Default Chinook SQLite database support
        - Uploaded SQLite database support for .db, .sqlite, and .sqlite3 files
        - Schema-aware SQL generation
        - SELECT-only SQL validation
        - Safe SQLite execution
        - Error capture and self-correction loop
        - Offline Chinook demo mode for predefined questions
        - Query logs, evaluation dashboard, and simple SQL visualizations
        """
    )

    st.subheader("Honest Limitations")

    st.markdown(
        """
        - LLM-generated SQL may be incorrect.
        - Self-correction improves robustness but does not guarantee correctness.
        - Offline demo mode only supports predefined Chinook questions.
        - Uploaded databases require API-based SQL generation.
        - QueryMind currently supports SQLite only, not every database system.
        - This is a portfolio prototype, not a production BI tool.
        """
    )
