import base64
import json
import logging
import asyncio
import io
import sys
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI
from elevenlabs.client import AsyncElevenLabs
from elevenlabs import VoiceSettings
from langchain_core.callbacks import BaseCallbackHandler # IMPORT ADDED

from config import config
from agent.graph import create_agent_graph
from logger_setup import setup_logging

# Setup Logging
setup_logging()
# logging.basicConfig(
#     level=config.LOG_LEVEL,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
logger = logging.getLogger("BrightSmile-Main")

agent_workflow = None
aclient = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
elevenlabs_client = AsyncElevenLabs(api_key=config.ELEVENLABS_API_KEY)

# ===========================================================================
# LANGSMITH COMPATIBLE TOKEN HANDLER
# ===========================================================================
class OpenAITokenHandler(BaseCallbackHandler):
    """
    Captures token usage for the LAST OpenAI LLM call in a run.
    Matches LangSmith numbers exactly.
    """
    def __init__(self):
        self.usage = None

    def on_llm_end(self, response, **kwargs):
        if response.llm_output and "token_usage" in response.llm_output:
            self.usage = response.llm_output["token_usage"]


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# ... (Keep synthesize_speech and transcribe_audio functions as is) ...
async def synthesize_speech(text: str) -> str:
    if not text: return ""
    try:
        audio_stream = elevenlabs_client.text_to_speech.convert(
            voice_id=config.ELEVENLABS_VOICE_ID,
            output_format="mp3_44100_128",
            text=text,
            model_id=config.ELEVENLABS_MODEL,
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.75),
        )
        audio_bytes = b"".join([chunk async for chunk in audio_stream if chunk])
        return base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return ""

async def transcribe_audio(audio_bytes: bytes) -> str:
    if not audio_bytes: return ""
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "input.webm"
        transcription = await aclient.audio.transcriptions.create(
            model="whisper-1", file=audio_file, language="en"
        )
        return transcription.text.strip()
    except Exception as e:
        logger.error(f"STT Error: {e}")
        return ""

@app.get("/", response_class=HTMLResponse)
async def get_page(request: Request):
    return templates.TemplateResponse("voice_chat.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, tz: str = Query("UTC")):
    await websocket.accept()
    
    # 1. Initialize Thread Config
    # We add metadata here so it shows up in your LangSmith Project correctly
    config_graph = {
        "configurable": {"thread_id": client_id},
        "metadata": {
            "source": "voice-agent-websocket", 
            "user_id": client_id,
            "timezone": tz # Optional: Log it for debugging
        }
    }
    
    TIMEOUT_SECONDS = 60 

    try:
        # Initial Greeting
        # CHANGED: Pass 'timezone': tz in the initial state
        start_result = await agent_workflow.ainvoke(
            {
                "messages": [], 
                "patient_id": None, 
                "patient_name": None,
                "timezone": tz 
            },
            config=config_graph
        )
        initial_text = start_result["messages"][-1].content
        await send_message(websocket, initial_text, {})


        # Main Loop
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout=TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                logger.info(f"Client {client_id} timed out.")
                await send_message(websocket, "I haven't heard from you in a minute, so I'm going to end the call to free up the line. Please call back if you need anything!", end_call=True)
                break

            user_text = ""
            if "bytes" in message:
                user_text = await transcribe_audio(message["bytes"])
                if not user_text:
                    await send_message(websocket, "I didn't catch that.")
                    continue
            elif "text" in message:
                user_text = message["text"].strip()

            if not user_text: continue

            # --- INVOKE AGENT WITH LANGSMITH TRACKING ---
            
            # # 1. Initialize our Handler
            # token_handler = LangSmithTokenHandler()
            
            # # 2. Inject Handler into the config
            # # This ensures the tokens are captured during the run
            # run_config = config_graph.copy()
            # run_config["callbacks"] = [token_handler]

            token_handler = OpenAITokenHandler()

            run_config = {
                **config_graph,
                "callbacks": [token_handler]
            }


            # 3. Invoke
            result = await agent_workflow.ainvoke(
                {"messages": [{"role": "user", "content": user_text}]},
                config=run_config
            )

            ai_message = result["messages"][-1]
            ai_text = ai_message.content
            
            # 4. Extract Usage from our Handler
            # usage_stats = {
            #     "total_tokens": token_handler.total_tokens,
            #     "prompt_tokens": token_handler.prompt_tokens,
            #     "completion_tokens": token_handler.completion_tokens
            # }

            usage_stats = token_handler.usage or {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }

            should_end = False
            if "[END_CALL]" in ai_text:
                ai_text = ai_text.replace("[END_CALL]", "").strip()
                should_end = True

            await send_message(websocket, ai_text, usage_stats, end_call=should_end)
            
            if should_end:
                await asyncio.sleep(1) 
                break

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

async def send_message(ws: WebSocket, text: str, usage: dict = {}, end_call: bool = False):
    b64_audio = await synthesize_speech(text)
    payload = {
        "text": text,
        "audio": b64_audio,
        "usage": usage,
        "end_call": end_call
    }
    await ws.send_text(json.dumps(payload))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)