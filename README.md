# Claude-free-API

Este repositorio ofrece una API local "Claude-like" (compatible en términos básicos con la API de OpenAI) y una forma simple de usar modelos open-source de forma gratuita.

Resumen rápido
- Prioriza usar Ollama si lo tienes instalado (fácil, estable y similar a un servicio local).
- Si no hay Ollama, intenta usar `llama-cpp-python` con modelos GGML/gguf locales.
- Se expone un endpoint compatible con el formato /v1/chat/completions para que clientes que esperan la API de OpenAI funcionen con mínimos cambios.

Contenido incluído
- app/main.py — FastAPI que actúa como proxy/generador.
- Dockerfile + docker-compose.yml — para levantar la API en contenedor.
- requirements.txt — dependencias (incluye opciones opcionales).
- examples/client.py — cómo llamar a la API desde Python.
- .env.example — variables de entorno para configurar Ollama o modelo local.
- README con pasos de instalación y uso.

Importante — modelos y licencias
- No incluyo pesos de modelos en el repositorio. Debes descargar/convertir los modelos por tu cuenta.
- Si vas a usar Ollama, instala Ollama y descarga modelos compatibles (consulta la documentación de Ollama).
- Si vas a usar `llama-cpp-python`, necesitas un archivo de modelo GGML/GGUF (por ejemplo: vicuna-7b.gguf).

Qué hace la app (comportamiento)
- Si detecta la variable OLLAMA_URL (por ejemplo http://localhost:11434), intentará enviar la petición a Ollama.
- Si no hay OLLAMA_URL, intentará cargar `llama-cpp-python` y usar el modelo definido en MODEL_PATH.
- Responde con un objeto en formato OpenAI-like: {id, object, created, model, choices:[{text, index, finish_reason}], usage:...}

Siguientes pasos
1) Clona el repo
2) Configura .env con OLLAMA_URL o MODEL_PATH
3) Levanta con `docker compose up --build` o `uvicorn app.main:app --reload`

Licencia: MIT

---

Más detalles y ejemplos en el README dentro del repo.
