# Running the API Locally or with Docker

The API uses Python 3.12 and PostgreSQL 17. PostgreSQL runs in a separate Docker container and stores its data in the Docker-managed volume `csl_postgres_data`.

## 1. Start PostgreSQL from Docker or Local (make sure PostgreSQL running on port 5432)

From the project root, run:

```powershell
docker compose -f src/core/postgress-docker/compose.yaml up -d --wait
```

## 2. Configure the local environment

Use your `.env` file when running the API directly on Windows:

```env
DATABASE_URL=postgresql+psycopg2://root:root@localhost:5432/CSL_SMS
```

Keep your other required environment variables, including your JWT secret and any Google OAuth credentials.

## 3. Run the API directly using Uvicorn (Local Enviroment)

 run these commands from the project root:

```powershell
uv sync
uvicorn  __init__:app --reload
```

If the FastAPI instance has a different variable name than `app`, adjust the import target accordingly.

The API and interactive documentation should be available at:

- API: http://localhost:8000
- Swagger documentation: http://localhost:8000/docs

## 4. Alternatively, run the API with Docker

Configure `.env.docker` to connect to PostgreSQL through the host's published port:

```env
DATABASE_URL=postgresql+psycopg2://root:root@host.docker.internal:5432/CSL_SMS
```

Build and run the API image:

```powershell
docker build -t csl-api .
docker run --rm --name csl-api --add-host=host.docker.internal:host-gateway --env-file .env.docker -p 8000:8000 csl-api
```

The Docker image applies pending Alembic migrations before starting Uvicorn, according to its configured startup command. If the migrations fail, the API container should exit instead of starting with an outdated schema.

The API and interactive docs are available at:

- API: http://localhost:8000
- Swagger documentation: http://localhost:8000/docs

## 5. Database persistence and safety

The Compose configuration uses a named volume:

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
    name: csl_postgres_data
```

Removing or recreating the PostgreSQL container normally does not delete this named volume. **Avoid `docker compose down --volumes` and `docker volume rm csl_postgres_data` if you need to preserve your database data.**

Both API workflows should use the same `CSL_SMS` database as long as they connect to the same running PostgreSQL container through port `5432`. Changing `localhost` to `host.docker.internal` changes the route to the server; it does not itself delete or move data.
