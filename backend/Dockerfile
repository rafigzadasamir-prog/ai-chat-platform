FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir .

RUN mkdir -p /app/data
ENV DATABASE_URL=sqlite:////app/data/ai_chat_platform.db
ENV EMBEDDINGS_BACKEND=hashing

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
