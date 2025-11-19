# sim_erp_app

## Overview
Simple Flask app containerized with Docker. Includes a PostgreSQL database service and SQLAlchemy models, with Alembic for migrations.

## Quick Start
```powershell
# Build and start in detached mode
docker compose up -d --build

# View logs
docker compose logs -f

# Stop
docker compose down
```

## Environment Variables
Values are defined in `.env` and loaded via `docker-compose.yml` (`env_file`).
- POSTGRES_DB: Database name (e.g., `app_db`)
- POSTGRES_USER: Database user (e.g., `app_user`)
- POSTGRES_PASSWORD: Database password
- DATABASE_URL: SQLAlchemy URL, e.g. `postgresql+psycopg2://app_user:app_pass@db:5432/app_db`

Notes:
- `.env` is ignored by Git and excluded from Docker build context.
- Inside Docker, the hostname `db` resolves to the PostgreSQL service.

## Application Structure
- `app/__init__.py`: Flask application factory; configures SQLAlchemy.
- `app/extensions.py`: Shared SQLAlchemy instance (`db`).
- `app/models/`: SQLAlchemy models (`Customer`, `Sim`, `Assignment`).
- `migrations/`: Alembic configuration and versions.

## IoT Data Model
- `Sim` entity: represents a mobile SIM used for IoT connectivity.
	- `iccid`: Integrated Circuit Card ID (19–20 digits). Seeder generates Croatian-style ICCIDs: `89` + `385` + MNC (`01/10/02`) + random + Luhn checksum.
	- `msisdn`: Subscriber number in E.164 format (e.g., `+3859XYYYYYYY`) using common Croatian mobile prefixes.
	- `carrier`: Human-readable operator name (e.g., Hrvatski Telekom, A1 Hrvatska, Telemach Hrvatska).
	- `status`: Simple lifecycle flag (`active`, `inactive`, `provisioning`).
- `Customer` entity: logical owner/tenant for SIMs.
- `Assignment` entity: links a `Sim` to a `Customer` with timestamp and note; unique per (customer, sim).

Future IoT extensions (ideas):
- Add device binding (IMEI), APN profile, and activation window.
- Track SIM state transitions and last network event timestamps.
- Expose simple JSON API endpoints to list/assign/unassign SIMs.

## Database & Migrations
We use SQLAlchemy models and Alembic for schema migrations.

This project relies on Alembic exclusively. Ensure you have created and applied the initial migration.

Common Alembic commands (via the web container):
```powershell
# Create a new migration (autogenerate from models)
docker compose run --rm web alembic revision --autogenerate -m "initial schema"

# Apply latest migrations
docker compose run --rm web alembic upgrade head

# Roll back last migration
docker compose run --rm web alembic downgrade -1
```

If you prefer to run Alembic on host, ensure your Python environment is active and `DATABASE_URL` is set.

## Connecting to the DB (optional)
Expose Postgres locally by adding to `docker-compose.yml` under `db`:
```yaml
		ports:
			- "5432:5432"
```
Then connect using a client:
- Host: `localhost`
- Port: `5432`
- DB/User/Password: from `.env`

## Troubleshooting
- If credentials in `.env` change after the DB has been initialized, remove the volume to reinitialize:
```powershell
docker compose down -v
docker compose up -d --build
```
- If `alembic` isn’t found on host, run commands through the `web` service as shown above.

## Seeding Data

There are two ways to seed data:

- Auto-seed on startup: controlled by `SEED_ON_START` in `.env`. This inserts a tiny sample dataset only if the DB is empty (safe for first run). Set `SEED_ON_START=false` if you prefer manual control.
- CLI seeding: bulk insert large datasets via a Flask CLI command.

CLI usage (runs inside the `web` container):

```powershell
# Seed 1k of each: customers, sims, assignments
docker compose run --rm --volume "$((Get-Location).Path):/app" web flask seed --customers 1000 --sims 1000 --assignments 1000 --reset

# Seed with custom sizes without clearing existing data
docker compose run --rm --volume "$((Get-Location).Path):/app" web flask seed --customers 500 --sims 2000 --assignments 1500
```

Notes:
- `--reset` clears existing rows before seeding.
- ICCIDs and MSISDNs are generated uniquely; assignments avoid duplicate pairs.
- For best control, disable auto-seed (`SEED_ON_START=false`) when using the CLI.

Verify seeded counts:

```powershell
docker compose exec db psql -U app_user -d app_db -c "SELECT count(*) AS customers FROM customer; SELECT count(*) AS sims FROM sim; SELECT count(*) AS assignments FROM assignment;"
```