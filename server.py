from __future__ import annotations

import asyncio
import json
import re
import time
from collections import deque
from pathlib import Path
from typing import Deque, Dict, Optional, Set

import requests
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# =========================
# Config
# =========================
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "messages.jsonl"

MAX_MESSAGES = 2000

# =========================
# App
# =========================
app = FastAPI()

# Static (chemin absolu => stable avec systemd)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Websocket clients
clients: Set[WebSocket] = set()

# Historique en mémoire (max 2000)
message_history: Deque[Dict] = deque(maxlen=MAX_MESSAGES)

# Lock async pour l'historique
history_lock = asyncio.Lock()


# =========================
# Utils
# =========================
def load_history() -> None:
    """Charge les N dernières lignes du fichier JSONL dans la mémoire (max 2000)."""
    if not HISTORY_FILE.exists():
        return
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines[-MAX_MESSAGES:]:
            try:
                message_history.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        # Ne jamais bloquer le serveur si le fichier est corrompu
        pass


def geocode(address: str) -> tuple[Optional[float], Optional[float]]:
    """Géocodage via Nominatim (OpenStreetMap)."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "POCSAG-Monitor/1.0"},
            timeout=10,
        )
        data = r.json()
        if not data:
            return None, None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None, None


async def append_history(payload: Dict) -> None:
    """Ajoute à l'historique mémoire + append fichier JSONL."""
    async with history_lock:
        message_history.append(payload)
        try:
            with HISTORY_FILE.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception:
            # On ne veut pas casser le live si le disque a un souci
            pass


async def broadcast(payload: Dict) -> None:
    """Envoie à tous les WS connectés. Retire les WS morts."""
    dead: list[WebSocket] = []
    for ws in list(clients):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)


# Charger l'historique au démarrage
load_history()

# =========================
# Routes
# =========================
@app.get("/")
def home():
    # Sert l'interface directement sur /
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/messages")
def get_messages(limit: int = Query(2000, ge=1, le=MAX_MESSAGES)):
    """Retourne les derniers messages (max 2000)."""
    items = list(message_history)[-limit:]
    return {"messages": items}


@app.post("/add")
async def add_message(msg: str = Query(...)):
    # ✅ Filtre : supprimer uniquement Function: 0
    if re.search(r"\bFunction:\s*0\b", msg):
        return JSONResponse({"status": "ignored_function_0"})

    # extraction RIC
    ric_match = re.search(r"Address:\s*(\d+)", msg)
    ric = ric_match.group(1) if ric_match else "?"

    # extraction adresse (après le dernier /)
    address = None
    if "/" in msg:
        address = msg.split("/")[-1].strip()

    lat = lon = None
    if address:
        lat, lon = geocode(address)

    payload = {
        "timestamp": int(time.time() * 1000),  # ms, stable multi-clients
        "ric": ric,
        "message": msg,
        "lat": lat,
        "lon": lon,
    }

    # Historique + fichier
    await append_history(payload)

    # Broadcast WS
    await broadcast(payload)

    return JSONResponse({"status": "ok"})


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            # On n'a pas besoin du contenu côté client, mais on garde la connexion vivante
            await ws.receive_text()
    except WebSocketDisconnect:
        clients.discard(ws)
    except Exception:
        clients.discard(ws)
