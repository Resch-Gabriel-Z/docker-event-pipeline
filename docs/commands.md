# Commands

This project is small enough that most inspection can be done with a few Compose commands.

## Start And Check

```bash
docker compose up -d --build
docker compose ps
```

## Test The Public API

These requests go through Nginx, which is the public entrypoint for the stack.

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/click
curl http://localhost:8080/stats
```

## Logs

Follow all logs:

```bash
docker compose logs -f
```

Follow only the worker logs:

```bash
docker compose logs -f worker
```

Follow only the API logs:

```bash
docker compose logs -f api
```

## Redis Inspection

Show the queued job IDs:

```bash
docker compose exec redis redis-cli LRANGE click_jobs 0 -1
```

Open an interactive Redis shell:

```bash
docker compose exec redis redis-cli
```

## PostgreSQL Inspection

Open a `psql` shell:

```bash
docker compose exec postgres psql -U eventuser -d eventdb
```

Run a one-off query:

```bash
docker compose exec postgres psql -U eventuser -d eventdb -c "SELECT id, status, created_at FROM clicks ORDER BY id;"
```

Open Adminer in a browser:

```text
http://localhost:8081
```

Inside Adminer, use `postgres` as the server name.

## Exec Into Containers

Get a shell inside the API container:

```bash
docker compose exec api sh
```

Get a shell inside the worker container:

```bash
docker compose exec worker sh
```

## Stop And Reset

Stop the stack but keep the database volume:

```bash
docker compose down
```

Stop the stack and remove the named volume:

```bash
docker compose down -v
```
