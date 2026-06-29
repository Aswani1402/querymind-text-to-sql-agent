import pandas as pd


def _is_year_or_date_column(series: pd.Series) -> bool:
    name = str(series.name).lower()

    if "year" in name or "date" in name:
        return True

    values = series.dropna().astype(str)
    if values.empty:
        return False

    sample = values.head(10)
    return sample.str.match(r"^\d{4}(-\d{2}-\d{2})?$").all()


def suggest_chart(df):
    """
    Suggest a simple Plotly chart for query results.
    """
    if df is None or df.empty or len(df.columns) < 2:
        return None

    try:
        import plotly.express as px
    except ImportError:
        return None

    numeric_columns = list(df.select_dtypes(include="number").columns)
    category_columns = [
        column for column in df.columns
        if column not in numeric_columns
    ]

    if len(numeric_columns) != 1 or len(category_columns) < 1:
        return None

    x_column = category_columns[0]
    y_column = numeric_columns[0]

    if _is_year_or_date_column(df[x_column]):
        return px.line(df, x=x_column, y=y_column, markers=True)

    return px.bar(df, x=x_column, y=y_column)
