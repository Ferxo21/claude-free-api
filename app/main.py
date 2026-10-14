from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os
import time
import json
import httpx
from typing import List, Optional, Any, Dict
from starlette.concurrency import run_in_threadpool

app = FastAPI(title="Claude-free-API (OpenAI-compatible proxy)")

OLLAMA_URL = os.getenv("OLLAMA_URL")
MODEL_PATH = os.getenv("MODEL_PATH")
REPORT_MODEL_NAME = os.getenv("REPORT_MODEL_NAME", "claude-free-local")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "512"))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

@app.get("/health")
async def health():
    return {"status": "ok", "ollama": bool(OLLAMA_URL), "model_path": bool(MODEL_PATH)}

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    model_name = req.model or REPORT_MODEL_NAME
    prompt = messages_to_prompt(req.messages)
    max_tokens = req.max_tokens or DEFAULT_MAX_TOKENS
    temperature = req.temperature if req.temperature is not None else DEFAULT_TEMPERATURE

    # Try Ollama first (if configured)
    if OLLAMA_URL:
        try:
            return await generate_with_ollama(OLLAMA_URL, model_name, prompt, max_tokens, temperature)
        except Exception as e:
            # fallthrough to llama-cpp if available
            print("Ollama generate failed:", e)

    # Try llama-cpp-python local generation
    if MODEL_PATH:
        try:
            result = await run_in_threadpool(generate_with_llama_cpp, MODEL_PATH, prompt, max_tokens, temperature)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Local generation failed: {e}")

    raise HTTPException(status_code=400, detail="No backend configured. Set OLLAMA_URL or MODEL_PATH in env.")


@app.post("/v1/completions")
async def completions(req: Request):
    # Accept older completion-style requests and transform to chat format
    body = await req.json()
    # Try to build a simple prompt from body.get('prompt') or messages
    if "messages" in body:
        messages = body["messages"]
        chat_req = ChatRequest(messages=[Message(**m) for m in messages], model=body.get("model"))
    else:
        prompt_text = None
        if isinstance(body.get("prompt"), list):
            prompt_text = "\n".join(body.get("prompt"))
        else:
            prompt_text = body.get("prompt") or ""
        chat_req = ChatRequest(messages=[Message(role="user", content=prompt_text)], model=body.get("model"))
    return await chat_completions(chat_req)


def messages_to_prompt(messages: List[Message]) -> str:
    # Simple concatenation: system -> assistant -> user etc.
    parts = []
    for m in messages:
        role = m.role
        content = m.content
        parts.append(f"[{role}] {content}")
    return "\n".join(parts)


async def generate_with_ollama(ollama_url: str, model: str, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    """
    Envía la petición a Ollama. El endpoint exacto puede variar según la versión de Ollama; aquí usamos `/api/generate`.
    Si tu Ollama usa otro endpoint o autenticación, ajusta OLLAMA_URL en .env a la URL completa.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Nota: algunos despliegues de Ollama usan /api/generate o /api/call; ajusta si es necesario.
        resp = await client.post(f"{ollama_url}/api/generate", json=payload)
        if resp.status_code != 200:
            raise Exception(f"Ollama returned {resp.status_code}: {resp.text}")
        data = resp.json()

    # Mapear respuesta de Ollama a formato OpenAI-like si es necesario
    # Intentamos soportar respuestas en {'output': '...'} o {'choices': ...}
    text = None
    if isinstance(data, dict):
        if "output" in data:
            text = data.get("output")
        elif "text" in data:
            text = data.get("text")
        elif "choices" in data and len(data["choices"])>0:
            c = data["choices"][0]
            text = c.get("text") or c.get("content") or json.dumps(c)
    else:
        text = str(data)

    res = {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}
        ],
        "usage": None,
    }
    return res


def generate_with_llama_cpp(model_path: str, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    try:
        from llama_cpp import Llama
    except Exception as e:
        raise RuntimeError("llama-cpp-python no está instalado o no es importable. Instala llama-cpp-python y dependencias nativas.")

    # Carga el modelo (se crea una nueva instancia por petición; para producción cachear la instancia)
    llm = Llama(model_path=model_path)
    # Ajusta parámetros según llama-cpp-python
    resp = llm.create(prompt=prompt, max_tokens=max_tokens, temperature=temperature)

    # resp suele contener 'choices' con 'text'
    text = ""
    choices = resp.get("choices")
    if choices and len(choices) > 0:
        text = choices[0].get("text") or ""
    else:
        # fallback: puede haber 'text' en raíz
        text = resp.get("text") or str(resp)

    result = {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": os.path.basename(model_path),
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}
        ],
        "usage": None,
    }
    return result
