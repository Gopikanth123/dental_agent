# import base64
# import json
# import logging
# import asyncio
# import io
# import sys
# import os
# # import edge_tts  # Free TTS
# from openai import AsyncOpenAI
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from contextlib import asynccontextmanager

# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

# from config import config
# from agent.graph import create_agent_graph

# # Logging
# logging.basicConfig(level=config.LOG_LEVEL)
# logger = logging.getLogger("BrightSmile")

# aclient = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

# # Global instances
# agent_workflow = None

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Lifespan Manager:
#     1. Starts the MCP Tool Server as a subprocess.
#     2. Connects the LangGraph Agent to it.
#     """
#     global agent_workflow
#     logger.info("🚀 Starting BrightSmile Agent...")

#     # Define the command to run the MCP server script
#     # We run it as a module or script. Here we point to the file directly.
#     server_script = os.path.join("mcp_server", "run.py")
    
#     server_params = StdioServerParameters(
#         command=sys.executable, # Uses the same python interpreter as the main app
#         args=[server_script],
#         env=os.environ.copy() # Pass env vars (API keys) to subprocess
#     )

#     try:
#         # Start the MCP Client connection
#         async with stdio_client(server_params) as (read, write):
#             async with ClientSession(read, write) as session:
#                 # Initialize the session
#                 await session.initialize()
                
#                 # Load tools from the connected session into our Agent Graph
#                 agent_workflow = await create_agent_graph(session)
                
#                 logger.info("✅ MCP Client connected to Tool Server.")
#                 yield
                
#     except Exception as e:
#         logger.error(f"❌ Failed to start MCP Server: {e}")
#         raise e
#     finally:
#         logger.info("🛑 Shutting down.")

# app = FastAPI(lifespan=lifespan)
# templates = Jinja2Templates(directory="templates")

# # --- Helper: Text to Speech (Free Edge TTS) ---
# # async def synthesize_speech(text: str) -> str:
# #     """Synthesizes speech using Microsoft Edge's Free Neural TTS."""
# #     try:
# #         communicate = edge_tts.Communicate(text, "en-US-AvaNeural")
# #         mp3_fp = io.BytesIO()
# #         async for chunk in communicate.stream():
# #             if chunk["type"] == "audio":
# #                 mp3_fp.write(chunk["data"])
# #         mp3_fp.seek(0)
# #         return base64.b64encode(mp3_fp.read()).decode('utf-8')
# #     except Exception as e:
# #         logger.error(f"EdgeTTS Error: {e}")
# #         return ""

# async def synthesize_speech(text: str) -> str:
#     """Synthesizes speech using OpenAI's TTS API."""
#     try:
#         response = await aclient.audio.speech.create(
#             model=config.OPENAI_TTS_MODEL,
#             voice=config.OPENAI_TTS_VOICE,
#             input=text
#         )
        
#         # Get binary data
#         audio_content = response.content
        
#         # Convert to Base64 for the browser
#         return base64.b64encode(audio_content).decode('utf-8')
#     except Exception as e:
#         logger.error(f"OpenAI TTS Error: {e}")
#         return ""

# # --- Routes ---

# @app.get("/", response_class=HTMLResponse)
# async def get_page(request: Request):
#     return templates.TemplateResponse("voice_chat.html", {"request": request})

# @app.websocket("/ws/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: str):
#     await websocket.accept()
    
#     config_graph = {"configurable": {"thread_id": client_id}}
    
#     try:
#         # Initial Greeting
#         start_result = await agent_workflow.ainvoke(
#             {"messages": [{"role": "user", "content": "The call has started. Greet me."}], "patient_id": None},
#             config=config_graph
#         )
#         initial_text = start_result["messages"][-1].content
#         await send_audio(websocket, initial_text)

#         while True:
#             data = await websocket.receive_text()
#             logger.info(f"User: {data}")

#             result = await agent_workflow.ainvoke(
#                 {"messages": [{"role": "user", "content": data}]}, 
#                 config=config_graph
#             )
            
#             ai_text = result["messages"][-1].content
#             await send_audio(websocket, ai_text)

#     except WebSocketDisconnect:
#         logger.info(f"Client {client_id} disconnected")
#     except Exception as e:
#         logger.error(f"WebSocket Error: {e}")

