# Database Implementation Tasks

1. ~Add DB dependencies (SQLAlchemy, Flask-SQLAlchemy, psycopg2-binary, alembic)~
2. ~Add Postgres service to docker-compose.yml~
2a. ~Move credentials to .env and wire docker-compose to use it~
3. ~Create `app/extensions.py` with `db = SQLAlchemy()`~
4. ~Create `app/models.py` with initial models (Customer, Sim, Assignment)~
4a. ~Refactor models into `app/models/` package with separate files~
5. ~Modify `app/__init__.py` to configure and initialize DB~
6. ~Rebuild and run containers to verify~
7. ~Initialize Alembic migrations~
8. ~Update README with DB instructions~
