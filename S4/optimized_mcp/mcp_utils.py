from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from contextlib import asynccontextmanager
from config import Config

class MCPConnectionPool:
    def __init__(self):
        self._pool = []
        self._lock = asyncio.Lock()
        
    @asynccontextmanager
    async def get_session(self):
        async with self._lock:
            if self._pool:
                session = self._pool.pop()
                try:
                    # Verify session is still alive
                    await session.list_tools()
                    yield session
                    self._pool.append(session)
                    return
                except:
                    # If verification fails, create new session
                    pass

        # Create new connection
        async with stdio_client(
            StdioServerParameters(
                command="python",
                args=[Config.MCP_SERVER_PATH]
            )
        ) as (read, write):
            session = ClientSession(read, write)
            await session.initialize()
            try:
                yield session
            finally:
                async with self._lock:
                    self._pool.append(session)

# Global connection pool
pool = MCPConnectionPool()

async def call_tool_with_retry(tool_name, arguments, max_retries=3):
    for attempt in range(max_retries):
        try:
            async with pool.get_session() as session:
                return await session.call_tool(tool_name, arguments=arguments)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(0.2 * (attempt + 1))