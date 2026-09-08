import json
import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from providers.registry import ProviderRegistry
from core.extractor import parse_message
from core.listener import MessageHandler
from core.database import insert_message, get_messages, is_duplicate, init_db


def load_config():
    config_path = os.environ.get("NEXUSSMS_CONFIG", "config.json")
    with open(config_path) as f:
        return json.load(f)


def resolve_env_vars(obj):
    """Interpolate ${ENV_VAR} placeholders in config values."""
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_env_vars(v) for v in obj]
    if isinstance(obj, str):
        return re.sub(r'\$\{([^}]+)\}', lambda m: os.environ.get(m.group(1), m.group(0)), obj)
    return obj


config = resolve_env_vars(load_config())

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="NexusSMS",
    description="Universal OTP & Message Ingestion Engine",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

registry = ProviderRegistry(config["providers"])
handler = MessageHandler(callbacks=[])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app.router.lifespan_context = lifespan


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


@app.post("/webhook/{provider_name}")
@limiter.limit("60/minute")
async def receive_webhook(provider_name: str, request: Request):
    provider = registry.get(provider_name)
    
    content_type = request.headers.get("content-type", "")
    
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        payload = dict(form)
        validation_body = payload
    elif "application/json" in content_type:
        body_bytes = await request.body()
        payload = json.loads(body_bytes) if body_bytes else {}
        validation_body = body_bytes
    else:
        body_bytes = await request.body()
        payload = {}
        validation_body = body_bytes
    
    secret = config["providers"][provider_name].get("secret", "")
    if not provider.validate_webhook(dict(request.headers), validation_body, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    msg_id = provider.get_message_id(payload)
    if is_duplicate(provider_name, msg_id):
        return {"status": "duplicate"}
    
    unified = provider.parse_payload(payload)
    result = parse_message(unified.sender, unified.body)
    
    inserted = insert_message(unified, {
        "category": result.category,
        "extracted_code": result.extracted_code,
    })
    
    if inserted:
        handler.notify(result, inserted)
    
    return {"status": "ok", "provider": provider_name}


@app.get("/messages")
@limiter.limit("120/minute")
async def query_messages(
    sender: str = None,
    provider: str = None,
    category: str = None,
    limit: int = 20
):
    return get_messages(sender=sender, provider=provider, category=category, limit=limit)


@app.get("/health")
async def health():
    return {"status": "ok"}
