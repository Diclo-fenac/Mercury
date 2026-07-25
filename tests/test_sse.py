import inspect

import mcp.server
import mcp.server.sse

print(inspect.signature(mcp.server.sse.SseServerTransport))
print(inspect.signature(mcp.server.Server.run))
