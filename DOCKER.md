# Running the API with Docker

The API image contains Python 3.12 and the locked project dependencies. PostgreSQL
remains a separate container.

## Start PostgreSQL

From the project root:

```powershell
docker compose -f src/core/postgress-docker/compose.yaml up -d --wait
```

PostgreSQL stores its data in the Docker-managed volume `csl_postgres_data`, so
removing or recreating the container does not remove the database. Avoid
`docker compose down --volumes` if you need to keep that data.

## Configure and start the API

Copy `.env.docker.example` to `.env.docker`, then set a private `JWT_SECRET_KEY`
and any Google OAuth credentials you use. The example database URL connects to
the PostgreSQL container through its published port.

```powershell
Copy-Item .env.docker.example .env.docker
docker build -t csl-api .
docker run --rm --name csl-api --add-host=host.docker.internal:host-gateway --env-file .env.docker -p 8000:8000 csl-api
```

On each container start, `alembic upgrade head` applies all pending migrations
before Uvicorn starts. If migrations fail, the API container exits with the
migration error instead of starting against an outdated schema.

The API and interactive docs are available at <http://localhost:8000> and
<http://localhost:8000/docs>. The container runs Uvicorn with `--reload`.

The sample PostgreSQL compose configuration uses development credentials
(`root`/`root`); change them and the matching `DATABASE_URL` before using this
setup beyond a local demonstration.
