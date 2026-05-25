from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from core.llm import stream_response

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("templates/index.html")


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
