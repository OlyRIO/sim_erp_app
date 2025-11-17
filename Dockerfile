FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8000

COPY requirements.txt .a
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["flask", "run"]
