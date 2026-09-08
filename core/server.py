"""FastAPI webhook server with provider-agnostic ingestion."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from providers.registry import ProviderRegistry
from core.extractor import parse_message
from core.listener import MessageHandler
from core.database import init_db, insert_message, is_duplicate
import json
import os

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="NexusSMS", version="1.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

config_path = os.environ.get("NEXUSSMS_CONFIG", "config.json")
if not os.path.exists(config_path):
    raise RuntimeError(f"Configuration file not found: {config_path}")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

init_db()

registry = ProviderRegistry(config.get("providers", {}))
handler = MessageHandler(db_path=os.environ.get("NEXUSSMS_DB", "nexus_sms.db"))


@app.post("/webhook/{provider_name}")
@limiter.limit("60/minute")
async def receive_webhook(provider_name: str, request: Request):
    try:
        provider = registry.get(provider_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    body = await request.body()
    headers = dict(request.headers)

    secret = config.get("providers", {}).get(provider_name, {}).get("secret", "")
    if not provider.validate_webhook(headers, body, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    content_type = headers.get("content-type", "")
    if "application/json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    msg_id = provider.get_message_id(payload)
    if is_duplicate(provider_name, msg_id):
        return {"status": "duplicate"}

    unified = provider.parse_payload(payload)
    result = parse_message(unified.sender, unified.body)

    inserted = insert_message(
        provider=unified.provider,
        provider_message_id=unified.provider_message_id,
        sender=unified.sender,
        recipient=unified.recipient,
        category=result.category,
        extracted_code=result.extracted_code,
        raw_body=unified.body,
        raw_payload=unified.raw_payload
    )

    if inserted:
        handler.notify(result, inserted=True)

    return {"status": "ok", "provider": provider_name}


@app.get("/messages")
async def query_messages(
    sender: str = None,
    provider: str = None,
    category: str = None,
    limit: int = 20
):
    from core.database import get_messages
    return get_messages(sender=sender, provider=provider, category=category, limit=limit)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.1.0"}
