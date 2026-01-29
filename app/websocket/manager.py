"""
WebSocket Connection Manager
Manages WebSocket connections, rooms, and message broadcasting
"""
import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger, StructuredLogger

logger = StructuredLogger("websocket")

class ConnectionManager:
    """Manages individual WebSocket connections"""
    
    def __init__(self):
        # Active connections: {websocket: connection_info}
        self.active_connections: Dict[WebSocket, Dict[str, Any]] = {}
        
        # User connections: {user_id: {websocket, ...}}
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        
        # Room connections: {room_id: {websocket, ...}}
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        connection_info = {
            "connected_at": datetime.now(),
            "user_id": user_id,
            "rooms": set(),
            "session_id": id(websocket)  # Use object id as session id
        }
        
        self.active_connections[websocket] = connection_info
        self.connection_metadata[websocket] = {}
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        logger.log_websocket_event("connection", user_id, session_id=connection_info["session_id"])
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket not in self.active_connections:
            return
        
        connection_info = self.active_connections[websocket]
        user_id = connection_info.get("user_id")
        rooms = connection_info.get("rooms", set())
        
        # Remove from active connections
        del self.active_connections[websocket]
        
        # Remove from user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from rooms
        for room_id in rooms:
            if room_id in self.room_connections:
                self.room_connections[room_id].discard(websocket)
                if not self.room_connections[room_id]:
                    del self.room_connections[room_id]
        
        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        logger.log_websocket_event("disconnection", user_id)
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.log_error(e, {"event": "send_personal_message"})
            self.disconnect(websocket)
    
    async def send_to_user(self, message: Dict[str, Any], user_id: str):
        """Send message to all connections of a user"""
        if user_id not in self.user_connections:
            return
        
        disconnected = []
        for websocket in self.user_connections[user_id].copy():
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.log_error(e, {"event": "send_to_user", "user_id": user_id})
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_room(self, message: Dict[str, Any], room_id: str, exclude: Optional[WebSocket] = None):
        """Broadcast message to all connections in a room"""
        if room_id not in self.room_connections:
            return
        
        disconnected = []
        for websocket in self.room_connections[room_id].copy():
            if websocket == exclude:
                continue
            
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.log_error(e, {"event": "broadcast_to_room", "room_id": room_id})
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: Dict[str, Any], exclude: Optional[WebSocket] = None):
        """Broadcast message to all active connections"""
        disconnected = []
        for websocket in list(self.active_connections.keys()):
            if websocket == exclude:
                continue
            
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.log_error(e, {"event": "broadcast_to_all"})
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    def join_room(self, websocket: WebSocket, room_id: str):
        """Add connection to a room"""
        if websocket not in self.active_connections:
            return False
        
        # Add to room connections
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(websocket)
        
        # Update connection info
        self.active_connections[websocket]["rooms"].add(room_id)
        
        logger.log_websocket_event(
            "join_room", 
            self.active_connections[websocket].get("user_id"),
            room_id=room_id
        )
        return True
    
    def leave_room(self, websocket: WebSocket, room_id: str):
        """Remove connection from a room"""
        if websocket not in self.active_connections:
            return False
        
        # Remove from room connections
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(websocket)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
        
        # Update connection info
        self.active_connections[websocket]["rooms"].discard(room_id)
        
        logger.log_websocket_event(
            "leave_room",
            self.active_connections[websocket].get("user_id"),
            room_id=room_id
        )
        return True
    
    def set_user_id(self, websocket: WebSocket, user_id: str):
        """Associate user ID with WebSocket connection"""
        if websocket not in self.active_connections:
            return False
        
        # Remove from old user connections if exists
        old_user_id = self.active_connections[websocket].get("user_id")
        if old_user_id and old_user_id in self.user_connections:
            self.user_connections[old_user_id].discard(websocket)
            if not self.user_connections[old_user_id]:
                del self.user_connections[old_user_id]
        
        # Add to new user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        # Update connection info
        self.active_connections[websocket]["user_id"] = user_id
        
        logger.log_websocket_event("user_auth", user_id)
        return True
    
    def get_connection_info(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        """Get connection information"""
        return self.active_connections.get(websocket)
    
    def get_user_connections(self, user_id: str) -> Set[WebSocket]:
        """Get all connections for a user"""
        return self.user_connections.get(user_id, set())
    
    def get_room_connections(self, room_id: str) -> Set[WebSocket]:
        """Get all connections in a room"""
        return self.room_connections.get(room_id, set())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "active_rooms": len(self.room_connections),
            "connections_per_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            },
            "connections_per_room": {
                room_id: len(connections)
                for room_id, connections in self.room_connections.items()
            }
        }

