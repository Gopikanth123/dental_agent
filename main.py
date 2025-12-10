# # # import base64
# # # import json
# # # import logging
# # # import asyncio
# # # import io
# # # import sys
# # # import os
# # # from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
# # # from fastapi.responses import HTMLResponse
# # # from fastapi.templating import Jinja2Templates
# # # from contextlib import asynccontextmanager

# # # # MCP & LangChain Imports
# # # from mcp import ClientSession, StdioServerParameters
# # # from mcp.client.stdio import stdio_client

# # # # OpenAI Import
# # # from openai import AsyncOpenAI

# # # from config import config
# # # from agent.graph import create_agent_graph

# # # # Logging Setup
# # # logging.basicConfig(level=config.LOG_LEVEL)
# # # logger = logging.getLogger("BrightSmile")

# # # # Global instances
# # # agent_workflow = None

# # # # Initialize OpenAI Async Client for TTS
# # # # Ensure OPENAI_API_KEY is in your .env file
# # # aclient = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

# # # @asynccontextmanager
# # # async def lifespan(app: FastAPI):
# # #     """
# # #     Lifespan Manager:
# # #     1. Starts the MCP Tool Server as a subprocess.
# # #     2. Connects the LangGraph Agent to it.
# # #     """
# # #     global agent_workflow
# # #     logger.info("🚀 Starting BrightSmile Agent...")

# # #     # Define the command to run the MCP server script
# # #     server_script = os.path.join("mcp_server", "run.py")
    
# # #     # Use the same python interpreter as the main app
# # #     server_params = StdioServerParameters(
# # #         command=sys.executable, 
# # #         args=[server_script],
# # #         env=os.environ.copy() # Pass env vars (API keys) to subprocess
# # #     )

# # #     try:
# # #         # Start the MCP Client connection
# # #         async with stdio_client(server_params) as (read, write):
# # #             async with ClientSession(read, write) as session:
# # #                 # Initialize the session
# # #                 await session.initialize()
                
# # #                 # Load tools from the connected session into our Agent Graph
# # #                 agent_workflow = await create_agent_graph(session)
                
# # #                 logger.info("✅ MCP Client connected to Tool Server.")
# # #                 yield
                
# # #     except Exception as e:
# # #         logger.error(f"❌ Failed to start MCP Server: {e}")
# # #         raise e
# # #     finally:
# # #         logger.info("🛑 Shutting down.")

# # # app = FastAPI(lifespan=lifespan)
# # # templates = Jinja2Templates(directory="templates")

# # # # --- Helper: Text to Speech (OpenAI TTS) ---
# # # async def synthesize_speech(text: str) -> str:
# # #     """Synthesizes speech using OpenAI's TTS API."""
# # #     try:
# # #         # Call OpenAI Audio API
# # #         response = await aclient.audio.speech.create(
# # #             model=config.OPENAI_TTS_MODEL,
# # #             voice=config.OPENAI_TTS_VOICE,
# # #             input=text
# # #         )
        
# # #         # Get binary audio content
# # #         audio_content = response.content
        
# # #         # Convert to Base64 for transmission to browser
# # #         return base64.b64encode(audio_content).decode('utf-8')
# # #     except Exception as e:
# # #         logger.error(f"OpenAI TTS Error: {e}")
# # #         return ""

# # # # --- Routes ---

# # # @app.head("/")
# # # async def health_check():
# # #     """
# # #     Responds to Render's health checks (HEAD requests).
# # #     This prevents the '405 Method Not Allowed' errors in logs.
# # #     """
# # #     return Response(status_code=200)

# # # @app.get("/favicon.ico", include_in_schema=False)
# # # async def favicon():
# # #     """Prevents 404 logs for favicon requests."""
# # #     return Response(status_code=204)

# # # @app.get("/", response_class=HTMLResponse)
# # # async def get_page(request: Request):
# # #     """Serves the Voice Chat Interface."""
# # #     return templates.TemplateResponse("voice_chat.html", {"request": request})

# # # @app.websocket("/ws/{client_id}")
# # # async def websocket_endpoint(websocket: WebSocket, client_id: str):
# # #     """
# # #     Handles Real-time Audio/Text WebSocket connection.
# # #     """
# # #     await websocket.accept()
    
# # #     # LangGraph Thread Configuration
# # #     config_graph = {"configurable": {"thread_id": client_id}}
    
