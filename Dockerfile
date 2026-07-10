FROM python:3.11-slim

WORKDIR /app

# System build dependencies (needed for psycopg2, cryptography, bcrypt etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY requirement.txt .

RUN uv pip install --system -r requirement.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]