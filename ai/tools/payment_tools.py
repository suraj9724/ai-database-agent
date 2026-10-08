from database.connection import get_connection
from tools.invoice_tools import get_customer_invoices

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
        
        
def get_customer_outstanding_details(
    customer_name: str,
) -> dict | None:
    """
    Return both the customer's outstanding amount
    and the invoices that make up that amount.

    This is a higher-level business operation.

    Internally it combines:
        1. Customer outstanding balance
        2. Customer invoice list

    Keeping this logic in Python means the LLM does not
    need to coordinate multiple database tools itself.
    """

    # ---------------------------------------------
    # Get the customer's outstanding balance.
    # ---------------------------------------------

    outstanding = get_customer_outstanding_by_name(
        customer_name
    )

    if outstanding is None:
        return None

    # ---------------------------------------------
    # Get all invoices belonging to the customer.
    # ---------------------------------------------

    invoices = get_customer_invoices(
        customer_name
    )

    # ---------------------------------------------
    # Return one clean result to the LLM.
    # ---------------------------------------------

    return {
    "customer_id": outstanding["customer_id"],
    "customer_name": outstanding["customer_name"],
    "outstanding_amount": outstanding["outstanding_amount"],

    # These are raw database values.
    # The LLM should present them exactly as returned.
    "invoices": [
        {
            "invoice_number": invoice["invoice_number"],
            "invoice_date": invoice["invoice_date"],
            "total": invoice["total"],
            "status": invoice["status"],
        }
        for invoice in invoices
    ],
}
    

def get_total_unpaid_amount() -> dict:
    """
    Calculate the total value of unpaid invoices.

    The calculation is performed by PostgreSQL rather than
    asking the LLM to add invoice amounts.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(total), 0)

                FROM invoices

                WHERE status = 'unpaid';
                """
            )

            row = cursor.fetchone()

            return {
                "total_unpaid_amount": float(row[0])
            }

    finally:
        connection.close()
        
        
def get_customer_payments(
    customer_name: str,
) -> dict | None:
    """
    Return the payments received from a specific customer.

    This is different from get_revenue(), which calculates
    revenue for a date range across all customers.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    c.id,
                    c.name,
                    COALESCE(SUM(p.amount), 0) AS total_received

                FROM customers c

                LEFT JOIN invoices i
                    ON i.customer_id = c.id

                LEFT JOIN payments p
                    ON p.invoice_id = i.id

                WHERE c.name ILIKE %s

                GROUP BY c.id, c.name;
                """,
                (f"%{customer_name}%",),
            )

            rows = cursor.fetchall()

            if not rows:
                return None

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
                "total_received": float(row[2]),
            }

    finally:
        connection.close()
        
def get_customer_with_highest_outstanding() -> dict | None:
    """
    Find the customer with the highest outstanding balance.

    This is useful for:
        - Prioritizing collections efforts
        - Understanding who owes the most
        - Reporting on key accounts
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

                GROUP BY c.id, c.name

                ORDER BY outstanding DESC

                LIMIT 1;
                """
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
        
        
def get_highest_invoice_for_customer(
    customer_id: int | None = None,
    customer_name: str | None = None,
) -> dict | None:
    """
    Find the single invoice with the highest outstanding balance
    for a specific customer.

    Supports lookup either by customer_id or customer_name.

    Returns:
        - The highest invoice (invoice number, total, amount paid, outstanding balance)
        - The customer's ID and name

    This is useful for:
        - Focusing collections on a specific invoice
        - Understanding the largest open debt items per customer
        - Prioritizing payment recovery efforts
    """

    if customer_id is None and not customer_name:
        return {
            "error": "Either customer_id or customer_name must be provided."
        }

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # ----------------------------------------
            # Resolve customer if customer_name is provided
            # ----------------------------------------
            if customer_id is None and customer_name:
                cursor.execute(
                    """
                    SELECT id, name
                    FROM customers
                    WHERE name ILIKE %s
                    ORDER BY name;
                    """,
                    (f"%{customer_name}%",),
                )

                cust_rows = cursor.fetchall()

                if not cust_rows:
                    return None

                if len(cust_rows) > 1:
                    return {
                        "error": "Multiple customers matched the supplied name.",
                        "matches": [
                            {
                                "customer_id": r[0],
                                "customer_name": r[1],
                            }
                            for r in cust_rows
                        ],
                    }

                customer_id = cust_rows[0][0]
                customer_name = cust_rows[0][1]

            elif customer_id is not None and not customer_name:
                cursor.execute(
                    """
                    SELECT id, name
                    FROM customers
                    WHERE id = %s;
                    """,
                    (customer_id,),
                )

                customer_row = cursor.fetchone()

                if customer_row is None:
                    return None

                customer_name = customer_row[1]

            # ----------------------------------------
            # Find the highest outstanding invoice
            # ----------------------------------------
            cursor.execute(
                """
                SELECT
                    i.id,
                    i.invoice_number,
                    i.total,

                    COALESCE(
                        SUM(p.amount)
                    , 0) AS total_paid,

                    i.total -
                    COALESCE(
                        SUM(p.amount)
                    , 0) AS outstanding_amount

                FROM invoices i

                LEFT JOIN payments p
                    ON p.invoice_id = i.id

                WHERE i.customer_id = %s

                GROUP BY i.id

                ORDER BY outstanding_amount DESC

                LIMIT 1;
                """,
                (customer_id,),
            )

            invoice_row = cursor.fetchone()

            if invoice_row is None:
                return {
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "highest_invoice": None,
                    "message": "No invoices found for this customer.",
                }

            # ----------------------------------------
            # Build the result
            # ----------------------------------------
            return {
                "customer_id": customer_id,
                "customer_name": customer_name,

                "highest_invoice": {
                    "invoice_id": invoice_row[0],
                    "invoice_number": invoice_row[1],
                    "total": float(invoice_row[2]),
                    "total_amount": float(invoice_row[2]),
                    "amount_paid": float(invoice_row[3]),
                    "outstanding_amount": float(invoice_row[4]),
                }
            }

    finally:
        connection.close()