from pathlib import Path

from database.connection import get_connection



def create_tables():
    """
    Read schema.sql and create all required tables.
    """

    schema_path = Path(__file__).parent / "schema.sql"

    with open(schema_path, "r", encoding="utf-8") as file:
        schema = file.read()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(schema)

        connection.commit()

        print("Database tables created successfully.")

    finally:
        connection.close()


def seed_data():
    """
    Insert sample business data into the database.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            # -------------------------
            # Customers
            # -------------------------

            cursor.execute(
                """
                INSERT INTO customers
                    (name, email, city, country)
                VALUES
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    "Global Retail Systems",
                    "accounts@globalretail.com",
                    "Melbourne",
                    "Australia",

                    "TechNova Solutions",
                    "finance@technova.com",
                    "Ahmedabad",
                    "India",

                    "BlueSky Enterprises",
                    "billing@bluesky.com",
                    "Mumbai",
                    "India",
                ),
            )

            customer_ids = [
                row[0]
                for row in cursor.fetchall()
            ]

            global_retail_id = customer_ids[0]
            technova_id = customer_ids[1]
            bluesky_id = customer_ids[2]

            # -------------------------
            # Invoices
            # -------------------------

            cursor.execute(
                """
                INSERT INTO invoices
                    (
                        invoice_number,
                        customer_id,
                        invoice_date,
                        subtotal,
                        gst,
                        total,
                        status
                    )
                VALUES
                    (
                        %s, %s, %s,
                        %s, %s, %s, %s
                    ),
                    (
                        %s, %s, %s,
                        %s, %s, %s, %s
                    ),
                    (
                        %s, %s, %s,
                        %s, %s, %s, %s
                    ),
                    (
                        %s, %s, %s,
                        %s, %s, %s, %s
                    )
                RETURNING id;
                """,
                (
                    # Invoice 1
                    "INV-1001",
                    global_retail_id,
                    "2026-09-05",
                    40000,
                    7200,
                    47200,
                    "paid",

                    # Invoice 2
                    "INV-1002",
                    technova_id,
                    "2026-09-12",
                    55000,
                    9900,
                    64900,
                    "unpaid",

                    # Invoice 3
                    "INV-1003",
                    bluesky_id,
                    "2026-09-20",
                    25000,
                    4500,
                    29500,
                    "partially_paid",

                    # Invoice 4
                    "INV-1004",
                    technova_id,
                    "2026-10-02",
                    30000,
                    5400,
                    35400,
                    "unpaid",
                ),
            )

            invoice_ids = [
                row[0]
                for row in cursor.fetchall()
            ]

            invoice_1001 = invoice_ids[0]
            invoice_1002 = invoice_ids[1]
            invoice_1003 = invoice_ids[2]
            invoice_1004 = invoice_ids[3]

            # -------------------------
            # Invoice Items
            # -------------------------

            cursor.execute(
                """
                INSERT INTO invoice_items
                    (
                        invoice_id,
                        description,
                        quantity,
                        unit_price,
                        amount
                    )
                VALUES
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s),
                    (%s, %s, %s, %s, %s);
                """,
                (
                    # INV-1001
                    invoice_1001,
                    "Website Development",
                    1,
                    30000,
                    30000,

                    invoice_1001,
                    "Payment Gateway Integration",
                    2,
                    5000,
                    10000,

                    # INV-1002
                    invoice_1002,
                    "Mobile Application Development",
                    1,
                    45000,
                    45000,

                    invoice_1002,
                    "Cloud Deployment",
                    1,
                    10000,
                    10000,

                    # INV-1003
                    invoice_1003,
                    "Database Optimization",
                    5,
                    3000,
                    15000,

                    invoice_1003,
                    "Security Audit",
                    1,
                    10000,
                    10000,

                    # INV-1004
                    invoice_1004,
                    "API Development",
                    1,
                    30000,
                    30000,
                ),
            )

            # -------------------------
            # Payments
            # -------------------------

            cursor.execute(
                """
                INSERT INTO payments
                    (
                        invoice_id,
                        payment_date,
                        amount,
                        payment_method
                    )
                VALUES
                    (%s, %s, %s, %s),
                    (%s, %s, %s, %s);
                """,
                (
                    # INV-1001 fully paid
                    invoice_1001,
                    "2026-09-15",
                    47200,
                    "bank_transfer",

                    # INV-1003 partially paid
                    invoice_1003,
                    "2026-09-25",
                    15000,
                    "bank_transfer",
                ),
            )

        connection.commit()

        print("Sample data inserted successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    create_tables()
    seed_data()