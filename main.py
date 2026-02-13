import os
import io
import json
import base64
import time
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from groq import Groq
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    audio_buffer = bytearray()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "audio_chunk":
                # Accumulate audio data
                chunk = base64.b64decode(message["data"])
                audio_buffer.extend(chunk)
                

            elif message["type"] == "stop_recording":
                # Process the accumulated audio
                if len(audio_buffer) > 0:
                    logger.info(f"[AUDIO BUFFER] Total size: {len(audio_buffer)} bytes")
                    
                    # 1. ElevenLabs STT
                    # Send buffer as a file-like object
                    # API expects a file-like object with a name and byte content
                    audio_file = io.BytesIO(audio_buffer)
                    audio_file.name = "audio.webm"
                    
                    try:
                        logger.info("[STT] Starting ElevenLabs transcription...")
                        stt_start_time = time.time()
                        
                        transcription = elevenlabs_client.speech_to_text.convert(
                            file=audio_file,
                            model_id="scribe_v2",
                            language_code="eng",
                            tag_audio_events=False
                        )
                        
                        stt_duration = time.time() - stt_start_time
                        logger.info(f"[STT] Completed in {stt_duration:.2f}s")
                        # transcription is a string in this SDK version usually, or an object?
                        # Based on docs "print(transcription)", it seems to return text or an object with text.
                        # Recent SDKs might return a Generator if streaming, but convert() usually returns result.
                        # Let's assume it returns a string or object with .text if not simple string.
                        # safely handle both
                        user_text = ""

                        if hasattr(transcription, "text"):
                            user_text = transcription.text
                        else:
                            # Fallback/Debug
                            user_text = str(transcription)

                        logger.info(f"[TRANSCRIPTION] User said: {user_text}")
                        
                        if user_text.strip():
                            # Send transcription to UI
                            await websocket.send_json({"type": "transcription", "text": user_text})
                            
                            # 2. LLM & TTS
                            logger.info("[PIPELINE] Starting LLM and TTS processing...")
                            await process_llm_and_tts(websocket, user_text)
                            
                        else:
                            await websocket.send_json({"type": "status", "text": "No speech detected."})

                    except Exception as e:
                        logger.error(f"[STT] Transcription Error: {e}")
                        await websocket.send_json({"type": "status", "text": "Error in transcription."})
                    
                    # Reset buffer
                    audio_buffer = bytearray()
                    await websocket.send_json({"type": "status", "text": "Ready"})

    except WebSocketDisconnect:
        logger.info("[WEBSOCKET] Client disconnected")

async def process_llm_and_tts(websocket: WebSocket, user_text: str):
    await websocket.send_json({"type": "status", "text": "Thinking..."})
    
    # 1. Get LLM Response
    # Using a valid Groq model
    try:
        logger.info("[LLM] Starting Groq API call...")
        llm_start_time = time.time()
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful conversational voice assistant. Keep your responses concise and natural."
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="openai/gpt-oss-120b",
        )
        
        llm_duration = time.time() - llm_start_time
        ai_text = chat_completion.choices[0].message.content
        logger.info(f"[LLM] Response generated in {llm_duration:.2f}s | Response length: {len(ai_text)} characters")
        
        # Send text to UI
        await websocket.send_json({"type": "response_text", "text": ai_text})
    
        # Configuration for TTS (Easy switch)
        ENABLE_ELEVENLABS_TTS = False # Set to True to use ElevenLabs, False for Browser TTS

        if ENABLE_ELEVENLABS_TTS:
            await websocket.send_json({"type": "status", "text": "Speaking (ElevenLabs)..."})
            # 2. Get TTS Audio (Streaming)
            try:
                logger.info("[TTS] Starting ElevenLabs text-to-speech...")
                tts_start_time = time.time()
                
                # Using new SDK method for TTS
                audio_stream = elevenlabs_client.text_to_speech.convert(
                    text=ai_text,
                    voice_id="21m00Tcm4TlvDq8ikWAM", # Rachel voice ID
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128",
                )

                # Check if it returns bytes or generator. 
                full_audio = b""
                if hasattr(audio_stream, '__iter__') and not isinstance(audio_stream, (bytes, bytearray)):
                     for chunk in audio_stream:
                        if chunk:
                            full_audio += chunk
                else:
                     # It's a single bytes object
                     full_audio = audio_stream

                tts_duration = time.time() - tts_start_time
                if full_audio:
                     logger.info(f"[TTS] Audio generated in {tts_duration:.2f}s | Audio size: {len(full_audio)} bytes")
                     audio_b64 = base64.b64encode(full_audio).decode('utf-8')
                     await websocket.send_json({"type": "audio", "data": audio_b64})

            except Exception as e:
                logger.error(f"[TTS] TTS Error: {e}")
                await websocket.send_json({"type": "status", "text": "Error in TTS."})
                # Fallback to browser TTS if server TTS fails?
                # For now, just let frontend handle text response
        else:
            # Browser TTS
            logger.info("[TTS] Using browser text-to-speech")
            await websocket.send_json({"type": "status", "text": "Speaking (Browser)..."})
            # We already sent "response_text", frontend will handle speaking it if no audio comes or based on flag?
            # Let's send a specific message to trigger browser TTS explicitly if we want to be robust
            await websocket.send_json({"type": "browser_tts", "text": ai_text})
            
    except Exception as e:
        logger.error(f"[LLM] LLM Error: {e}")
        await websocket.send_json({"type": "status", "text": "Error in LLM."})
    
    logger.info("[PIPELINE] LLM and TTS processing completed")
        


