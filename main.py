import asyncio
import os
import queue
import tempfile

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from core.llm import stream_response
from core import stt, serial_worker, tts

active_connections: set[WebSocket] = set()
_tts_task: asyncio.Task | None = None


async def broadcast(data: dict) -> None:
    for ws in list(active_connections):
        try:
            await ws.send_json(data)
        except Exception:
            active_connections.discard(ws)


async def _speak_async(text: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, tts.speak, text)


def _open_browser() -> None:
    import subprocess
    subprocess.Popen(["open", "-a", "Google Chrome", "http://localhost:7001"])


async def serial_relay() -> None:
    while True:
        try:
            cmd = serial_worker.command_queue.get_nowait()
            if cmd == "START":
                _open_browser()
                serial_worker.send_status("listening...")
                await broadcast({"type": "record_start"})
            elif cmd == "STOP":
                serial_worker.send_status("processing...")
                await broadcast({"type": "record_stop"})
        except queue.Empty:
            pass
        await asyncio.sleep(0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    serial_worker.start()
    asyncio.create_task(serial_relay())
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("templates/index.html")


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    suffix = ".webm" if "webm" in (file.content_type or "") else ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, stt.transcribe, tmp_path)
    finally:
        os.unlink(tmp_path)
    return JSONResponse({"text": text})


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    global _tts_task
    await websocket.accept()
    active_connections.add(websocket)
    history: list[dict] = []
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "stop_tts":
                tts.stop()
                if _tts_task and not _tts_task.done():
                    _tts_task.cancel()
                await websocket.send_json({"type": "status", "value": "lulu.ai is ready:"})
                serial_worker.send_status("lulu.ai is ready:")
                continue

            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            # Stop any ongoing TTS before processing new message
            tts.stop()
            if _tts_task and not _tts_task.done():
                _tts_task.cancel()

            await websocket.send_json({"type": "status", "value": "lulu.ai is processing..."})
            serial_worker.send_status("lulu.ai is processing...")

            try:
                full_response = ""
                async for token in stream_response(user_message, history):
                    full_response += token
                    await websocket.send_json({"type": "token", "value": token})

                history.append({"role": "user", "content": user_message})
                history.append({"role": "assistant", "content": full_response})
            except Exception as e:
                await websocket.send_json({"type": "token", "value": f"[Error: {e}]"})
                full_response = ""

            await websocket.send_json({"type": "done"})

            if full_response:
                await websocket.send_json({"type": "tts_start"})
                serial_worker.send_status("speaking...")

                def on_tts_done(task: asyncio.Task) -> None:
                    async def finish() -> None:
                        try:
                            await websocket.send_json({"type": "tts_end"})
                            await websocket.send_json({"type": "status", "value": "lulu.ai is ready:"})
                            serial_worker.send_status("lulu.ai is ready:")
                        except Exception:
                            pass
                    asyncio.create_task(finish())

                _tts_task = asyncio.create_task(_speak_async(full_response))
                _tts_task.add_done_callback(on_tts_done)
            else:
                await websocket.send_json({"type": "status", "value": "lulu.ai is ready:"})
                serial_worker.send_status("lulu.ai is ready:")

    except WebSocketDisconnect:
        active_connections.discard(websocket)
