# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

lulu.ai is a locally-hosted voice assistant with a ChatGPT-style browser UI. Everything runs on your machine — no cloud, no API fees, no subscriptions. Built on a Mac, designed to eventually move to a Raspberry Pi 5.

You talk to it via a physical Arduino button or a mic button in the browser. It listens, transcribes your voice, thinks with a local LLM, speaks the response back, and shows its status on an LCD screen.

## Directory Structure

```text
lulu_ai/
├── main.py                 # FastAPI app — routing, WebSocket, TTS orchestration
├── core/
│   ├── llm.py              # Ollama chat API client (streaming)
│   ├── stt.py              # Faster Whisper transcription
│   ├── tts.py              # macOS TTS via say, upgradeable to Piper binary
│   ├── serial_worker.py    # Arduino serial thread (START/STOP commands + LCD)
│   └── tools.py            # Web search (DuckDuckGo) + weather (Open-Meteo)
├── templates/
│   └── index.html          # Single-page UI
├── static/
│   ├── css/style.css       # Dark mode styling
│   ├── js/app.js           # WebSocket client, MediaRecorder, UI logic
│   └── favicon.svg
└── arduino/
    └── lulu_assistant/
        └── lulu_assistant.ino
```

## How to Run It

```bash
# Activate the venv
source ~/claude-button/bin/activate

# Make sure Ollama is running
ollama serve

# Start the server
cd ~/Desktop/Projects/lulu_ai
uvicorn main:app --reload --port 7001
```

Open `http://localhost:7001`. The Arduino button will open Chrome automatically if no browser is connected.

## Key Config to Know

- **Model**: `qwen2.5:7b` in `core/llm.py` — change `MODEL` if you switch models
- **Default weather location**: `DEFAULT_LOCATION` at the top of `core/tools.py`
- **Arduino serial port**: auto-detected via `ls /dev/cu.usb*` — changes every session
- **Piper TTS**: falls back to macOS `say` if `~/piper/piper` binary isn't installed

## How the Backend Works

- `main.py` runs a FastAPI server with a single `/ws` WebSocket per browser session
- When a message comes in, it runs `tools.detect_and_fetch()` first (weather or search if needed), then streams tokens from Ollama back to the browser
- TTS runs as a background `asyncio` task so the WebSocket stays open to receive stop commands mid-speech
- The serial worker runs in a daemon thread, reads `START`/`STOP` from the Arduino, and broadcasts to all connected browser clients via WebSocket
- When the Arduino button is pressed and no browser is open, Python opens Chrome before starting anything

## LLM Integration

- Uses `/api/chat` (not `/api/generate`) so the model gets proper chat formatting
- Context from web search or weather is injected into the user message with a strict instruction to only use the live data — not training memory
- Token cap is enforced in Python (`MAX_TOKENS = 500`), not in the prompt

## Frontend Rules

- Vanilla JS only — no React, Vue, or Tailwind
- Audio recording uses the browser MediaRecorder API
- WebSocket events: `token`, `done`, `tts_start`, `tts_end`, `status`, `record_start`, `record_stop`, `stop_tts`

## Hardware

- **Elegoo UNO R3** connected via USB (`/dev/cu.usbmodem*`)
- **Button**: Pin 2 with `INPUT_PULLUP` — first press sends `START`, second sends `STOP`
- **LCD1602**: RS → Pin 7, E → Pin 8, D4–D7 → Pins 9–12
- Always close Arduino IDE Serial Monitor before running Python or you'll get a port conflict

## Common Issues

- `zsh: command not found: uvicorn` — venv isn't active, run `source ~/claude-button/bin/activate`
- LCD showing blanks or blocks — turn the contrast potentiometer
- Serial port busy — close Arduino IDE Serial Monitor
- Arduino port changed — check with `ls /dev/cu.usb*`
