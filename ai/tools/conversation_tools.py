from database.connection import get_connection


def create_conversation(conversation_id: str):
    """
    Create a conversation if it does not already exist.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO conversations (conversation_id)
                VALUES (%s)
                ON CONFLICT (conversation_id)
                DO NOTHING
                """,
                (conversation_id,),
            )

        connection.commit()

    finally:
        connection.close()


def save_message(
    conversation_id: str,
    role: str,
    content: str,
):
    """
    Save one message to a conversation.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO conversation_messages
                    (conversation_id, role, content)
                VALUES
                    (%s, %s, %s)
                """,
                (
                    conversation_id,
                    role,
                    content,
                ),
            )

        connection.commit()

    finally:
        connection.close()


def get_conversation_history(
    conversation_id: str,
) -> list[dict]:
    """
    Retrieve conversation messages in chronological order.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY id ASC
                """,
                (conversation_id,),
            )

            rows = cursor.fetchall()

            return [
                {
                    "role": row[0],
                    "content": row[1],
                }
                for row in rows
            ]

    finally:
        connection.close()