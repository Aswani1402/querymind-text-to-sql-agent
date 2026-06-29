def generate_simple_explanation(
    question: str,
    final_sql: str,
    success: bool,
    row_count: int | None = None
) -> str:
    """
    Create a simple plain-English explanation without calling an LLM.
    """
    if not success:
        return (
            "QueryMind generated SQL for the question, but execution failed. "
            "Review the error message and generated SQL before using the result."
        )

    question_text = question.lower()
    sql_text = (final_sql or "").lower()

    if "top 5 customers" in question_text or "total invoice amount" in question_text:
        explanation = (
            "This query joins Customer and Invoice, groups invoices by customer, "
            "sums total invoice amount, and returns the highest spending customers."
        )
    elif "genre" in question_text and "revenue" in question_text:
        explanation = (
            "This query joins Genre, Track, and InvoiceLine to calculate revenue "
            "by genre and returns the highest revenue genre."
        )
    elif "spent more than 40" in question_text:
        explanation = (
            "This query joins Customer and Invoice, totals each customer's invoice "
            "amounts, and returns customers whose total spending is above 40 dollars."
        )
    elif "invoices by year" in question_text or "strftime" in sql_text:
        explanation = (
            "This query extracts the year from invoice dates and counts invoices "
            "for each year."
        )
    elif "employees support" in question_text or "support the most customers" in question_text:
        explanation = (
            "This query joins Employee and Customer, counts customers assigned to "
            "each support representative, and returns the highest support counts."
        )
    elif "billing country" in question_text or "sales by" in question_text:
        explanation = (
            "This query groups invoices by billing country and sums invoice totals "
            "to show sales by country."
        )
    elif "most expensive tracks" in question_text:
        explanation = (
            "This query sorts tracks by unit price and returns the most expensive tracks."
        )
    elif "number of customers" in question_text and "countr" in question_text:
        explanation = (
            "This query groups customers by country and counts how many customers "
            "are in each country."
        )
    elif "artist" in question_text and "most tracks" in question_text:
        explanation = (
            "This query joins Artist, Album, and Track, counts tracks for each artist, "
            "and returns the artist with the largest track count."
        )
    else:
        explanation = (
            "This query answers the user question by running the generated SQL "
            "against the selected SQLite database."
        )

    if row_count is not None:
        explanation += f" The result contains {row_count} row(s)."

    return explanation
