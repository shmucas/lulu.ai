import asyncio
import os
import tempfile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from core.llm import stream_response
from core import stt

app = FastAPI()
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
    await websocket.accept()
    history: list[dict] = []
    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            await websocket.send_json({"type": "status", "value": "PROCESSING"})

            try:
                full_response = ""
                async for token in stream_response(user_message, history):
                    full_response += token
                    await websocket.send_json({"type": "token", "value": token})

                history.append({"role": "user", "content": user_message})
                history.append({"role": "assistant", "content": full_response})
            except Exception as e:
                await websocket.send_json({"type": "token", "value": f"[Error: {e}]"})

            await websocket.send_json({"type": "done"})
            await websocket.send_json({"type": "status", "value": "READY"})

    except WebSocketDisconnect:
        pass
