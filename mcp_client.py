import asyncio
import httpx
from fastmcp import FastMCP
import json

api_client = httpx.AsyncClient(base_url="http://127.0.0.1:8002")

async def main():
    # 1. Load OpenAPI spec from running FastAPI app
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get("http://127.0.0.1:8002/openapi.json")
        resp.raise_for_status()
        spec = resp.json()

    # 2. Create HTTPX tool client
    raw_client = httpx.AsyncClient(base_url="http://127.0.0.1:8002")
    # 3. Create MCP server
    mcp = FastMCP.from_openapi(openapi_spec=spec, client=api_client)

    # 4. Run MCP server
    await mcp.run_async(
        transport="http",
        host="127.0.0.1",
        port=8000
    )

if __name__ == "__main__":
    asyncio.run(main())