# # #     try:
# # #         # 1. Trigger Initial Greeting
# # #         # The prompt in agent/prompts.py determines the actual text ("Welcome to BrightSmile...")
# # #         start_result = await agent_workflow.ainvoke(
# # #             {"messages": [{"role": "user", "content": "The call has started. Greet me."}], "patient_id": None},
# # #             config=config_graph
# # #         )
        
# # #         # Get the AI's response text
# # #         initial_text = start_result["messages"][-1].content
        
# # #         # Send Audio to client
# # #         await send_audio(websocket, initial_text)

# # #         # 2. Main Chat Loop
# # #         while True:
# # #             # Receive text (transcript) from browser
# # #             data = await websocket.receive_text()
# # #             logger.info(f"User ({client_id}): {data}")

# # #             # Invoke Agent
# # #             result = await agent_workflow.ainvoke(
# # #                 {"messages": [{"role": "user", "content": data}]}, 
# # #                 config=config_graph
# # #             )
            
# # #             # Get AI Response
# # #             ai_text = result["messages"][-1].content
            
# # #             # Send Audio back
# # #             await send_audio(websocket, ai_text)

# # #     except WebSocketDisconnect:
# # #         logger.info(f"Client {client_id} disconnected")
# # #     except Exception as e:
# # #         logger.error(f"WebSocket Error: {e}")

# # # async def send_audio(ws: WebSocket, text: str):
# # #     """Helper to synthesize audio and send JSON to WebSocket."""
# # #     if not text:
# # #         return

# # #     b64_audio = await synthesize_speech(text)
# # #     if b64_audio:
# # #         await ws.send_text(json.dumps({"text": text, "audio": b64_audio}))

# # # if __name__ == "__main__":
# # #     import uvicorn
# # #     # 1. Get PORT from Environment (Render sets this dynamically)
# # #     # 2. Default to 8000 for local testing
# # #     port = int(os.environ.get("PORT", 8000))
    
# # #     # 3. Run Uvicorn
# # #     # reload=False is recommended for production/deployments
# # #     uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)


# # import base64
# # import json
# # import logging
# # import asyncio
# # import io
# # import sys
# # import os
# # from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
# # from fastapi.responses import HTMLResponse
# # from fastapi.templating import Jinja2Templates
# # from contextlib import asynccontextmanager

# # # MCP & LangChain Imports
# # from mcp import ClientSession, StdioServerParameters
# # from mcp.client.stdio import stdio_client

# # # OpenAI Import
# # from openai import AsyncOpenAI

# # from config import config
# # from agent.graph import create_agent_graph

# # # Logging Setup
# # logging.basicConfig(level=config.LOG_LEVEL)
# # logger = logging.getLogger("BrightSmile")

# # # Global instances
# # agent_workflow = None

# # # Initialize OpenAI Async Client
# # aclient = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

# # @asynccontextmanager
# # async def lifespan(app: FastAPI):
# #     global agent_workflow
# #     logger.info("🚀 Starting BrightSmile Agent...")

# #     server_script = os.path.join("mcp_server", "run.py")
# #     server_params = StdioServerParameters(
# #         command=sys.executable, 
# #         args=[server_script],
# #         env=os.environ.copy()
# #     )

# #     try:
# #         async with stdio_client(server_params) as (read, write):
# #             async with ClientSession(read, write) as session:
# #                 await session.initialize()
# #                 agent_workflow = await create_agent_graph(session)
# #                 logger.info("✅ MCP Client connected to Tool Server.")
# #                 yield
# #     except Exception as e:
# #         logger.error(f"❌ Failed to start MCP Server: {e}")
# #         raise e
# #     finally:
# #         logger.info("🛑 Shutting down.")

# # app = FastAPI(lifespan=lifespan)
# # templates = Jinja2Templates(directory="templates")

# # # --- Helper: Text to Speech (OpenAI TTS) ---
# # async def synthesize_speech(text: str) -> str:
# #     try:
# #         response = await aclient.audio.speech.create(
# #             model=config.OPENAI_TTS_MODEL,
# #             voice=config.OPENAI_TTS_VOICE,
# #             input=text
# #         )
# #         return base64.b64encode(response.content).decode('utf-8')
# #     except Exception as e:
# #         logger.error(f"OpenAI TTS Error: {e}")
# #         return ""

# # # --- Helper: Speech to Text (OpenAI Whisper) ---
# # async def transcribe_audio(audio_bytes: bytes) -> str:
# #     """Sends audio bytes to OpenAI Whisper and returns text."""
# #     try:
# #         # Create a file-like object from bytes
# #         audio_file = io.BytesIO(audio_bytes)
# #         audio_file.name = "input.webm" # OpenAI needs a filename to know the format

