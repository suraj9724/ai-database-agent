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