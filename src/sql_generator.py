
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from schema_reader import get_schema_text
from prompt_builder import build_sql_generation_prompt
from sql_cleaner import clean_sql_output


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)


MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


def get_gemini_imports():
    try:
        from google import genai
        from google.genai import errors
    except ImportError as error:
        raise RuntimeError(
            "Gemini client package is unavailable. Install google-genai or use "
            "offline demo mode with the default Chinook database."
        ) from error

    return genai, errors


def get_gemini_client():
    genai, _ = get_gemini_imports()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Add it to .env.")

    return genai.Client(api_key=api_key)


def _is_quota_or_rate_limit_error(error: Exception) -> bool:
    message = str(error).lower()
    return (
        "429" in message
        or "resource_exhausted" in message
        or "quota" in message
        or "rate limit" in message
        or "rate-limit" in message
    )


def _is_unavailable_error(error: Exception) -> bool:
    message = str(error).lower()
    return "503" in message or "unavailable" in message


def call_gemini_with_retry(prompt: str, max_retries: int = 3) -> tuple[str, str]:
    """
    Call Gemini with retry and fallback models.

    Returns:
        raw_text, model_used
    """
    client = get_gemini_client()
    _, errors = get_gemini_imports()

    last_error = None

    for model_name in MODEL_CANDIDATES:
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                return response.text, model_name

            except errors.ServerError as e:
                last_error = e
                wait_time = 2 ** attempt
                print(
                    f"[Retry] {model_name} failed with server error. "
                    f"Attempt {attempt}/{max_retries}. Waiting {wait_time}s..."
                )
                time.sleep(wait_time)

            except errors.APIError as e:
                last_error = e

                if _is_unavailable_error(e):
                    wait_time = 2 ** attempt
                    print(
                        f"[Retry] {model_name} is temporarily unavailable. "
                        f"Attempt {attempt}/{max_retries}. Waiting {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

                if _is_quota_or_rate_limit_error(e):
                    print(
                        f"[Fallback] {model_name} hit quota or rate limits: {e}"
                    )
                    break

                print(f"[Fallback] {model_name} failed with API error: {e}")
                break

    raise RuntimeError(f"All Gemini model attempts failed. Last error: {last_error}")


def generate_sql(user_question: str, schema_text: str | None = None) -> dict:
    if schema_text is None:
        schema_text = get_schema_text()

    prompt = build_sql_generation_prompt(
        user_question=user_question,
        schema_text=schema_text
    )

    raw_output, model_used = call_gemini_with_retry(prompt)

    cleaned_sql = clean_sql_output(raw_output)

    return {
        "question": user_question,
        "raw_output": raw_output,
        "sql": cleaned_sql,
        "model_used": model_used
    }


if __name__ == "__main__":
    question = "Show the top 5 customers by total invoice amount."

    result = generate_sql(question)

    print("Question:")
    print(result["question"])

    print("\nModel used:")
    print(result["model_used"])

    print("\nRaw model output:")
    print(result["raw_output"])

    print("\nCleaned SQL:")
    print(result["sql"])