# #         transcription = await aclient.audio.transcriptions.create(
# #             model="whisper-1",
# #             file=audio_file,
# #             language="en"
# #         )
# #         return transcription.text
# #     except Exception as e:
# #         logger.error(f"OpenAI STT Error: {e}")
# #         return ""

# # # --- Routes ---

# # @app.head("/")
# # async def health_check():
# #     return Response(status_code=200)

# # @app.get("/favicon.ico", include_in_schema=False)
# # async def favicon():
# #     return Response(status_code=204)

# # @app.get("/", response_class=HTMLResponse)
# # async def get_page(request: Request):
# #     return templates.TemplateResponse("voice_chat.html", {"request": request})

# # @app.websocket("/ws/{client_id}")
# # async def websocket_endpoint(websocket: WebSocket, client_id: str):
# #     await websocket.accept()
    
# #     config_graph = {"configurable": {"thread_id": client_id}}
    
# #     try:
# #         # 1. Trigger Initial Greeting
# #         # Replace the initial trigger with a natural one
# #         start_result = await agent_workflow.ainvoke(
# #             {"messages": [], "patient_id": None},  # Empty history → triggers greeting
# #             config=config_graph
# #         )
# #         initial_text = start_result["messages"][-1].content
# #         await send_audio(websocket, initial_text)

# #         # 2. Main Chat Loop
# #         while True:
# #             # We use receive() instead of receive_text() to handle both bytes and text
# #             message = await websocket.receive()
            
# #             user_text = ""

# #             if "bytes" in message:
# #                 # Audio received -> Transcribe it
# #                 logger.info(f"Received audio bytes from {client_id}...")
# #                 user_text = await transcribe_audio(message["bytes"])
# #                 logger.info(f"Transcribed: {user_text}")
            
# #             elif "text" in message:
# #                 # Text received (fallback)
# #                 user_text = message["text"]

# #             if not user_text or user_text.strip() == "":
# #                 continue

# #             # Invoke Agent with the text (either from STT or direct)
# #             result = await agent_workflow.ainvoke(
# #                 {"messages": [{"role": "user", "content": user_text}]}, 
# #                 config=config_graph
# #             )
            
# #             ai_text = result["messages"][-1].content
# #             await send_audio(websocket, ai_text)

# #     except WebSocketDisconnect:
# #         logger.info(f"Client {client_id} disconnected")
# #     except Exception as e:
# #         logger.error(f"WebSocket Error: {e}")

# # async def send_audio(ws: WebSocket, text: str):
# #     if not text: return
# #     b64_audio = await synthesize_speech(text)
# #     if b64_audio:
# #         await ws.send_text(json.dumps({"text": text, "audio": b64_audio}))

# # if __name__ == "__main__":
# #     import uvicorn
# #     port = int(os.environ.get("PORT", 8000))
# #     uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

# import base64
# import json
# import logging
# import asyncio
# import io
# import sys
# import os
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from contextlib import asynccontextmanager

# # MCP & LangChain Imports
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client

# # OpenAI Import
# from openai import AsyncOpenAI

# # ElevenLabs Import
# from elevenlabs.client import AsyncElevenLabs
# from elevenlabs import VoiceSettings

# from config import config
# from agent.graph import create_agent_graph

# # Logging Setup
# logging.basicConfig(level=config.LOG_LEVEL)
# logger = logging.getLogger("BrightSmile")

# # Global instances
# agent_workflow = None

# # 1. Initialize OpenAI Async Client (For Whisper STT and LLM)
# aclient = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

# # 2. Initialize ElevenLabs Async Client (For TTS)
# elevenlabs_client = AsyncElevenLabs(api_key=config.ELEVENLABS_API_KEY)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global agent_workflow
#     logger.info("🚀 Starting BrightSmile Agent...")

#     # Start the MCP Tool Server
#     server_script = os.path.join("mcp_server", "run.py")
#     server_params = StdioServerParameters(
#         command=sys.executable, 
#         args=[server_script],
#         env=os.environ.copy()
#     )

#     try:
#         async with stdio_client(server_params) as (read, write):
#             async with ClientSession(read, write) as session:
#                 await session.initialize()
#                 # Pass session to graph creator
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

