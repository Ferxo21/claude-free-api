#!/usr/bin/env bash
set -e

# Carga .env si existe
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

uvicorn app.main:app --host 0.0.0.0 --port 8080
