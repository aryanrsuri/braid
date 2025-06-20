FROM python:3.13-slim

WORKDIR /app

COPY . /app

# RUN python -m venv .venv && .venv/bin/pip install -r requirements.txt

CMD [".venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

