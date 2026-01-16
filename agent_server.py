# # agent_sse.py

# import asyncio
# from fastapi import FastAPI, Request
# from fastapi.responses import HTMLResponse, StreamingResponse
# from fastapi.templating import Jinja2Templates

# from mcp_agent import setup_llm_gemini, create_tool_wrapper
# from fastmcp.client import Client
# from llama_index.core.agent.workflow import ReActAgent
# from llama_index.core.workflow import Context
# from llama_index.core.tools import FunctionTool

# app = FastAPI()
# templates = Jinja2Templates(directory="templates")


# @app.get("/", response_class=HTMLResponse)
# async def get_chat(request: Request):
#     return templates.TemplateResponse("chat.html", {"request": request})


# @app.get("/chat")
# async def chat(query: str):
#     async def event_stream():
#         try:
#             setup_llm_gemini()
#             client = Client("http://localhost:8000/mcp/")
#             await client.__aenter__()

#             mcp_tools = await client.list_tools()
#             li_tools = [
#                 FunctionTool.from_defaults(
#                     fn=create_tool_wrapper(client, t.name, t.inputSchema),
#                     name=t.name,
#                     description=t.description
#                 ) for t in mcp_tools
#             ]

#             agent = ReActAgent(
#                 description="HR Leave Agent",
#                 tools=li_tools,
#                 verbose=False,
#                 system_prompt="You're an HR assistant. Answer clearly and only use tools when needed."
#             )

#             ctx = Context(agent)
#             handler = agent.run(query, ctx=ctx)

#             final_response = ""
#             async for event in handler.stream_events():
#                 if hasattr(event, "delta") and event.delta:
#                     print("⏳ Event:", event.delta)
#                     if "Answer:" in event.delta:
#                         final_response = event.delta.split("Answer:")[-1].strip()
#                         print("-------------------------",final_response)


#             await client.__aexit__(None, None, None)

#             yield f"data: {final_response}\n\n"

#         except Exception as e:
#             yield f"data: ⚠️ Error: {str(e)}\n\n"

#     return StreamingResponse(event_stream(), media_type="text/event-stream")


# from fastapi import FastAPI, Request
# from pydantic import BaseModel
# from fastapi.middleware.cors import CORSMiddleware
# import asyncio
# from mcp_agent import run_agent_flow  # from your current code

# app = FastAPI()

# # Enable frontend CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class Query(BaseModel):
#     message: str

# @app.post("/ask")
# async def ask_agent(query: Query):
#     # Replace this with cleaner agent query invocation
#     response = await run_agent_flow(query.message)
#     return {"response": response}


# app.py (FastAPI Server with memory-based dynamic chaining)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
from mcp_agent import get_agent_with_context

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    user_id: str
    message: str

@app.post("/ask")
async def ask_agent(query: Query):
    agent, ctx = await get_agent_with_context(query.user_id)
    handler = agent.run(query.message, ctx=ctx)

    final_response = ""
    capture = False
    async for event in handler.stream_events():
        if hasattr(event, "delta") and event.delta:
            delta = event.delta.strip()
            print("*************************",delta)
            if "Answer:" in delta:
                capture = True
                final_response = delta.split("Answer:")[-1].strip()
                print("------------------------------",final_response)
            elif capture:
                final_response += " " + delta

    return {"response": final_response.strip()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent_server:app", host="0.0.0.0", port=8003, reload=True)
