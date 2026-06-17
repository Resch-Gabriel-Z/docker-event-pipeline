# Troubleshooting

## API Cannot Connect To Postgres

Symptoms:

- the API container restarts
- `docker compose logs api` shows connection errors
- requests to `http://localhost:8080/health` fail because Nginx cannot reach the API

Checks:

```bash
docker compose ps
docker compose logs api
docker compose exec api sh
```

Inside the API container, confirm the host and port values:

```bash
echo "$POSTGRES_HOST"
echo "$POSTGRES_PORT"
```

Expected values in this project:

- `POSTGRES_HOST=postgres`
- `POSTGRES_PORT=5432`

If you used `localhost` inside the API container, that is the wrong host.

## API Cannot Connect To Redis

Symptoms:

- the API starts but `POST /click` fails
- startup logs show Redis connection errors

Checks:

```bash
docker compose logs api
docker compose exec api sh
```

Inside the API container:

```bash
echo "$REDIS_HOST"
echo "$REDIS_PORT"
```

Expected values:

- `REDIS_HOST=redis`
- `REDIS_PORT=6379`

Again, `localhost` is not correct from inside the API container.

## Worker Has No Logs Because Python Output Is Buffered

Python can buffer output, which makes background-worker logs appear delayed or missing.

This project avoids that by starting the worker with:

```text
python -u worker.py
```

If you are not seeing worker activity, confirm the container is running:

```bash
docker compose ps
docker compose logs -f worker
```

## Port Already In Use

Symptoms:

- `docker compose up` fails
- Docker reports that port `8080` or `8081` is already allocated

Fixes:

- stop the conflicting process on the host
- or change `NGINX_PORT` / `ADMINER_PORT` in `.env`

Then restart:

```bash
docker compose up -d --build
```

## Changing Postgres Credentials Does Not Affect An Existing Volume

The PostgreSQL image uses `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` only when the data directory is initialized for the first time.

If the named volume already exists, changing those variables in `.env` does not recreate the database automatically.

That is why you may see old credentials or old data even after editing `.env`.

## When To Use `docker compose down -v`

Use this when you want a full reset of persistent PostgreSQL state.

```bash
docker compose down -v
```

This removes containers and the named volume, so the next `docker compose up` starts PostgreSQL from a fresh data directory.

Use it when:

- you want to reset the demo data
- you changed PostgreSQL initialization variables and want them applied from scratch
- you suspect the database volume contains stale state from an older run

Do not use it if you want to keep the current database contents.
