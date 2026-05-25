import queue
import threading
import time

import serial
import serial.tools.list_ports

command_queue: queue.Queue = queue.Queue()

_conn: serial.Serial | None = None
_lock = threading.Lock()


def find_port() -> str | None:
    for p in serial.tools.list_ports.comports():
        if "usbmodem" in p.device or "usbserial" in p.device:
            return p.device
    return None


def send_status(status: str) -> None:
    with _lock:
        if _conn and _conn.is_open:
            try:
                _conn.write((status + "\n").encode())
            except Exception:
                pass


def _run(port: str, baud: int) -> None:
    global _conn
    try:
        _conn = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # wait for Arduino reset after connection
        while True:
            line = _conn.readline().decode(errors="ignore").strip()
            if line in ("START", "STOP"):
                command_queue.put(line)
    except Exception as e:
        print(f"[serial] error: {e}")


def start(baud: int = 9600) -> None:
    port = find_port()
    if not port:
        print("[serial] No Arduino found — hardware button disabled")
        return
    print(f"[serial] Connected to {port}")
    threading.Thread(target=_run, args=(port, baud), daemon=True).start()
