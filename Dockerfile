FROM python:3.12-slim

WORKDIR /main

ENV PYTHONUNBUFFERED=1

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend

COPY frontend ./frontend

EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
