from database.connection import get_connection


def get_invoice(invoice_number: str) -> dict | None:
    """
    Fetch a complete invoice using its invoice number.

    This tool joins:
        invoices
        customers
        invoice_items
        payments

    so the agent receives useful business information
    instead of raw database rows.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # -----------------------------------------
            # Fetch invoice + customer information
            # -----------------------------------------

            cursor.execute(
                """
                SELECT
                    i.id,
                    i.invoice_number,
                    i.invoice_date,
                    i.subtotal,
                    i.gst,
                    i.total,
                    i.status,

                    c.id AS customer_id,
                    c.name AS customer_name,
                    c.email AS customer_email,
                    c.city AS customer_city,
                    c.country AS customer_country

                FROM invoices i

                JOIN customers c
                    ON c.id = i.customer_id

                WHERE i.invoice_number = %s;
                """,
                (invoice_number,),
            )

            invoice_row = cursor.fetchone()

            # Invoice doesn't exist.
            if invoice_row is None:
                return None

            (
                invoice_id,
                invoice_number,
                invoice_date,
                subtotal,
                gst,
                total,
                status,
                customer_id,
                customer_name,
                customer_email,
                customer_city,
                customer_country,
            ) = invoice_row

            # -----------------------------------------
            # Fetch invoice items
            # -----------------------------------------

            cursor.execute(
                """
                SELECT
                    description,
                    quantity,
                    unit_price,
                    amount

                FROM invoice_items

                WHERE invoice_id = %s

                ORDER BY id;
                """,
                (invoice_id,),
            )

            item_rows = cursor.fetchall()

            items = []

            for row in item_rows:
                items.append(
                    {
                        "description": row[0],
                        "quantity": float(row[1]),
                        "unit_price": float(row[2]),
                        "amount": float(row[3]),
                    }
                )

            # -----------------------------------------
            # Fetch payments
            # -----------------------------------------

            cursor.execute(
                """
                SELECT
                    payment_date,
                    amount,
                    payment_method

                FROM payments

                WHERE invoice_id = %s

                ORDER BY payment_date;
                """,
                (invoice_id,),
            )

            payment_rows = cursor.fetchall()

            payments = []

            for row in payment_rows:
                payments.append(
                    {
                        "payment_date": str(row[0]),
                        "amount": float(row[1]),
                        "payment_method": row[2],
                    }
                )

            # -----------------------------------------
            # Build a clean business object
            # -----------------------------------------

            return {
                "invoice_number": invoice_number,
                "invoice_date": str(invoice_date),

                "customer": {
                    "id": customer_id,
                    "name": customer_name,
                    "email": customer_email,
                    "city": customer_city,
                    "country": customer_country,
                },

                "subtotal": float(subtotal),
                "gst": float(gst),
                "total": float(total),

                "status": status,

                "items": items,
                "payments": payments,
            }

    finally:
        connection.close()
        
     
def search_invoices(status: str) -> list[dict]:
    """
    Return invoices filtered by payment status.

    Supported statuses:
        paid
        unpaid
        partially_paid
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    i.invoice_number,
                    i.invoice_date,
                    c.name AS customer_name,
                    i.total,
                    i.status

                FROM invoices i

                JOIN customers c
                    ON c.id = i.customer_id

                WHERE i.status = %s

                ORDER BY i.invoice_date DESC;
                """,
                (status,),
            )

            rows = cursor.fetchall()

            invoices = []

            for row in rows:
                invoices.append(
                    {
                        "invoice_number": row[0],
                        "invoice_date": str(row[1]),
                        "customer_name": row[2],
                        "total": float(row[3]),
                        "status": row[4],
                    }
                )

            return invoices

    finally:
        connection.close()
        

def search_invoices_above_amount(
    amount: float,
) -> list[dict]:
    """
    Return invoices whose total is greater than
    the supplied amount.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    i.invoice_number,
                    i.invoice_date,
                    c.name AS customer_name,
                    i.total,
                    i.status

                FROM invoices i

                JOIN customers c
                    ON c.id = i.customer_id

                WHERE i.total > %s

                ORDER BY i.total DESC;
                """,
                (amount,),
            )

            rows = cursor.fetchall()

            invoices = []

            for row in rows:
                invoices.append(
                    {
                        "invoice_number": row[0],
                        "invoice_date": str(row[1]),
                        "customer_name": row[2],
                        "total": float(row[3]),
                        "status": row[4],
                    }
                )

            return invoices

    finally:
        connection.close()