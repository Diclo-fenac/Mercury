from mcp.server.fastmcp import FastMCP
mcp = FastMCP("test")
print(type(mcp._mcp_server))
print(type(mcp._mcp_server.run))
