"""
Ejemplo de cliente para llamar a la API OpenAI-compatible que expone este repo.
"""
import requests

API_URL = "http://localhost:8080/v1/chat/completions"

payload = {
    "model": "local-claude-free",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Escribe un pequeño poema en español sobre la luna."}
    ],
    "max_tokens": 150,
}

r = requests.post(API_URL, json=payload)
print(r.status_code)
print(r.json())
