import os
import time
from contextlib import contextmanager

import psycopg
import redis


QUEUE_NAME = "click_jobs"


def get_database_config() -> dict[str, str]:
    return {
        "dbname": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "host": os.environ["POSTGRES_HOST"],
        "port": os.environ["POSTGRES_PORT"],
    }


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        decode_responses=True,
    )


@contextmanager
def get_connection():
    connection = psycopg.connect(**get_database_config())

    try:
        yield connection
    finally:
        connection.close()


def process_click(click_id: str) -> None:
    print(f"Processing click {click_id}...")

    time.sleep(1)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE clicks
                SET status = %s
                WHERE id = %s;
                """,
                ("processed", click_id),
            )

        connection.commit()

    print(f"Processed click {click_id}.")


def main() -> None:
    redis_client = get_redis_client()

    print("Worker started. Waiting for jobs...")

    while True:
        queue_name, click_id = redis_client.blpop(QUEUE_NAME)
        print(f"Received job from {queue_name}: {click_id}")
        process_click(click_id)


if __name__ == "__main__":
    main()
