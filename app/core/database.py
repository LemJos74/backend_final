from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg import Connection

from app.core.config import settings


def create_connection() -> Connection:
    """Create a new psycopg 3 connection from the .env settings."""
    return psycopg.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=5,
    )


@contextmanager
def get_connection() -> Iterator[Connection]:
    """Provide a connection and close it when the context exits."""
    connection = create_connection()
    try:
        yield connection
    finally:
        connection.close()
