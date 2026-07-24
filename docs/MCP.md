# Mercury Model Context Protocol (MCP)

Mercury provides an MCP server to allow AI agents and LLM clients to securely read catalog data, perform semantic search, and get recommendations on behalf of a tenant.

## Authentication

All MCP endpoints require authentication. You can authenticate using:
- **API Key**: Pass the `X-API-Key` header with a valid tenant API key.
- **OIDC Token**: Pass an OIDC token in the `Authorization: Bearer <token>` header. The token must be signed by the trusted issuer configured in `MCP_OIDC_ISSUER`.

## Endpoints

- **SSE Connection**: `GET /api/v1/mcp/sse`
- **Messages**: `POST /api/v1/mcp/messages?sessionId=<id>`

## Available Tools (Read-Only)

1. `search_products(query: str, limit: int = 10, page: int = 1)`: Semantic/keyword product search.
2. `search_documents(query: str, limit: int = 10, page: int = 1)`: Document search.
3. `autocomplete(query: str, limit: int = 5)`: Search query suggestions.
4. `get_product(product_id: str)`: Retrieve specific product details.
5. `get_collections()`: Get all collection facets.
6. `get_categories()`: Get all category facets.
7. `find_similar_products(product_id: str, limit: int = 5)`: Semantic similarity.
8. `recommend_products(user_id: str, limit: int = 5)`: Personalized recommendations.
9. `chat_catalog(message: str, user_id: str, conversation_id: str = None)`: Grounded AI chat.

## Tenant Isolation

Every tool execution is strictly scoped to the tenant associated with the provided API Key or OIDC token. Cross-tenant reads are structurally impossible because the collection name and database row-level filters are enforced by the `TenantContext`.

## Client Example

To use with a standard MCP client (e.g., Anthropic Claude Desktop or a custom client), configure it to connect via SSE to `https://<mercury-domain>/api/v1/mcp/sse` and provide the appropriate headers.