# # --- Helper: Text to Speech (ElevenLabs) ---
# async def synthesize_speech(text: str) -> str:
#     """
#     Converts text to audio using ElevenLabs and returns base64 encoded string.
#     """
#     if not text: return ""
#     try:
#         # FIX: Do not 'await' this call. It returns an async generator immediately.
#         audio_stream = elevenlabs_client.text_to_speech.convert(
#             voice_id=config.ELEVENLABS_VOICE_ID,
#             output_format="mp3_44100_128",
#             text=text,
#             model_id=config.ELEVENLABS_MODEL,
#             voice_settings=VoiceSettings(
#                 stability=0.5,
#                 similarity_boost=0.75,
#                 style=0.0,
#                 use_speaker_boost=True,
#             ),
#         )

#         # Collect all chunks from the async stream
#         audio_bytes = b""
#         async for chunk in audio_stream:
#             if chunk:
#                 audio_bytes += chunk

#         return base64.b64encode(audio_bytes).decode('utf-8')

#     except Exception as e:
#         logger.error(f"ElevenLabs TTS Error: {e}")
#         return ""

# # # --- Helper: Speech to Text (OpenAI Whisper) ---
# # async def transcribe_audio(audio_bytes: bytes) -> str:
# #     """Sends audio bytes to OpenAI Whisper and returns text."""
# #     try:
# #         # Create a file-like object from bytes
# #         audio_file = io.BytesIO(audio_bytes)
# #         audio_file.name = "input.webm" # OpenAI needs a filename to know the format

# #         transcription = await aclient.audio.transcriptions.create(
# #             model="whisper-1",
# #             file=audio_file,
# #             language="en"
# #         )
# #         return transcription.text
# #     except Exception as e:
# #         logger.error(f"OpenAI STT Error: {e}")
# #         return ""

# # --- Routes ---

# @app.head("/")
# async def health_check():
#     return Response(status_code=200)

# @app.get("/favicon.ico", include_in_schema=False)
# async def favicon():
#     return Response(status_code=204)

# @app.get("/", response_class=HTMLResponse)
# async def get_page(request: Request):
#     return templates.TemplateResponse("voice_chat.html", {"request": request})

# @app.websocket("/ws/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: str):
#     await websocket.accept()
    
#     config_graph = {"configurable": {"thread_id": client_id}}
    
#     try:
#         # 1. Trigger Initial Greeting
#         start_result = await agent_workflow.ainvoke(
#             {"messages": [], "patient_id": None}, 
#             config=config_graph
#         )
#         initial_text = start_result["messages"][-1].content
#         await send_audio(websocket, initial_text)

#         # 2. Main Chat Loop
#         while True:
#             message = await websocket.receive()
            
#             user_text = ""

#             if "bytes" in message:
#                 # Audio received -> Transcribe with Whisper
#                 logger.info(f"Received audio bytes from {client_id}...")
#                 user_text = await transcribe_audio(message["bytes"])
#                 logger.info(f"Transcribed: {user_text}")
            
#             elif "text" in message:
#                 user_text = message["text"]

#             if not user_text or user_text.strip() == "":
#                 continue

#             # Invoke Agent (LangGraph logic)
#             result = await agent_workflow.ainvoke(
#                 {"messages": [{"role": "user", "content": user_text}]}, 
#                 config=config_graph
#             )
            
#             ai_text = result["messages"][-1].content
            
#             # Send back ElevenLabs Audio
#             await send_audio(websocket, ai_text)

#     except WebSocketDisconnect:
#         logger.info(f"Client {client_id} disconnected")
#     except Exception as e:
#         logger.error(f"WebSocket Error: {e}")

# async def send_audio(ws: WebSocket, text: str):
#     if not text: return
#     b64_audio = await synthesize_speech(text)
#     if b64_audio:
#         await ws.send_text(json.dumps({"text": text, "audio": b64_audio}))

# if __name__ == "__main__":
#     import uvicorn
#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

import base64
import json
import logging
import asyncio
import io
import sys
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

# MCP & LangChain Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# OpenAI Imports
from openai import AsyncOpenAI

# ElevenLabs Import
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings

from config import config
from agent.graph import create_agent_graph

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BrightSmile")

# ============================================================================
# GLOBAL INSTANCES
# ============================================================================
agent_workflow = None
aclient = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
elevenlabs_client = AsyncElevenLabs(api_key=config.ELEVENLABS_API_KEY)

# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP server and agent on startup."""
    global agent_workflow
    logger.info("🚀 Starting BrightSmile Agent...")
    
    server_script = os.path.join("mcp_server", "run.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy()
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                agent_workflow = await create_agent_graph(session)
                logger.info("✅ MCP Client connected to Tool Server.")
                yield
    except Exception as e:
        logger.error(f"❌ Failed to start MCP Server: {e}")
        raise
    finally:
        logger.info("🛑 Shutting down.")

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# ============================================================================
# TEXT-TO-SPEECH (ElevenLabs)
# ============================================================================
async def synthesize_speech(text: str) -> str:
    """
    Converts text to audio using ElevenLabs.
    Returns base64-encoded MP3 audio string.
    """
    if not text or len(text.strip()) == 0:
        logger.warning("Empty text provided to TTS")
        return ""
    
    try:
        logger.info(f"Synthesizing speech: {text[:100]}...")
        
        # text_to_speech.convert returns an async generator
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id=config.ELEVENLABS_VOICE_ID,
            output_format="mp3_44100_128",
            text=text,
            model_id=config.ELEVENLABS_MODEL,
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True,
            ),
        )
        
        # Collect all chunks from async stream
        audio_bytes = b""
        async for chunk in audio_stream:
            if chunk:
                audio_bytes += chunk
        
        if not audio_bytes:
            logger.error("No audio data received from ElevenLabs")
            return ""
        
        b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
        logger.info(f"✓ Speech synthesis complete ({len(audio_bytes)} bytes)")
        return b64_audio
        
    except Exception as e:
        logger.error(f"❌ ElevenLabs TTS Error: {e}")
        return ""

# ============================================================================
# SPEECH-TO-TEXT (OpenAI Whisper)
# ============================================================================
async def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Sends audio bytes to OpenAI Whisper and returns transcribed text.
    """
    if not audio_bytes or len(audio_bytes) == 0:
        logger.warning("Empty audio bytes received")
        return ""
    
    try:
        logger.info(f"Transcribing {len(audio_bytes)} bytes of audio...")
        
        # Create file-like object from bytes
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "input.webm"
        
        # Call Whisper API
        transcription = await aclient.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
        
        text = transcription.text.strip()
        logger.info(f"✓ Transcribed: {text}")
        return text
        
    except Exception as e:
        logger.error(f"❌ OpenAI STT Error: {e}")
        return ""

# ============================================================================
# ROUTES
# ============================================================================
@app.head("/")
async def health_check():
    """Health check endpoint."""
    return Response(status_code=200)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint."""
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def get_page(request: Request):
    """Serve the voice chat interface."""
    return templates.TemplateResponse("voice_chat.html", {"request": request})

# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time voice chat.
    Handles bidirectional audio/text communication.
    """
    await websocket.accept()
    logger.info(f"✓ Client {client_id} connected")
    
    config_graph = {"configurable": {"thread_id": client_id}}
    
    try:
        # 1. Send initial greeting
        logger.info("Sending initial greeting...")
        start_result = await agent_workflow.ainvoke(
            {"messages": [], "patient_id": None, "patient_name": None},
            config=config_graph
        )
        
        initial_text = start_result["messages"][-1].content
        logger.info(f"Initial response: {initial_text}")
        await send_message(websocket, initial_text)
        
        # 2. Main conversation loop
        while True:
            message = await websocket.receive()
            
            # Handle binary audio data
            if "bytes" in message:
                logger.info(f"Received audio from {client_id}")
                user_text = await transcribe_audio(message["bytes"])
                
                if not user_text:
                    logger.warning("Transcription returned empty string")
                    await send_message(
                        websocket,
                        "I didn't catch that. Could you say that again?"
                    )
                    continue
            
            # Handle text input
            elif "text" in message:
                user_text = message["text"].strip()
            
            else:
                continue
            
            # Skip empty messages
            if not user_text:
                continue
            
            logger.info(f"User message from {client_id}: {user_text}")
            
            # 3. Invoke agent with user message
            result = await agent_workflow.ainvoke(
                {"messages": [{"role": "user", "content": user_text}]},
                config=config_graph
            )
            
            # Extract AI response
            ai_message = result["messages"][-1]
            ai_text = ai_message.content
            
            logger.info(f"Agent response: {ai_text}")
            
            # 4. Send response to client
            await send_message(websocket, ai_text)
    
    except WebSocketDisconnect:
        logger.info(f"✓ Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket Error for {client_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=1000, reason=str(e)[:50])
        except:
            pass

async def send_message(ws: WebSocket, text: str):
    """
    Send text and synthesized audio to client.
    """
    if not text:
        return
    
    logger.info(f"Generating speech for: {text[:80]}...")
    b64_audio = await synthesize_speech(text)
    
    payload = {
        "text": text,
        "audio": b64_audio if b64_audio else None
    }
    
    try:
        await ws.send_text(json.dumps(payload))
        logger.info(f"✓ Message sent to client")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

# ============================================================================
# SERVER STARTUP
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)