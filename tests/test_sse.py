import inspect
import mcp.server.sse
import mcp.server
print(inspect.signature(mcp.server.sse.SseServerTransport))
print(inspect.signature(mcp.server.Server.run))
