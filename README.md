# lulu.ai — Local Voice Assistant

lulu.ai is a fully local, private voice assistant I built from scratch that runs entirely on my machine. No cloud, no API fees, no subscriptions. I talk to it through a physical button I wired up on an Arduino, it listens, thinks, and talks back. It does so while showing its status on an LCD screen sitting on my desk.


---

## What It Does

- **Voice in** — press the physical button or click the mic in the browser, speak, and your words get transcribed locally using the Faster Whisper
- **AI responses** — runs a local LLM (Qwen2.5 7B) through Ollama, streams the response back token by token like ChatGPT
- **Voice out** — Lulu speaks the response back through your speaker, and you can cut it off mid-sentence with a Stop button
- **Live web search** — Using duckduck go, you can ask about the weather or  latest news. It pulls real data from the web before answering.
- **Hardware integration** — Q physical Arduino button starts and stops recording, an LCD screen shows what Lulu is doing in real time (listening, processing, speaking)
- **Smart browser launch** — By pressing the Arduino button when the browser isn't open automatically launches Chrome to the right URL

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend | FastAPI + WebSockets |
| LLM | Ollama + Qwen2.5 7B (runs 100% locally) |
| Speech-to-Text | Faster Whisper (runs 100% locally) |
| Text-to-Speech | macOS `say` / Piper (runs 100% locally) |
| Web Search | DuckDuckGo (no API key) |
| Weather | Open-Meteo (no API key) |
| Frontend | Vanilla JS, HTML, CSS — no frameworks |
| Hardware | Arduino UNO R3 + LCD1602 |
| Serial Comms | pyserial |

---

## How It's Built

The backend is a single FastAPI server that handles everything, the webSocket connections from the browser, serial communication with the Arduino, audio transcription, LLM streaming, and TTS playback.

When you send a message (voice or text):
1. Python checks if the question needs live data (weather or web search) and fetches it first (still a work in progress, its prone to hallucination)
2. The query and live data gets sent to Ollama, which streams the response back token by token
3. The browser renders each token as it arrives
4. Once the response is done, Lulu speaks it through the speaker using a subprocess, meaning you can kill it mid-sentence cleanly
5. The Arduino LCD updates at every stage so you always know what's happening 

The Arduino runs a sketch that toggles between `START` and `STOP` on each button press and displays status strings sent from Python over serial.

---

## Hardware Setup

- Elegoo UNO R3 connected via USB
- Push button wired to Pin 2 with `INPUT_PULLUP` (no resistor needed)
- LCD1602 16-pin display wired to Pins 7–12

---

## Running It Locally

```bash
# Prerequisites
brew install ffmpeg portaudio
pip install fastapi uvicorn faster-whisper httpx duckduckgo-search

# Pull the LLM
ollama pull qwen2.5:7b

# Run
source ~/claude-button/bin/activate
uvicorn main:app --reload --port 7001
```

Open `http://localhost:7001`.

---

## Why I Built This

I was bored and wanted a voice assistant I actually control, no data leaving my machine, and no monthly fees. I also wanted to learn how all the pieces fit together: local LLMs, real-time audio, WebSockets, and hardware integration in one project.

The plan is to eventually move this off my laptop and onto a Raspberry Pi 5 so it runs standalone on my desk 24/7.

---

## Next steps

- Move to Raspberry Pi 5 for standalone operation
- Swap macOS `say` for Piper TTS for a better voice
- Add wake word detection so the button isn't needed!
- Add conversation memory so Lulu remembers context across sessions!
