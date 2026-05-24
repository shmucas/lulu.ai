# lulu.ai voice Assistant Project

A locally-hosted, privacy-first voice assistant with a ChatGPT-style browser UI called lulu.ai, Arduino physical controls, and an LCD status display. Runs entirely on your machine — no cloud, no API fees.

---

## What You're Actually Building

A web app that runs on your laptop (and later a Raspberry Pi 5) that lets you:
- Talk to an AI by pressing a physical button or clicking in the browser
- See a ChatGPT-style chat history in the browser
- Type and edit messages directly
- Hear responses spoken back via text-to-speech
- See status on the Arduino LCD: `READY → LISTENING → PROCESSING → READY`

```
[Arduino Button] → USB Serial → [FastAPI Backend]
                                      ↕
                              [Browser UI via WebSocket]
                                      ↕
                    [Whisper STT] → [Ollama LLM] → [Piper TTS]
                                      ↕
                    [LCD shows: READY / LISTENING / PROCESSING]
```

---

## Existing Starting Point

This project builds directly on top of the Claude Button project. Here's what's already built and working:

**Hardware (already wired and tested):**
- Elegoo UNO R3 connected via USB to Mac (`/dev/cu.usbmodem101` or `1101` — check with `ls /dev/cu.usb*`)
- Push button wired to **digital Pin 2** with `INPUT_PULLUP` (no resistor needed)
  - Pin 2 → left button leg
  - GND → right button leg
  - Toggle behavior needed: click once = start, click again = stop
- LCD1602 (16-pin, non-I2C) wired to Arduino:
  - LCD pin 1 (VSS) → GND
  - LCD pin 2 (VDD) → 5V
  - LCD pin 3 (V0) → potentiometer middle leg (contrast)
  - LCD pin 4 (RS) → Arduino pin 7
  - LCD pin 5 (RW) → GND
  - LCD pin 6 (E) → Arduino pin 8
  - LCD pins 7-10 → not connected
  - LCD pin 11 (D4) → Arduino pin 9
  - LCD pin 12 (D5) → Arduino pin 10
  - LCD pin 13 (D6) → Arduino pin 11
  - LCD pin 14 (D7) → Arduino pin 12
  - LCD pin 15 (A) → 5V via 220Ω resistor
  - LCD pin 16 (K) → GND
  - Potentiometer: left → GND, middle → LCD pin 3, right → 5V
  - 5V rail powered from Elegoo 5V pin
  - GND rail powered from Elegoo GND pin

**Software (already installed and working):**
- Python virtual environment at `~/claude-button/`
  - Activate: `source ~/claude-button/bin/activate`
  - Run script: `python3 claude_button.py` from `~/Desktop/Projects/elegooproject/`
- `pyserial` installed in the venv
- Ollama installed and running with `llama3.2` model pulled
- Existing `claude_button.py` script handles serial comms with Arduino

**Known Mac-specific quirks:**
- Serial port changes between sessions — always check with `ls /dev/cu.usb*`
- Arduino IDE Serial Monitor must be closed before running Python (port conflict)
- Virtual environment must be active — prompt shows `(claude-button)`
- Kill Ollama with `killall ollama`, start with `ollama serve`

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Backend | FastAPI | Async, WebSocket support, simple |
| Frontend | HTML + CSS + Vanilla JS | No framework needed, clean and fast |
| Real-time | WebSockets | Streaming responses, live status updates |
| STT | Faster Whisper | Fast, runs locally, works on Mac and Pi |
| LLM | Ollama + Qwen2.5 3B | Already installed, fast for short responses |
| TTS | Piper | Fast local TTS, no cloud needed |
| Hardware | Arduino UNO R3 + LCD1602 | Already built and working |
| Serial | pyserial | Already installed |

---

## UI Design

ChatGPT-style interface:
- Dark mode
- Scrollable chat history (user messages right, assistant messages left)
- Text input at the bottom — user can type or edit transcribed text before sending
- **Record button** in UI — click to start recording, click again to stop
- **Stop TTS button** — kills voice output mid-sentence
- Status indicator in UI matching LCD: `READY / LISTENING / PROCESSING`
- Responsive, clean, no clutter

---

## Roadmap

**Rule: Do not start Phase N+1 until Phase N is fully working.**

---

### Phase 1 — Backend + Basic UI (3–4 hrs)

**Goal:** ChatGPT-style text conversation in the browser. No voice, no Arduino yet.

**Backend:**
1. Set up FastAPI with WebSocket support
2. `/chat` endpoint receives user message, calls Ollama, streams response back
3. WebSocket for real-time response streaming to frontend

