# Docker Event Pipeline

`docker-event-pipeline` is a small Docker Compose learning project.

It is intentionally simple. The goal is not to build a feature-rich application. The goal is to demonstrate how multiple containers work together in one Compose stack:

- multiple services
- internal Docker networking
- service-name based communication
- published ports vs internal ports
- named volumes
- environment variables
- logs
- `docker compose exec`
- a background worker container
- Nginx as the public entrypoint

## What This Project Does

The stack accepts click events through a small FastAPI app.

When you send `POST /click`:

1. Nginx receives the public HTTP request on `localhost:8080`.
2. Nginx forwards the request to the internal `api` service.
3. The API inserts a row into PostgreSQL with status `received`.
4. The API pushes the row ID into a Redis list named `click_jobs`.
5. The `worker` container consumes jobs from Redis.
6. The worker updates the PostgreSQL row status to `processed`.

This gives you a compact example of an API container, a database, a queue, a worker, and a reverse proxy.

## Architecture

```text
Host machine
    |
    |  http://localhost:8080
    v
+---------+      Docker network: backend
|  nginx  | ---------------------------------------------+
+---------+                                              |
    | proxy_pass to api:8000                             |
    v                                                    |
+---------+      reads/writes      +------------+        |
|   api   | ---------------------> |  postgres  |        |
+---------+                        +------------+        |
    |                                                    |
    | pushes click IDs                                   |
    v                                                    |
+---------+      pops jobs         +------------+        |
|  redis  | <--------------------> |   worker   | -------+
+---------+                        +------------+

Public ports:
- `nginx` -> `localhost:8080`
- `adminer` -> `localhost:8081`

Internal-only services:
- `api` -> `8000`
- `postgres` -> `5432`
- `redis` -> `6379`
- `worker` -> no published port
```

## Services

| Service | Purpose | Public? | Notes |
| --- | --- | --- | --- |
| `nginx` | Reverse proxy and public entrypoint | Yes | Published on `localhost:8080` |
| `api` | FastAPI application | No | Reached by other containers as `http://api:8000` |
| `postgres` | Stores click rows | No | Uses a named volume for persistent data |
| `redis` | Stores queued click job IDs | No | Reached by other containers as `redis:6379` |
| `worker` | Background job consumer | No | Reads from Redis and updates Postgres |
| `adminer` | Database inspection UI | Yes | Published on `localhost:8081` |

## How Containers Communicate

- The host machine talks to published ports such as `localhost:8080` and `localhost:8081`.
- Containers on the Compose network talk to each other by service name.
- The API uses `postgres` and `redis` as hostnames because those are Compose service names.
- Nginx talks to the API as `api:8000`.
- The worker talks to Redis and Postgres over the internal Docker network.

The most common beginner mistake is mixing up `localhost` and service names:

- Use `localhost:8080` from your host machine.
- Use `api:8000`, `postgres:5432`, and `redis:6379` from inside containers.
- Do not use `localhost` inside the `api` or `worker` containers for Postgres or Redis. Inside a container, `localhost` means that same container, not another service.

More detail: [docs/networking.md](/home/gabe_desktop/code/docker-event-pipeline/docs/networking.md)

## Setup

Copy the example environment file if needed:

```bash
cp .env.example .env
```

Then start the project:

```bash
docker compose up -d --build
```

Check that the containers are running:

```bash
docker compose ps
```

## Commands

```bash
docker compose up -d --build
docker compose ps
curl http://localhost:8080/health
curl -X POST http://localhost:8080/click
curl http://localhost:8080/stats
docker compose logs -f worker
docker compose exec redis redis-cli LRANGE click_jobs 0 -1
docker compose down
docker compose down -v
```

More command examples: [docs/commands.md](/home/gabe_desktop/code/docker-event-pipeline/docs/commands.md)

## Test The API Through Nginx

Health check:

```bash
curl http://localhost:8080/health
```

Expected response:

```json
{"status":"ok"}
```

Create a click:

```bash
curl -X POST http://localhost:8080/click
```

Expected response shape:

```json
{"id":1,"status":"received","queued":"true"}
```

View aggregate stats:

```bash
curl http://localhost:8080/stats
```

If the worker has processed the job, you should see a `processed` count.

## Inspect Redis And Postgres

Inspect the Redis queue:

```bash
docker compose exec redis redis-cli LRANGE click_jobs 0 -1
```

Open a PostgreSQL shell inside the database container:

```bash
docker compose exec postgres psql -U eventuser -d eventdb
```

Example SQL:

```sql
SELECT id, status, created_at
FROM clicks
ORDER BY id;
```

Or inspect the database in Adminer:

- URL: `http://localhost:8081`
- System: `PostgreSQL`
- Server: `postgres`
- Username: value of `POSTGRES_USER`
- Password: value of `POSTGRES_PASSWORD`
- Database: value of `POSTGRES_DB`

## View Logs

All services:

```bash
docker compose logs -f
```

Worker only:

```bash
docker compose logs -f worker
```

API only:

```bash
docker compose logs -f api
```

## Stop And Reset

Stop containers but keep the database volume:

```bash
docker compose down
```

Stop containers and delete the named volume:

```bash
docker compose down -v
```

Use `docker compose down -v` when you want a completely fresh PostgreSQL data directory. This matters because PostgreSQL initialization settings are only applied when the volume is first created.

## Common Mistakes

- Using `localhost` inside a container when you should use a Compose service name like `postgres` or `redis`.
- Expecting the `api` service to be reachable directly from the host. In this project, the public HTTP entrypoint is Nginx on `localhost:8080`.
- Forgetting that `postgres` and `redis` do not publish ports to the host.
- Changing `POSTGRES_USER`, `POSTGRES_PASSWORD`, or `POSTGRES_DB` in `.env` and expecting an existing PostgreSQL volume to reinitialize automatically.
- Using `docker compose down` when you actually need `docker compose down -v` to reset persistent database state.

Troubleshooting guide: [docs/troubleshooting.md](docs/troubleshooting.md)
