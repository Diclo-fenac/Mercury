# Backend Summary

## Auth

Authenticated endpoints use `Authorization: Bearer <token>`. In debug mode, tokens beginning with `user_` are accepted and mapped to the remaining value as `user_id`.

Admin endpoints require a JWT containing the `admin` role.

## Endpoint Map

### Health

- `GET /api/v1/health/` returns overall service status.
- `GET /api/v1/health/ready` returns readiness for Redis and Firestore.
- `GET /api/v1/health/live` returns process liveness.

### Products

- `POST /api/v1/products/search`
  - Body: `{ query, filters, sort, pagination, user_context, search_type, include }`
  - Returns: search results, facets, metadata, optional suggestions.
- `GET /api/v1/products/search/suggestions?q=&limit=`
- `GET /api/v1/products/trending?category=&days=&page=&limit=`
- `GET /api/v1/products/deals?category=&min_discount=&page=&limit=`
- `GET /api/v1/products/flash-deals?page=&limit=`
- `GET /api/v1/products/{product_id}?user_id=`
- `GET /api/v1/products/{product_id}/recommendations?user_id=&recommendation_type=&page=&limit=`

### Users

- `GET /api/v1/users/{user_id}/profile`
- `GET /api/v1/users/{user_id}/preferences`
- `GET /api/v1/users/{user_id}/recommendations?category=&page=&limit=`

All user endpoints require auth and enforce `token user_id == path user_id`.

### Conversations

- `GET /api/v1/conversations/?user_id=&page=&limit=`
- `POST /api/v1/conversations/`
  - Body: `{ user_id?, title?, metadata? }`
- `GET /api/v1/conversations/{conversation_id}`
- `DELETE /api/v1/conversations/{conversation_id}`

### Chat

- `POST /api/v1/chat/completions`
  - Body: `{ user_id?, conversation_id?, messages, model_version?, stream?, temperature?, max_tokens?, context_config?, tools?, image_data? }`
- `POST /api/v1/chat/stream`
  - Same body, returns SSE.
- `POST /api/v1/chat/tools`
  - Body: `{ operation: "discover" | "execute", tool_name?, parameters? }`
- `GET /api/v1/chat/history/{conversation_id}?page=&limit=`

### Images

- `POST /api/v1/images/`
  - Body: `{ image_data, message?, conversation_id?, create_chat_message? }`
- `GET /api/v1/images/{image_id}`
- `POST /api/v1/images/search`
  - Body: `{ image_id?, image_data?, prompt, search_type, limit }`

### Admin Cache

- `GET /api/v1/admin/cache/stats`
- `GET /api/v1/admin/cache/health`

## Required Fixes

- Fixed `status.HTTP_53` in product search service-unavailable handling to `status.HTTP_503_SERVICE_UNAVAILABLE`.
- WebSocket event handlers are present, but no route is mounted in `main.py`. Add a `/ws` route before building a true realtime frontend.
