FROM python:3.11-slim

WORKDIR /app

# system deps for llama-cpp-python may be required on some systems (libstdc++, build-essential)
RUN apt-get update && apt-get install -y build-essential git libssl-dev libffi-dev python3-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
