import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.container import get_container
from app.domain.tenants.service import TenantService

logger = logging.getLogger("websocket_dashboard")
router = APIRouter()

@router.websocket("/dashboard")
async def dashboard_websocket_endpoint(websocket: WebSocket):
    # 1. Provisional acceptance
    await websocket.accept()
    
    client_ip = websocket.client.host if websocket.client else "unknown"
    from app.api.dependencies import check_rate_limit
    container = get_container()
    redis_client = container.get("redis")
    
    if not await check_rate_limit(f"ws:{client_ip}", limit=1000, window=60, cache=redis_client):
        await websocket.close(code=1008, reason="Too many connection attempts")
        return
    
    tenant_service: TenantService = container.get("tenant_service")
    
    org_id = None
    authenticated = False
    subscriptions = set()
    pubsub = None
    
    # 2. Wait for auth event with 3-second deadline
    try:
        auth_message_str = await asyncio.wait_for(websocket.receive_text(), timeout=3.0)
        auth_message = json.loads(auth_message_str)
        
        if auth_message.get("event") != "auth" or not auth_message.get("token"):
            await websocket.close(code=1008, reason="Expected auth event")
            return
            
        token = auth_message["token"]
        # In a real app, this would validate a short-lived scoped token.
        # Here we use the API key validation but ensure it has admin scopes.
        ctx = await tenant_service.validate_api_key(token)
        if not ctx or not any(s in ctx.get("scopes", []) for s in ("admin", "all", "*")):
            await websocket.close(code=1008, reason="Invalid token or missing admin scope")
            return
            
        org_id = ctx["organization_id"]
        authenticated = True
        await websocket.send_json({"event": "auth:ok"})
        
    except asyncio.TimeoutError:
        await websocket.close(code=1008, reason="Auth timeout")
        return
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        await websocket.close(code=1008, reason="Auth failure")
        return

    # 3. Setup Redis PubSub listener for this connection
    async def redis_listener():
        nonlocal pubsub
        try:
            pubsub = redis_client.redis.pubsub()
            # Subscribe to a dummy channel first so it's active
            await pubsub.subscribe(f"mercury:{org_id}:system")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode('utf-8')
                    topic = channel.split(":")[-1]
                    if topic in subscriptions:
                        try:
                            payload = json.loads(message["data"])
                            if websocket.client_state == WebSocketState.CONNECTED:
                                await websocket.send_json(payload)
                        except Exception as e:
                            logger.error(f"Error forwarding pubsub message: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
        finally:
            if pubsub:
                await pubsub.unsubscribe()
                await pubsub.close()

    listener_task = asyncio.create_task(redis_listener())

    # 4. Message loop for subscribe/unsubscribe/ping
    try:
        while True:
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            event = data.get("event")
            
            if event == "ping":
                await websocket.send_json({"event": "pong"})
            
            elif event == "subscribe":
                topics = data.get("topics", [])
                for topic in topics:
                    if topic in ["ingestion", "jobs", "errors", "metrics", "search"]:
                        subscriptions.add(topic)
                        if pubsub:
                            await pubsub.subscribe(f"mercury:{org_id}:{topic}")
                            
            elif event == "unsubscribe":
                topics = data.get("topics", [])
                for topic in topics:
                    if topic in subscriptions:
                        subscriptions.remove(topic)
                        if pubsub:
                            await pubsub.unsubscribe(f"mercury:{org_id}:{topic}")
                            
    except WebSocketDisconnect:
        logger.info(f"Dashboard websocket disconnected for org {org_id}")
    except Exception as e:
        logger.error(f"Dashboard websocket error: {e}")
    finally:
        listener_task.cancel()
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close()
