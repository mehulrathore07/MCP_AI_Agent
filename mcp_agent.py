# =============================
# Step 1: Install dependencies
# =============================
# pip install fastmcp llama-index llama-index-llms-llama-cpp llama-index-llms-google-genai

import asyncio
import inspect
import os
from typing import Any, Dict

import httpx
from fastmcp.client import Client
from llama_index.core import Settings
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Context
from llama_index.core.agent.workflow import (
    ReActAgent,
    AgentStream,
    ToolCall,
    ToolCallResult,
)
# from llama_index.llms.google_genai import GoogleGenAI  # Optional cloud LLM
# from llama_index.llms.ollama import Ollama
from llama_index.llms.google import Gemini
from llama_index.core import Settings





# =========================================================
# Step 2: Choose your LLM - Local (LlamaCPP) or Gemini (optional)
# =========================================================
# def setup_llm_local():
#     model_path = "./models/Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf"  # adjust this
#     llm = LlamaCPP(
#         model_path=model_path,
#         temperature=0.0,
#         max_new_tokens=4000,
#         context_window=10096,
#         model_kwargs={"n_gpu_layers": 16},
#         verbose=False
#     )
#     Settings.llm = llm

def setup_llm_gemini():
    API_KEY = "AIzaSyBKidii6NfzRR4fJKFloLSdu0mcN01LUTM"
    # print(";;;===================",API_KEY)
    llm = Gemini(
        model="gemini-2.5-flash-preview-05-20",
        api_key=API_KEY
    )
    Settings.llm = llm
    Settings.chunk_size = 512

# def setup_llm_local():
#     llm = Ollama(
#             model="deepseek-r1:1.5b",
#             request_timeout=60,
#             temperature=0.7,
#             max_tokens=1024 
#     )
#     Settings.llm = llm


# =========================================================
# Step 3: Tool Wrapper from MCP tool schema
# =========================================================
def create_tool_wrapper(mcp_client: Any, tool_name: str, input_schema: Dict[str, Any]):
    params = input_schema.get("properties", {})
    required = set(input_schema.get("required", []))
    sig_params = []

    for name, spec in params.items():
        annotation = str
        if spec.get("type") == "integer":
            annotation = int
        elif spec.get("type") == "number":
            annotation = float
        elif spec.get("type") == "boolean":
            annotation = bool

        default = inspect.Parameter.empty if name in required else None
        param = inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=default, annotation=annotation)
        if name in required:
            sig_params.insert(0, param)
        else:
            sig_params.append(param)

    sig = inspect.Signature(parameters=sig_params)

    async def _tool_func_template(**kwargs):
        try:
            filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
            result = await mcp_client.call_tool(tool_name, filtered_kwargs)
            
            # ✅ Correctly extract the actual tool response
            if hasattr(result, "return_value"):
                return str(result.return_value)
            else:
                return str(result)

        except Exception as e:
            return f"❌ Tool call error: {e}"

    _tool_func_template.__signature__ = sig
    _tool_func_template.__name__ = tool_name
    return _tool_func_template



# =========================================================
# Step 4: Agent runner (verbose stream)
# =========================================================
async def run_agent_verbose(agent, ctx, query):
    handler = agent.run(query, ctx=ctx)
    async for event in handler.stream_events():
        if isinstance(event, ToolCallResult):
            print(f"\n\n-----------\nTool execution result:\n{event.tool_output}")
        elif isinstance(event, ToolCall):
            print(f"\n\n-----------\nGenerated args from LLM:\n{event.tool_kwargs}")
        elif isinstance(event, AgentStream):
            print(event.delta, end="", flush=True)
    return await handler


# =========================================================
# Step 5: Main entrypoint
# =========================================================
# async def main():
#     setup_llm_gemini() 
#     mcp_url = "http://localhost:8000/mcp/"
#     client = Client(mcp_url)

#     async with client:
#         mcp_tools = await client.list_tools()
#         li_tools = []

#         for tool in mcp_tools:
#             wrapper_fn = create_tool_wrapper(client, tool.name, tool.inputSchema)
#             llamaindex_tool = FunctionTool.from_defaults(
#                 fn=wrapper_fn,
#                 name=tool.name,
#                 description=tool.description,
#             )
#             li_tools.append(llamaindex_tool)

#         # Build the agent
#         lib_agent = ReActAgent(
#             description="Useful for making API calls to query the MCP toolset.",
#             tools=li_tools,
#             system_prompt = """
#                 You are a helpful HR assistant. You can:
#                 - Apply, delete, or approve leave
#                 - Check leave balance
#                 - Update leave information
#                 Respond precisely and only use tools when needed.
#                 """,
#             verbose=True
#         )

#         ctx = Context(lib_agent)
#         user_query = "Apply leave for Sohan from 5 aug 2025 to 11 aug 2025"
#         # user_query = "get all the details of employees"
#         # user_query = "get all the leaves requested by Sumit"
#         # user_query = "Approve the leave of Mohan"
#         response = await run_agent_verbose(lib_agent, ctx, user_query)
#         print("\nFinal response:\n", response)


# async def run_agent_flow(user_query: str) -> str:
#     setup_llm_gemini()  # Configure Gemini / LLM

#     mcp_url = "http://localhost:8000/mcp/"
#     client = Client(mcp_url)

#     async with client:
#         mcp_tools = await client.list_tools()

#         li_tools = [
#             FunctionTool.from_defaults(
#                 fn=create_tool_wrapper(client, tool.name, tool.inputSchema),
#                 name=tool.name,
#                 description=tool.description
#             )
#             for tool in mcp_tools
#         ]

#         agent = ReActAgent(
#             description="Useful for making API calls to query the MCP toolset.",
#             tools=li_tools,
#             system_prompt="""
#                 You are a helpful HR assistant. You can:
#                 - Apply, delete, or approve leave
#                 - Check leave balance
#                 - Update leave information
#                 Respond precisely and only use tools when needed.
#             """,
#             verbose=False,
#         )

#         ctx = Context(agent)
#         handler = agent.run(user_query, ctx=ctx)

#         final_response = ""
#         start = False
#         async for event in handler.stream_events():
#             if hasattr(event, "delta") and event.delta:
#                 if "Answer:" in event.delta:
#                     final_response += event.delta.split("Answer:")[-1].strip()
#                     print(final_response)
#                     start = True
#                 elif start:
#                     final_response += event.delta
#                     print("------------,",final_response)

#         return final_response.strip()


# from llama_index.core.agent import ReActAgent

# Global session context store
memory_store = {}

async def get_agent_with_context(user_id: str):

    # Setup
    setup_llm_gemini()
    client = Client("http://localhost:8000/mcp/")
    await client.__aenter__()

    async with client:
        mcp_tools = await client.list_tools()

        li_tools = [
            FunctionTool.from_defaults(
                fn=create_tool_wrapper(client, tool.name, tool.inputSchema),
                name=tool.name,
                description=tool.description
            )
            for tool in mcp_tools
        ]

    agent = ReActAgent(
        description="HR Assistant",
        tools=li_tools,
        system_prompt="""
                You are a helpful HR assistant. You can:
                - Apply, delete, or approve leave
                - Check leave balance
                - Update leave information
                - Respond precisely and only use tools when needed.
            """,
        verbose=False
    )

# Retrieve or create memory context per user
    ctx = memory_store.get(user_id)
    if ctx is None:
        ctx = Context(agent)
        memory_store[user_id] = ctx

    return agent, ctx