class WebSocketManager:
    """High-level WebSocket manager with additional features"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.message_handlers: Dict[str, callable] = {}
        self.middleware: List[callable] = []
    
    async def connect(self, websocket: WebSocket):
        """Connect WebSocket with enhanced features"""
        await self.connection_manager.connect(websocket)
        
        # Send connection confirmation
        await self.send_message(websocket, {
            "event": "connection_response",
            "data": {
                "status": "connected",
                "message": "🛍️ Welcome to Walmart AI Assistant - FastAPI Elite Edition!",
                "session_id": id(websocket),
                "server_time": datetime.now().isoformat(),
                "features": [
                    "🔁 Real-time messaging",
                    "✍️ Typing indicators",
                    "✅ Message delivery status",
                    "💾 Smart caching",
                    "📦 File sharing",
                    "🌍 Multilingual support"
                ]
            }
        })
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect WebSocket"""
        self.connection_manager.disconnect(websocket)
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message with timestamp"""
        message["timestamp"] = datetime.now().isoformat()
        await self.connection_manager.send_personal_message(message, websocket)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to user with timestamp"""
        message["timestamp"] = datetime.now().isoformat()
        await self.connection_manager.send_to_user(message, user_id)
    
    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude: Optional[WebSocket] = None):
        """Broadcast to room with timestamp"""
        message["timestamp"] = datetime.now().isoformat()
        await self.connection_manager.broadcast_to_room(message, room_id, exclude)
    
    def register_handler(self, event_type: str, handler: callable):
        """Register message handler for event type"""
        self.message_handlers[event_type] = handler
    
    def add_middleware(self, middleware: callable):
        """Add middleware function"""
        self.middleware.append(middleware)
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            # Apply middleware
            for middleware_func in self.middleware:
                message = await middleware_func(websocket, message)
                if message is None:  # Middleware can block message
                    return
            
            # Get event type
            event_type = message.get("event")
            if not event_type:
                await self.send_error(websocket, "Missing event type")
                return
            
            # Find and execute handler
            handler = self.message_handlers.get(event_type)
            if handler:
                await handler(websocket, message.get("data", {}))
            else:
                await self.send_error(websocket, f"Unknown event type: {event_type}")
        
        except Exception as e:
            logger.log_error(e, {"event": "handle_message"})
            await self.send_error(websocket, "Message handling failed")
    
    async def send_error(self, websocket: WebSocket, error_message: str):
        """Send error message"""
        await self.send_message(websocket, {
            "event": "error",
            "data": {
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    # Delegate methods to connection manager
    def join_room(self, websocket: WebSocket, room_id: str):
        return self.connection_manager.join_room(websocket, room_id)
    
    def leave_room(self, websocket: WebSocket, room_id: str):
        return self.connection_manager.leave_room(websocket, room_id)
    
    def set_user_id(self, websocket: WebSocket, user_id: str):
        return self.connection_manager.set_user_id(websocket, user_id)
    
    def get_connection_info(self, websocket: WebSocket):
        return self.connection_manager.get_connection_info(websocket)
    
    def get_stats(self):
        return self.connection_manager.get_stats()