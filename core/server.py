from fastapi import FastAPI, Request, HTTPException, Depends
from providers.registry import ProviderRegistry
from core.extractor import parse_message
from core.listener import MessageHandler
from core.database import insert_message, get_messages, is_duplicate
import json

app = FastAPI()
config = json.loads(open("config.json").read())  # or env-based
registry = ProviderRegistry(config["providers"])
handler = MessageHandler(callbacks=[...])  # your callbacks

@app.post("/webhook/{provider_name}")
async def receive_webhook(provider_name: str, request: Request):
    provider = registry.get(provider_name)
    
    body = await request.body()
    headers = dict(request.headers)
    
    # Validate
    secret = config["providers"][provider_name].get("secret", "")
    if not provider.validate_webhook(headers, body, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    payload = await request.json() if body else {}
    
    # Deduplicate using provider-specific ID
    msg_id = provider.get_message_id(payload)
    if is_duplicate(provider_name, msg_id):
        return {"status": "duplicate"}
    
    # Normalize
    unified = provider.parse_payload(payload)
    
    # Extract codes using existing engine
    result = parse_message(unified.sender, unified.body)
    
    # Store
    inserted = insert_message(unified, result)
    
    # Notify
    if inserted:
        handler.notify(result, unified)
    
    return {"status": "ok", "provider": provider_name}

@app.get("/messages")
async def query_messages(sender: str = None, provider: str = None, limit: int = 20):
    return get_messages(sender=sender, provider=provider, limit=limit)
