"""
WebSocket Event Handlers
Handles different types of WebSocket events and messages
"""
import json
from datetime import datetime
from typing import Any, Dict

from fastapi import WebSocket

from app.container import Container
from app.core.logging import StructuredLogger
from app.websocket.manager import WebSocketManager

logger = StructuredLogger("websocket_handlers")

async def register_websocket_handlers(
    websocket: WebSocket,
    manager: WebSocketManager,
    container: Container,
    tenant_context: Any,
    current_user: Dict[str, Any],
):
    """Register all WebSocket event handlers and start message loop"""
    organization_id = tenant_context.organization_id
    authenticated_user_id = current_user["user_id"]

    def user_room(user_id: str) -> str:
        return f"tenant:{organization_id}:user:{user_id}"

    def conversation_room(conversation_id: str) -> str:
        return f"tenant:{organization_id}:conversation:{conversation_id}"
    
    # Get services
    chat_service = await container.get_service("chat_orchestrator")
    user_service = await container.get_service("user_service")
    product_service = await container.get_service("search_orchestrator")
    conversation_service = await container.get_service("conversation_orchestrator")
    redis_service = await container.get_service("redis")
    
    # Register event handlers
    async def handle_user_auth(websocket: WebSocket, data: Dict[str, Any]):
        """Handle user authentication"""
        try:
            user_id = authenticated_user_id
            user_name = current_user.get("name", f"User_{user_id}")
            language = data.get("language", "en")
            
            if user_id:
                # Set user ID for connection
                # Join user's personal room
                manager.join_room(websocket, user_room(user_id))
                
                await manager.send_message(websocket, {
                    "event": "auth_success",
                    "data": {
                        "user_id": user_id,
                        "user_name": user_name,
                        "status": "authenticated",
                        "features_enabled": True
                    }
                })
                
                logger.log_websocket_event("user_authenticated", user_id)
            else:
                await manager.send_error(websocket, "User ID is required")
                
        except Exception as e:
            logger.log_error(e, {"event": "user_auth"})
            await manager.send_error(websocket, "Authentication failed")
    
    async def handle_join_conversation(websocket: WebSocket, data: Dict[str, Any]):
        """Handle joining a conversation room"""
        try:
            user_id = authenticated_user_id
            conversation_id = data.get("conversation_id")
            
            if conversation_id:
                history = await conversation_service.get_conversation_history(
                    organization_id, conversation_id, user_id, limit=100
                )
                if not history.get("success"):
                    await manager.send_error(websocket, "Conversation not found or access denied")
                    return

                room_name = conversation_room(conversation_id)
                manager.join_room(websocket, room_name)
                
                await manager.send_message(websocket, {
                    "event": "conversation_joined",
                    "data": {
                        "conversation_id": conversation_id,
                        "room": room_name,
                        "cached": True
                    }
                })
                
                # Notify others in the conversation
                await manager.broadcast_to_room(room_name, {
                    "event": "user_joined",
                    "data": {
                        "user_id": user_id,
                        "user_name": data.get("user_name", user_id),
                        "timestamp": datetime.now().isoformat()
                    }
                }, exclude=websocket)
                
        except Exception as e:
            logger.log_error(e, {"event": "join_conversation"})
            await manager.send_error(websocket, "Failed to join conversation")
    
    async def handle_chat_message(websocket: WebSocket, data: Dict[str, Any]):
        """Handle chat messages with full feature support"""
        try:
            message = data.get("message", "").strip()
            user_id = authenticated_user_id
            conversation_id = data.get("conversation_id")
            message_type = data.get("type", "text")
            image_data = data.get("image_data") if message_type == "image" else None
            
            if not message and message_type == "text":
                await manager.send_error(websocket, "Message is required")
                return
            
            if not user_id:
                await manager.send_error(websocket, "User ID is required")
                return
            
            # Generate message ID
            message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
            
            # Send typing indicator
            if conversation_id:
                await manager.broadcast_to_room(conversation_room(conversation_id), {
                    "event": "typing_indicator",
                    "data": {
                        "user_id": "assistant",
                        "typing": True,
                        "conversation_id": conversation_id
                    }
                })
            
            # Process chat message
            chat_result = await chat_service.process_chat_message(
                user_id=user_id,
                message=message,
                conversation_id=conversation_id,
                message_type=message_type,
                image_data=image_data,
                tenant_context=tenant_context,
            )
            
            # Stop typing indicator
            if conversation_id:
                await manager.broadcast_to_room(conversation_room(conversation_id), {
                    "event": "typing_indicator",
                    "data": {
                        "user_id": "assistant",
                        "typing": False,
                        "conversation_id": conversation_id
                    }
                })
            
            # Send response
            response_payload = {
                "event": "chat_response",
                "data": {
                    "success": chat_result.get("success", True),
                    "message": chat_result.get("response", ""),
                    "message_id": chat_result.get("assistant_message_id"),
                    "user_id": user_id,
                    "conversation_id": chat_result.get("conversation_id"),
                    "personalization_reason": chat_result.get("personalization_reason", ""),
                    "cache_stats": {
                        "redis_available": await redis_service.is_available() if redis_service else False,
                        "conversation_cached": True,
                        "context_cached": chat_result.get("context_cached", False)
                    },
                    "features_used": {
                        "real_time": True,
                        "caching": True,
                        "personalization": bool(chat_result.get("personalization_reason")),
                        "status_tracking": True,
                        "shared_service": True
                    }
                }
            }
            
            await manager.send_message(websocket, response_payload)
            
            # Notify conversation room
            if chat_result.get("conversation_id"):
                await manager.broadcast_to_room(conversation_room(chat_result.get('conversation_id')), {
                    "event": "new_message",
                    "data": {
                        "from": "assistant",
                        "message": chat_result.get("response", ""),
                        "conversation_id": chat_result.get("conversation_id"),
                        "timestamp": datetime.now().isoformat()
                    }
                }, exclude=websocket)
            
            logger.log_websocket_event("chat_message_processed", user_id)
            
        except Exception as e:
            logger.log_error(e, {"event": "chat_message"})
            await manager.send_error(websocket, "Chat message processing failed")
    
    async def handle_product_search(websocket: WebSocket, data: Dict[str, Any]):
        """Handle product search via WebSocket"""
        try:
            query = data.get("query", "").strip()
            limit = data.get("limit", 10)
            rerank = data.get("rerank", True)
            user_id = authenticated_user_id
            
            if not query:
                await manager.send_error(websocket, "Search query is required")
                return
            
            # Send search started event
            await manager.send_message(websocket, {
                "event": "search_started",
                "data": {
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            # Perform search
            result = await product_service.search_products(
                query, user_id=user_id, limit=limit, tenant_context=tenant_context
            )
            
            if result.get("success"):
                await manager.send_message(websocket, {
                    "event": "product_search_results",
                    "data": {
                        "success": True,
                        "query": query,
                        "products": result.get("results", []),
                        "total": result.get("total_results", 0),
                        "reranked": result.get("reranked", False),
                        "timestamp": datetime.now().isoformat()
                    }
                })
            else:
                await manager.send_error(websocket, result.get("error", "Search failed"))
                
        except Exception as e:
            logger.log_error(e, {"event": "product_search"})
            await manager.send_error(websocket, "Product search failed")
    
    async def handle_typing(websocket: WebSocket, data: Dict[str, Any]):
        """Handle typing indicators"""
        try:
            user_id = authenticated_user_id
            conversation_id = data.get("conversation_id")
            typing = data.get("typing", False)
            
            if conversation_id:
                conversation = await conversation_service.get_conversation_details(
                    organization_id, user_id, conversation_id
                )
                if not conversation.get("success"):
                    await manager.send_error(websocket, "Conversation not found or access denied")
                    return
                user_name = current_user.get("name", user_id)
                
                await manager.broadcast_to_room(conversation_room(conversation_id), {
                    "event": "typing_indicator",
                    "data": {
                        "user_id": user_id,
                        "user_name": user_name,
                        "typing": typing,
                        "conversation_id": conversation_id
                    }
                }, exclude=websocket)
                
        except Exception as e:
            logger.log_error(e, {"event": "typing"})
    
    async def handle_get_conversation_list(websocket: WebSocket, data: Dict[str, Any]):
        """Get user's conversation list"""
        try:
            user_id = authenticated_user_id
            limit = data.get("limit", 20)
            
            if not user_id:
                await manager.send_error(websocket, "User ID required")
                return
            
            # Get conversations from service
            result = await conversation_service.get_user_conversations(organization_id, user_id, limit)
            
            if result.get("success"):
                await manager.send_message(websocket, {
                    "event": "conversation_list",
                    "data": result
                })
            else:
                await manager.send_message(websocket, {
                    "event": "conversation_list_error",
                    "data": {
                        "error": result.get("error", "Failed to get conversations"),
                        "details": result.get("details")
                    }
                })
                
        except Exception as e:
            logger.log_error(e, {"event": "get_conversation_list"})
            await manager.send_error(websocket, "Failed to get conversations")
    
    async def handle_file_upload(websocket: WebSocket, data: Dict[str, Any]):
        """Handle file uploads via WebSocket"""
        try:
            user_id = authenticated_user_id
            file_data = data.get("file_data")
            file_name = data.get("file_name")
            file_type = data.get("file_type")
            conversation_id = data.get("conversation_id")
            message = data.get("message", f"I'm sharing a file: {file_name}")
            
            if not file_data:
                await manager.send_error(websocket, "No file data provided")
                return
            
            file_id = f"file_{int(datetime.now().timestamp())}_{user_id}"
            
            # Send upload progress
            await manager.send_message(websocket, {
                "event": "upload_progress",
                "data": {
                    "file_id": file_id,
                    "progress": 10,
                    "status": "processing"
                }
            })
            
            # Handle image files
            if file_type and file_type.startswith("image/"):
                # Use chat service for image processing
                chat_result = await chat_service.process_chat_message(
                    user_id=user_id,
                    message=message,
                    conversation_id=conversation_id,
                    message_type="image",
                    image_data=file_data,
                    tenant_context=tenant_context,
                )
                
                if chat_result.get("success"):
                    await manager.send_message(websocket, {
                        "event": "file_uploaded",
                        "data": {
                            "file_id": file_id,
                            "file_name": file_name,
                            "file_type": file_type,
                            "file_url": chat_result.get("image_url"),
                            "analysis": chat_result.get("image_analysis"),
                            "conversation_id": chat_result.get("conversation_id"),
                            "response": chat_result.get("response"),
                            "progress": 100,
                            "status": "complete"
                        }
                    })
                else:
                    await manager.send_error(websocket, "Failed to process image")
            else:
                await manager.send_error(websocket, f"File type {file_type} not supported")
                
        except Exception as e:
            logger.log_error(e, {"event": "file_upload"})
            await manager.send_error(websocket, "File upload failed")
    
    # Register all handlers
    manager.register_handler("user_auth", handle_user_auth)
    manager.register_handler("join_conversation", handle_join_conversation)
    manager.register_handler("chat_message", handle_chat_message)
    manager.register_handler("product_search", handle_product_search)
    manager.register_handler("typing", handle_typing)
    manager.register_handler("get_conversation_list", handle_get_conversation_list)
    manager.register_handler("file_upload", handle_file_upload)
    
    # Message handling loop
    try:
        while True:
            # Receive message
            message_text = await websocket.receive_text()
            
            try:
                message = json.loads(message_text)
                await manager.handle_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_error(websocket, "Invalid JSON message")
            except Exception as e:
                logger.log_error(e, {"event": "message_processing"})
                await manager.send_error(websocket, "Message processing failed")
                
    except Exception as e:
        logger.log_error(e, {"event": "websocket_loop"})
        manager.disconnect(websocket)
