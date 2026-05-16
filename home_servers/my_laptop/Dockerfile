FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

COPY home_servers/my_laptop/requirements-local.txt .
RUN pip install --no-cache-dir -r requirements-local.txt

COPY ../../. .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
