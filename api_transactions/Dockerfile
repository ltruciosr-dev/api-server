# api_transactions/Dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN pip install fastapi uvicorn psycopg2-binary

COPY main.py .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]