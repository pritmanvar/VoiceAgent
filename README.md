# VoiceAgent

A real-time voice-based conversational AI agent built with FastAPI, Groq LLM, and ElevenLabs. This application enables natural voice conversations with AI through a sleek web interface.

## Features

- 🎤 **Real-time Voice Recognition** - Speech-to-text using ElevenLabs Scribe V2
- 🤖 **AI-Powered Responses** - Conversational AI using Groq's LLM
- 🔊 **Text-to-Speech** - Choice between ElevenLabs TTS or browser-native TTS
- 📊 **Voice Activity Detection** - Visual feedback for audio levels and silence detection
- 💬 **Chat Interface** - Clean, modern UI showing conversation history
- ⚡ **WebSocket Communication** - Low-latency bidirectional communication
- 🎚️ **Adjustable Sensitivity** - Customizable silence threshold for voice detection

## Demo

The application provides:
- Visual audio level monitoring with dB meter
- Animated wave effects during recording
- Real-time transcription display
- Conversational AI responses with voice playback

## Prerequisites

- Python 3.8+
- [Groq API Key](https://console.groq.com/)
- [ElevenLabs API Key](https://elevenlabs.io/)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd VoiceAgent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

## Usage

1. **Start the server**
   ```bash
   uvicorn main:app --reload
   ```

2. **Open your browser**
   
   Navigate to `http://localhost:8000`

3. **Start conversation**
   - Click "Start Conversation" button
   - Speak into your microphone
   - The AI will respond both in text and voice

## Configuration

### TTS Provider

In [main.py](main.py#L122), you can switch between ElevenLabs and browser TTS:

```python
ENABLE_ELEVENLABS_TTS = False  # Set to True for ElevenLabs, False for browser TTS
```

### Voice Settings

- **Silence Threshold**: Adjust the slider in the UI (-100 to 0 dB)
- **Voice ID**: Change the ElevenLabs voice in [main.py](main.py#L130) (default: Rachel - `21m00Tcm4TlvDq8ikWAM`)
- **LLM Model**: Configured in [main.py](main.py#L114) (default: `openai/gpt-oss-120b`)

## Architecture

### Backend (`main.py`)
- **FastAPI** server with WebSocket support
- **Speech-to-Text**: ElevenLabs Scribe V2 API
- **LLM Processing**: Groq API for conversational responses
- **Text-to-Speech**: Optional ElevenLabs or browser-based TTS

### Frontend (`templates/index.html`)
- Real-time audio capture using MediaRecorder API
- Voice activity detection with Web Audio API
- WebSocket communication for bidirectional streaming
- Tailwind CSS for responsive, modern UI

## Dependencies

```
fastapi          - Web framework
uvicorn          - ASGI server
python-multipart - Form data handling
jinja2           - Template engine
groq             - Groq LLM API client
elevenlabs       - ElevenLabs API client
python-dotenv    - Environment variable management
websockets       - WebSocket support
```

## Project Structure

```
VoiceAgent/
├── main.py              # FastAPI application and WebSocket handlers
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
├── templates/
│   └── index.html      # Frontend UI
```

## How It Works

1. **Audio Capture**: Browser captures microphone input and sends chunks via WebSocket
2. **Voice Detection**: Client-side analyser detects speech vs silence
3. **Transcription**: Audio buffer sent to ElevenLabs STT when user stops speaking
4. **AI Processing**: Transcribed text sent to Groq LLM for response generation
5. **Response Delivery**: AI response converted to speech and streamed back to client
6. **Audio Playback**: Browser plays the audio response and restarts listening

## Troubleshooting

### No audio detected
- Check microphone permissions in browser
- Adjust silence threshold slider in the UI

### API errors
- Verify API keys in `.env` file
- Check API rate limits and quotas

### WebSocket connection issues
- Ensure server is running on the correct port
- Check firewall settings

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
