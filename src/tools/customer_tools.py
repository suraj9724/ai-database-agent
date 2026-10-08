from database.connection import get_connection


def search_customer(customer_name: str) -> list[dict]:
    """
    Search customers by name.

    We use ILIKE so the search is case-insensitive.
    The % characters allow partial matches.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    city,
                    country

                FROM customers

                WHERE name ILIKE %s

                ORDER BY name;
                """,
                (f"%{customer_name}%",),
            )

            rows = cursor.fetchall()

            customers = []

            for row in rows:
                customers.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "email": row[2],
                        "city": row[3],
                        "country": row[4],
                    }
                )

            return customers

    finally:
        connection.close()