**Frontend:**
1. Clean dark-mode UI
2. Scrollable chat history
3. Text input + send button
4. Streaming response (words appear as they're generated)
5. Status indicator (READY / PROCESSING)

**Install:**
```bash
source ~/claude-button/bin/activate
pip3 install fastapi uvicorn websockets httpx
```

**Run:**
```bash
uvicorn main:app --reload --port 8000
```
Open `http://localhost:8000` in browser.

**Done when:** You can have a full text conversation with Ollama in the browser with streaming responses.

---

### Phase 2 — Voice Input (2–3 hrs)

**Goal:** Click record in UI, speak, click stop, transcribed text appears as your message.

**Steps:**
1. Install Faster Whisper: `pip3 install faster-whisper`
2. Install audio recording: `pip3 install sounddevice soundfile numpy`
3. Add record button to UI — toggle behavior (click start / click stop)
4. Backend records audio while recording is active
5. Whisper transcribes on stop
6. Transcribed text appears in the text input field (editable before sending)
7. User can edit transcription then hit send

**Done when:** You can speak, see your words appear (editable) in the input, and send them to Ollama.

---

### Phase 3 — Wire In Arduino (2–3 hrs)

**Goal:** Physical button on Arduino triggers the same record/stop flow as the UI button. LCD shows live status.

**Arduino sketch changes:**
- Toggle behavior: first press = send `START\n` over serial, second press = send `STOP\n`
- LCD displays status sent from Python:
  - `READY` → waiting for input
  - `LISTENING` → recording in progress
  - `PROCESSING` → Whisper + Ollama running
  - `READY` → back to waiting

**Python changes:**
- Serial listener runs in background thread
- `START` signal triggers same recording function as UI button
- `STOP` signal triggers same stop function
- Backend sends LCD status strings back to Arduino over serial

**Arduino LCD sketch additions:**
```cpp
if (Serial.available()) {
  String status = Serial.readStringUntil('\n');
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(status.substring(0, 16));
}
```

**Done when:** Arduino button and UI button both trigger recording identically, LCD shows correct status at each stage.

---

### Phase 4 — Voice Output (1–2 hrs)

**Goal:** Ollama response is spoken through speaker. Stop button kills audio mid-sentence.

**Steps:**
1. Install Piper TTS (follow piper-tts docs for Mac)
2. After Ollama generates response, pipe text through Piper
3. Play audio through USB speaker/mic combo
4. Stop TTS button in UI kills the audio subprocess immediately
5. LCD shows `READY` after TTS finishes

**Done when:** Full loop works — press button → speak → transcription appears → Ollama responds → response shown in UI → Piper speaks it → LCD shows READY.

---

## Start Commands

```bash
# Navigate to project
cd ~/Desktop/Projects/elegooproject

# Activate virtual environment
source ~/claude-button/bin/activate

# Start Ollama (if not running)
ollama serve

# Start the assistant
uvicorn main:app --reload --port 8000

# Open in browser
open http://localhost:8000
```

---

## Useful Debug Commands

```bash
# Find Arduino serial port
ls /dev/cu.usb*

# Check Ollama is running
ollama list

# Kill Ollama
killall ollama

# Check virtual environment is active
# Should show (claude-button) in prompt
```

---

## Known Issues / Gotchas

- **Port changes:** Arduino serial port changes between sessions. Always check with `ls /dev/cu.usb*` and update `PORT` in the script.
- **Port busy error:** Arduino IDE Serial Monitor must be closed before running Python.
- **Virtual env:** Always activate before running anything — `source ~/claude-button/bin/activate`.
- **Ollama response length:** Smaller models ignore character limits. Enforce truncation in Python, not in the prompt.
- **LCD contrast:** If LCD shows blank or squares, turn the potentiometer. Contrast pot middle leg must be in exact same breadboard row as LCD pin 3.
- **Button always firing:** Check no wires share a breadboard row with Pin 2 unintentionally. Use `INPUT_PULLUP` — button connects Pin 2 to GND, no resistor needed.

---

## After It Works: Where to Go Next

- **Move to Raspberry Pi 5** — same stack, same code, runs standalone without your laptop
- **Add conversation memory** — pass chat history to Ollama so it remembers context across turns
- **Wake word detection** — replace button with always-on wake word ("Hey Assistant") using Porcupine
- **Better TTS voice** — swap Piper voice models for a more natural sound
- **Keyboard shortcut** — trigger recording with a hotkey instead of clicking
