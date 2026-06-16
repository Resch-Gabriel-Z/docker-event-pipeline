import os
import time
from contextlib import contextmanager

import psycopg
from fastapi import FastAPI


app = FastAPI()


def get_database_config() -> dict[str, str]:
    """Read database settings from environment variables."""
    return {
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "host": os.environ["POSTGRES_HOST"],
        "port": os.environ["POSTGRES_PORT"],
    }


@contextmanager
def get_connection():
    """Open a PostgreSQL connection and close it afterwards."""
    config = get_database_config()
    connection = psycopg.connect(**config)

    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the clicks table if it does not exist yet."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS clicks (
                    id SERIAL PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
        connection.commit()


def wait_for_database(max_attempts: int = 20, delay_seconds: float = 1.0) -> None:
    """Wait until PostgreSQL accepts connections."""
    for attempt in range(1, max_attempts + 1):
        try:
            initialize_database()
            print("Database is ready.")
            return
        except Exception as error:
            print(f"Database not ready yet. Attempt {attempt}/{max_attempts}. Error: {error}")
            time.sleep(delay_seconds)

    raise RuntimeError("Database did not become ready in time.")


@app.on_event("startup")
def startup_event() -> None:
    """Run setup code when the API container starts."""
    wait_for_database()


@app.get("/health")
def health() -> dict[str, str]:
    """Simple endpoint to check whether the API is running."""
    return {"status": "ok"}


@app.post("/click")
def create_click() -> dict[str, int | str]:
    """Insert one click event into the database."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO clicks (status)
                VALUES (%s)
                RETURNING id;
                """,
                ("received",),
            )
            click_id = cursor.fetchone()[0]

        connection.commit()

    return {"id": click_id, "status": "received"}


@app.get("/stats")
def stats() -> dict[str, int]:
    """Return how many clicks exist per status."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT status, COUNT(*)
                FROM clicks
                GROUP BY status;
                """
            )
            rows = cursor.fetchall()

    return {status: count for status, count in rows}
