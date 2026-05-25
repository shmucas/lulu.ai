# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

lulu.ai is a locally-hosted, privacy-first voice assistant with a ChatGPT-style browser UI. No cloud, no API fees — everything runs on-device (Mac during development, Raspberry Pi 5 later).

## Directory Structure

Ensure all new code follows this explicit layout:

```text
lulu_ai/
├── CLAUDE.md
├── main.py                 # FastAPI application & routing
├── core/
│   ├── __init__.py
│   ├── serial_worker.py    # Arduino communication thread
│   ├── stt.py              # Faster Whisper implementation
│   ├── llm.py              # Ollama API client wrapper
│   └── tts.py              # Piper TTS wrapper/subprocess
├── templates/
│   └── index.html          # Web UI HTML
├── static/
│   ├── css/style.css       # Dark mode styling
│   └── js/app.js           # WebSocket handling & Audio recording
└── arduino/
    └── lulu_assistant/
        └── lulu_assistant.ino  # Arduino C++ Sketch
```

## System Requirements & Pre-Requisites

Before executing Python installation phases, ensure these Mac binaries are available:
- **PortAudio** (required for sounddevice): `brew install portaudio`
- **Ollama Engine**: must be running locally on port `11434`

## Development Commands

```bash
# Activate virtual environment (always required first)
source ~/claude-button/bin/activate

# Start Ollama if not running
ollama serve

# Run the dev server (from project root)
uvicorn main:app --reload --port 7001

# Open in browser
open http://localhost:7001

# Debug: find Arduino serial port (changes between sessions)
ls /dev/cu.usb*

# Debug: verify Ollama is up
ollama list

# Kill Ollama
killall ollama
```

## Architecture

```
[Arduino Button] → USB Serial → [FastAPI Backend]
                                      ↕
                              [Browser UI via WebSocket]
                                      ↕
                [Whisper STT] → [Ollama LLM] → [Piper TTS]
                                      ↕
                [LCD shows: READY / LISTENING / PROCESSING]
```

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend | FastAPI + WebSockets |
| Frontend | HTML + CSS + Vanilla JS (no framework) |
| STT | Faster Whisper (local) |
| LLM | Ollama + Qwen2.5 3B |
| TTS | Piper (local, via subprocess) |
| Hardware | Arduino UNO R3 (button + LCD1602 16-pin non-I2C) |
| Serial | pyserial |

## Technical Guardrails

1. **Ollama Integration:** Use the official `ollama` Python library or `httpx` async calls to `http://localhost:11434/api/generate`. Use model `qwen2.5:3b` or `llama3.2`. Enforce response truncation in Python — small models ignore prompt-level length limits.
2. **Asynchronous Code:** The FastAPI backend must handle WebSocket connections with `async def`. Do not block the main event loop with long-running sync operations.
3. **Serial Threading:** Run the `pyserial` listener loop inside a background thread or async executor so it does not block the FastAPI webserver.
4. **Piper TTS on Mac:** Implement Piper via `subprocess` calling the standalone Mac binary. Send `SIGTERM` to the player process to handle the "Stop TTS" button mid-sentence.
5. **No Frameworks:** Frontend must use native browser Web APIs only — Vanilla JS, standard WebSockets, MediaRecorder API. Do not pull in React, Vue, or Tailwind via CDN.

## Hardware Configuration

**Elegoo UNO R3:**
- Port: `/dev/cu.usbmodem*` — dynamic, always check with `ls /dev/cu.usb*` before running. Update `PORT` in code each session.
- Push Button: Pin 2 (`INPUT_PULLUP`). Toggle: first press = `START\n`, second press = `STOP\n` over serial.
- LCD1602: RS → Pin 7, E → Pin 8, D4–D7 → Pins 9–12.

**Gotchas:**
- Arduino IDE Serial Monitor must be closed before running Python (port conflict).
- LCD contrast: if display shows blanks or blocks, adjust the potentiometer. Contrast wiper must share a breadboard row with LCD pin 3.
- Button wiring: any unintended wire sharing Pin 2's breadboard row will cause phantom triggers.

## Existing Infrastructure (do not rewrite)

- venv at `~/claude-button/` with `pyserial`, `fastapi`, `uvicorn`, `websockets`, `httpx` already installed.
- Ollama running with `llama3.2` and `qwen2.5:3b` already pulled.
- `claude_button.py` in `~/Desktop/Projects/elegooproject/` demonstrates working serial communication — use as reference for the serial layer in `core/serial_worker.py`.

## Phase-by-Phase Roadmap

**Rule: Do not start Phase N+1 until Phase N is fully working.**

### Phase 1 — Backend + Basic UI (Text Only)
**Goal:** ChatGPT-style text conversation streaming over WebSockets.
- Target files: `main.py`, `core/llm.py`, `templates/index.html`, `static/js/app.js`
- Dependencies: `fastapi uvicorn websockets httpx ollama`
- Validation: Text input streams tokens dynamically back to the UI.

### Phase 2 — Voice Input (Local STT)
**Goal:** Browser records audio, sends blob to backend, Whisper transcribes it.
- Target files: `core/stt.py`, updated backend endpoints, `static/js/app.js` (MediaRecorder)
- Dependencies: `faster-whisper sounddevice soundfile numpy`
- Validation: Speaking into the UI places editable text into the prompt field.

### Phase 3 — Arduino Hardware Bridge
**Goal:** Sync physical button presses and LCD status with the backend state machine.
- Target files: `core/serial_worker.py`, `arduino/lulu_assistant/lulu_assistant.ino`
- State machine strings sent via serial: `READY`, `LISTENING`, `PROCESSING`
- Validation: Physical button starts browser audio capture; LCD displays real-time state.

### Phase 4 — Voice Output (Local TTS)
**Goal:** Audio synthesis with hard interrupt.
- Target files: `core/tts.py`, UI "Stop" button handler
- Validation: Assistant response plays audio; clicking "Stop" drops the audio process cleanly.
