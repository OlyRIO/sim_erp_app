FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default port for Render (can be overridden by PORT env var)
EXPOSE 10000

# Use gunicorn for production, fallback to flask dev server
CMD if [ "$FLASK_ENV" = "development" ]; then \
      flask run --host=0.0.0.0 --port=${PORT:-8000}; \
    else \
      alembic upgrade head && \
      gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 --timeout 60 wsgi:app; \
    fi
