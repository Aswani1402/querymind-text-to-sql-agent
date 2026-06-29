def generate_mock_sql(user_question: str) -> dict:
    """
    Offline fallback SQL generator for demo/testing when API quota is exhausted.

    This supports common Chinook demo questions.
    """

    question = user_question.lower().strip()

    if "top 5 customers" in question or "total invoice amount" in question:
        sql = """
        SELECT
          C.FirstName,
          C.LastName,
          SUM(I.Total) AS TotalInvoiceAmount
        FROM Customer AS C
        JOIN Invoice AS I
          ON C.CustomerId = I.CustomerId
        GROUP BY
          C.CustomerId,
          C.FirstName,
          C.LastName
        ORDER BY
          TotalInvoiceAmount DESC
        LIMIT 5;
        """

    elif "genre" in question and "revenue" in question:
        sql = """
        SELECT
          G.Name AS Genre,
          SUM(IL.UnitPrice * IL.Quantity) AS Revenue
        FROM Genre AS G
        JOIN Track AS T
          ON G.GenreId = T.GenreId
        JOIN InvoiceLine AS IL
          ON T.TrackId = IL.TrackId
        GROUP BY
          G.Name
        ORDER BY
          Revenue DESC
        LIMIT 1;
        """

    elif "spent more than 40" in question:
        sql = """
        SELECT
          C.FirstName,
          C.LastName,
          SUM(I.Total) AS TotalSpent
        FROM Customer AS C
        JOIN Invoice AS I
          ON C.CustomerId = I.CustomerId
        GROUP BY
          C.CustomerId,
          C.FirstName,
          C.LastName
        HAVING
          SUM(I.Total) > 40
        ORDER BY
          TotalSpent DESC;
        """

    elif "invoices by year" in question:
        sql = """
        SELECT
          STRFTIME('%Y', InvoiceDate) AS InvoiceYear,
          COUNT(InvoiceId) AS NumberOfInvoices
        FROM Invoice
        GROUP BY
          InvoiceYear
        ORDER BY
          InvoiceYear;
        """

    elif "employees support" in question or "support the most customers" in question:
        sql = """
        SELECT
          E.FirstName,
          E.LastName,
          COUNT(C.CustomerId) AS NumberOfCustomersSupported
        FROM Employee AS E
        JOIN Customer AS C
          ON E.EmployeeId = C.SupportRepId
        GROUP BY
          E.EmployeeId,
          E.FirstName,
          E.LastName
        ORDER BY
          NumberOfCustomersSupported DESC
        LIMIT 1;
        """

    elif "sales by billing country" in question or "total sales by billing country" in question:
        sql = """
        SELECT
          BillingCountry,
          SUM(Total) AS TotalSales
        FROM Invoice
        GROUP BY
          BillingCountry
        ORDER BY
          TotalSales DESC;
        """

    elif "most expensive tracks" in question:
        sql = """
        SELECT
          Name,
          UnitPrice
        FROM Track
        ORDER BY
          UnitPrice DESC
        LIMIT 10;
        """

    elif (
        "highest number of customers" in question
        or "number of customers" in question
        and "countr" in question
    ):
        sql = """
        SELECT
          Country,
          COUNT(CustomerId) AS NumberOfCustomers
        FROM Customer
        GROUP BY
          Country
        ORDER BY
          NumberOfCustomers DESC,
          Country ASC
        LIMIT 10;
        """

    elif "artist" in question and "most tracks" in question:
        sql = """
        SELECT
          AR.Name AS Artist,
          COUNT(T.TrackId) AS TrackCount
        FROM Artist AS AR
        JOIN Album AS AL
          ON AR.ArtistId = AL.ArtistId
        JOIN Track AS T
          ON AL.AlbumId = T.AlbumId
        GROUP BY
          AR.ArtistId,
          AR.Name
        ORDER BY
          TrackCount DESC
        LIMIT 1;
        """

    else:
        sql = """
        SELECT
          Name,
          UnitPrice
        FROM Track
        LIMIT 10;
        """

    return {
        "question": user_question,
        "raw_output": sql.strip(),
        "sql": sql.strip(),
        "model_used": "offline_mock"
    }
