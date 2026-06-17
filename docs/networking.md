# Networking

This project demonstrates two different ways to reach services:

- host-to-container communication
- container-to-container communication

## Host To Container Communication

From your host machine, you use `localhost` with a published port.

Examples:

- `http://localhost:8080` -> reaches the `nginx` container
- `http://localhost:8081` -> reaches the `adminer` container

Those ports are published by Docker Compose:

- `NGINX_PORT:80`
- `ADMINER_PORT:8080`

The left side is the host port. The right side is the container port.

So when you run:

```bash
curl http://localhost:8080/health
```

the request flow is:

1. your host sends traffic to port `8080`
2. Docker forwards it to port `80` in the `nginx` container
3. Nginx proxies the request to `api:8000`

## Container To Container Communication

Containers on the same Compose network reach each other by service name.

Examples in this project:

- `api` connects to PostgreSQL at `postgres:5432`
- `api` connects to Redis at `redis:6379`
- `worker` connects to PostgreSQL at `postgres:5432`
- `worker` connects to Redis at `redis:6379`
- `nginx` proxies requests to `api:8000`

Docker Compose automatically creates DNS entries for service names on the shared network. That is why `postgres` and `redis` work as hostnames inside the containers.

## Published Ports vs Internal Ports

Published ports are reachable from the host machine.

In this project:

- `nginx` is published to the host
- `adminer` is published to the host

Internal ports are only reachable by other containers on the Docker network.

In this project:

- `api` listens on `8000` internally
- `postgres` listens on `5432` internally
- `redis` listens on `6379` internally

These are not published to the host, so you do not call them as `localhost:8000`, `localhost:5432`, or `localhost:6379`.

## Why The API Uses `postgres` And `redis`

The API container is not running on your host network. It is running inside Docker on the `backend` network.

Inside that network:

- `postgres` means the PostgreSQL container
- `redis` means the Redis container

So the API must use:

- `POSTGRES_HOST=postgres`
- `REDIS_HOST=redis`

If you changed those to `localhost`, the API would try to connect to itself, not to the database or Redis containers.

## Why The Host Uses `localhost:8080`

Your browser or `curl` command runs on the host machine, not inside the Docker network.

From the host, the correct entrypoint is the published Nginx port:

```bash
curl http://localhost:8080/health
```

That works because Compose maps host port `8080` to container port `80` in `nginx`.

## Practical Rule

- From the host: use `localhost:<published-port>`
- From a container: use `<service-name>:<internal-port>`
