import os

import psycopg2
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """
    Create and return a PostgreSQL database connection.

    Keeping the connection logic in one place means
    our tools won't need to know how the database is configured.
    """

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    return psycopg2.connect(DATABASE_URL)