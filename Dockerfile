FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY requirement.txt .

RUN uv pip install --system -r requirement.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]