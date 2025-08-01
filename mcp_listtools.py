# mcp_test_client.py
from fastmcp.client import Client
import asyncio
                                                                                                                                       
mcp_url = "http://localhost:8000/mcp/"
client = Client(mcp_url)

async def main():
    # Connection is established here
    async with client:
       mcp_tools = await client.list_tools()
       for i,tool in enumerate(mcp_tools):
           print(f'Tool {i}: {tool.name}\n\t{tool.inputSchema}')
        
    # Connection is closed automatically here

if __name__ == "__main__":
    asyncio.run(main())