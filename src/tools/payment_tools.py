from database.connection import get_connection


def get_revenue(
    start_date: str,
    end_date: str,
) -> dict:
    """
    Calculate revenue from paid payments between two dates.

    Important:
    We calculate revenue from the payments table,
    rather than simply adding invoice totals.

    This means partially-paid invoices are handled correctly.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(amount), 0)

                FROM payments

                WHERE payment_date >= %s
                  AND payment_date <= %s;
                """,
                (start_date, end_date),
            )

            row = cursor.fetchone()

            total_revenue = float(row[0])

            return {
                "start_date": start_date,
                "end_date": end_date,
                "revenue": total_revenue,
            }

    finally:
        connection.close()
        
        
def get_outstanding_amount() -> dict:
    """
    Calculate the total outstanding amount across invoices.

    Outstanding amount:

        invoice total - payments received

    Only invoices with a remaining balance contribute
    to the outstanding amount.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    COALESCE(
                        SUM(
                            i.total -
                            COALESCE(
                                (
                                    SELECT SUM(p.amount)
                                    FROM payments p
                                    WHERE p.invoice_id = i.id
                                ),
                                0
                            )
                        ),
                        0
                    )

                FROM invoices i;
                """
            )

            row = cursor.fetchone()

            return {
                "outstanding_amount": float(row[0])
            }

    finally:
        connection.close()
        
def get_customer_outstanding(customer_id: int) -> dict | None:
    """
    Calculate the outstanding balance for one customer.

    Outstanding balance is:

        invoice total - payments received

    across all invoices belonging to that customer.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    c.id,
                    c.name,

                    COALESCE(
                        SUM(
                            i.total -
                            COALESCE(
                                (
                                    SELECT SUM(p.amount)
                                    FROM payments p
                                    WHERE p.invoice_id = i.id
                                ),
                                0
                            )
                        ),
                        0
                    ) AS outstanding

                FROM customers c

                LEFT JOIN invoices i
                    ON i.customer_id = c.id

                WHERE c.id = %s

                GROUP BY c.id, c.name;
                """,
                (customer_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return {
                "customer_id": row[0],
                "customer_name": row[1],
                "outstanding_amount": float(row[2]),
            }

    finally:
        connection.close()
        
        
def get_customer_outstanding_by_name(
    customer_name: str,
) -> dict | None:
    """
    Calculate the outstanding balance for a customer
    using their name.

    This combines customer lookup and outstanding calculation
    into one controlled business operation.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    c.id,
                    c.name,

                    COALESCE(
                        SUM(
                            i.total -
                            COALESCE(
                                (
                                    SELECT SUM(p.amount)
                                    FROM payments p
                                    WHERE p.invoice_id = i.id
                                ),
                                0
                            )
                        ),
                        0
                    ) AS outstanding

                FROM customers c

                LEFT JOIN invoices i
                    ON i.customer_id = c.id

                WHERE c.name ILIKE %s

                GROUP BY c.id, c.name

                ORDER BY c.name;
                """,
                (f"%{customer_name}%",),
            )

            rows = cursor.fetchall()

            if not rows:
                return None

            # For now, require a unique customer match.
            if len(rows) > 1:
                return {
                    "error": "Multiple customers matched the supplied name.",
                    "matches": [
                        {
                            "customer_id": row[0],
                            "customer_name": row[1],
                        }
                        for row in rows
                    ],
                }

            row = rows[0]

            return {
                "customer_id": row[0],
                "customer_name": row[1],
                "outstanding_amount": float(row[2]),
            }

    finally:
        connection.close()