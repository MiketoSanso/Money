FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install psycopg2-binary

COPY . .

ENV FLASK_RUN_HOST=0.0.0.0

CMD ["python", "app.py"]