# async def send_audio(ws: WebSocket, text: str):
#     b64_audio = await synthesize_speech(text)
#     if b64_audio:
#         await ws.send_text(json.dumps({"text": text, "audio": b64_audio}))

# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
import base64
import json
import logging
import asyncio
import io
import sys
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

# MCP & LangChain Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# OpenAI Import
from openai import AsyncOpenAI

from config import config
from agent.graph import create_agent_graph

# Logging Setup
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger("BrightSmile")

# Global instances
agent_workflow = None

# Initialize OpenAI Async Client for TTS
# Ensure OPENAI_API_KEY is in your .env file
aclient = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan Manager:
    1. Starts the MCP Tool Server as a subprocess.
    2. Connects the LangGraph Agent to it.
    """
    global agent_workflow
    logger.info("🚀 Starting BrightSmile Agent...")

    # Define the command to run the MCP server script
    server_script = os.path.join("mcp_server", "run.py")
    
    # Use the same python interpreter as the main app
    server_params = StdioServerParameters(
        command=sys.executable, 
        args=[server_script],
        env=os.environ.copy() # Pass env vars (API keys) to subprocess
    )

    try:
        # Start the MCP Client connection
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # Load tools from the connected session into our Agent Graph
                agent_workflow = await create_agent_graph(session)
                
                logger.info("✅ MCP Client connected to Tool Server.")
                yield
                
    except Exception as e:
        logger.error(f"❌ Failed to start MCP Server: {e}")
        raise e
    finally:
        logger.info("🛑 Shutting down.")

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# --- Helper: Text to Speech (OpenAI TTS) ---
async def synthesize_speech(text: str) -> str:
    """Synthesizes speech using OpenAI's TTS API."""
    try:
        # Call OpenAI Audio API
        response = await aclient.audio.speech.create(
            model=config.OPENAI_TTS_MODEL,
            voice=config.OPENAI_TTS_VOICE,
            input=text
        )
        
        # Get binary audio content
        audio_content = response.content
        
        # Convert to Base64 for transmission to browser
        return base64.b64encode(audio_content).decode('utf-8')
    except Exception as e:
        logger.error(f"OpenAI TTS Error: {e}")
        return ""

# --- Routes ---

@app.head("/")
async def health_check():
    """
    Responds to Render's health checks (HEAD requests).
    This prevents the '405 Method Not Allowed' errors in logs.
    """
    return Response(status_code=200)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Prevents 404 logs for favicon requests."""
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def get_page(request: Request):
    """Serves the Voice Chat Interface."""
    return templates.TemplateResponse("voice_chat.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Handles Real-time Audio/Text WebSocket connection.
    """
    await websocket.accept()
    
    # LangGraph Thread Configuration
    config_graph = {"configurable": {"thread_id": client_id}}
    
    try:
        # 1. Trigger Initial Greeting
        # The prompt in agent/prompts.py determines the actual text ("Welcome to BrightSmile...")
        start_result = await agent_workflow.ainvoke(
            {"messages": [{"role": "user", "content": "The call has started. Greet me."}], "patient_id": None},
            config=config_graph
        )
        
        # Get the AI's response text
        initial_text = start_result["messages"][-1].content
        
        # Send Audio to client
        await send_audio(websocket, initial_text)

        # 2. Main Chat Loop
        while True:
            # Receive text (transcript) from browser
            data = await websocket.receive_text()
            logger.info(f"User ({client_id}): {data}")

            # Invoke Agent
            result = await agent_workflow.ainvoke(
                {"messages": [{"role": "user", "content": data}]}, 
                config=config_graph
            )
            
            # Get AI Response
            ai_text = result["messages"][-1].content
            
            # Send Audio back
            await send_audio(websocket, ai_text)

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")

async def send_audio(ws: WebSocket, text: str):
    """Helper to synthesize audio and send JSON to WebSocket."""
    if not text:
        return

    b64_audio = await synthesize_speech(text)
    if b64_audio:
        await ws.send_text(json.dumps({"text": text, "audio": b64_audio}))

if __name__ == "__main__":
    import uvicorn
    # 1. Get PORT from Environment (Render sets this dynamically)
    # 2. Default to 8000 for local testing
    port = int(os.environ.get("PORT", 8000))
    
    # 3. Run Uvicorn
    # reload=False is recommended for production/deployments
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
