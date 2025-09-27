FROM python:3.12-slim

WORKDIR /app

COPY service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]