import base64
import json
import logging
import asyncio
import io
import sys
import os
# import edge_tts  # Free TTS
from openai import AsyncOpenAI
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import config
from agent.graph import create_agent_graph

# Logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger("BrightSmile")

aclient = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

# Global instances
agent_workflow = None

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
    # We run it as a module or script. Here we point to the file directly.
    server_script = os.path.join("mcp_server", "run.py")
    
    server_params = StdioServerParameters(
        command=sys.executable, # Uses the same python interpreter as the main app
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

# --- Helper: Text to Speech (Free Edge TTS) ---
# async def synthesize_speech(text: str) -> str:
#     """Synthesizes speech using Microsoft Edge's Free Neural TTS."""
#     try:
#         communicate = edge_tts.Communicate(text, "en-US-AvaNeural")
#         mp3_fp = io.BytesIO()
#         async for chunk in communicate.stream():
#             if chunk["type"] == "audio":
#                 mp3_fp.write(chunk["data"])
#         mp3_fp.seek(0)
#         return base64.b64encode(mp3_fp.read()).decode('utf-8')
#     except Exception as e:
#         logger.error(f"EdgeTTS Error: {e}")
#         return ""

async def synthesize_speech(text: str) -> str:
    """Synthesizes speech using OpenAI's TTS API."""
    try:
        response = await aclient.audio.speech.create(
            model=config.OPENAI_TTS_MODEL,
            voice=config.OPENAI_TTS_VOICE,
            input=text
        )
        
        # Get binary data
        audio_content = response.content
        
        # Convert to Base64 for the browser
        return base64.b64encode(audio_content).decode('utf-8')
    except Exception as e:
        logger.error(f"OpenAI TTS Error: {e}")
        return ""

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def get_page(request: Request):
    return templates.TemplateResponse("voice_chat.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    config_graph = {"configurable": {"thread_id": client_id}}
    
    try:
        # Initial Greeting
        start_result = await agent_workflow.ainvoke(
            {"messages": [{"role": "user", "content": "The call has started. Greet me."}], "patient_id": None},
            config=config_graph
        )
        initial_text = start_result["messages"][-1].content
        await send_audio(websocket, initial_text)

        while True:
            data = await websocket.receive_text()
            logger.info(f"User: {data}")

            result = await agent_workflow.ainvoke(
                {"messages": [{"role": "user", "content": data}]}, 
                config=config_graph
            )
            
            ai_text = result["messages"][-1].content
            await send_audio(websocket, ai_text)

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")

async def send_audio(ws: WebSocket, text: str):
    b64_audio = await synthesize_speech(text)
    if b64_audio:
        await ws.send_text(json.dumps({"text": text, "audio": b64_audio}))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)