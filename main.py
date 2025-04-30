# main.py ─ FastAPI “Wardrobe Stylist” back-end
# ───────────────────────────────────────────────
import os, json, asyncio
from pathlib import Path
from typing import List, Dict, Set

from fastapi import (
    FastAPI, UploadFile, File, BackgroundTasks,
    WebSocket, WebSocketDisconnect, HTTPException, Query
)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from mcp_store       import load_wardrobe
from clothing_vision import describe_image        # single-image helper
from stylist_agent   import stylist               # the LLM agent

load_dotenv("ai_hackathon.env", override=True)

# ─── Paths ──────────────────────────────────────
APP_DIR   = Path(__file__).parent
IMG_DIR   = APP_DIR / "User Weardrobe"            # auto-create if missing
META_FILE = APP_DIR / "closet.ndjson"
IMG_DIR.mkdir(parents=True, exist_ok=True)

# ─── FastAPI set-up ─────────────────────────────
app = FastAPI()
app.mount("/static",  StaticFiles(directory=APP_DIR / "static"),  name="static")
app.mount("/images",  StaticFiles(directory=IMG_DIR),             name="images")

# ─── Web-socket registry ────────────────────────
active_ws: Set[WebSocket] = set()

async def _broadcast(payload: Dict):
    """Send a JSON dict to all open web-socket clients."""
    if not active_ws:      # no one listening
        return
    dead = set()
    data = json.dumps(payload)
    for ws in active_ws:
        try:
            await ws.send_text(data)
        except WebSocketDisconnect:
            dead.add(ws)
    active_ws.difference_update(dead)

# ─── Vision helper ──────────────────────────────
def run_vision(img_names: List[str]):
    """Describe new images and append them to `closet.ndjson`."""
    if not img_names:
        return
    print("▶ vision: processing", img_names)

    seen = {r["source_image"] for r in load_wardrobe()}
    processed = 0

    with META_FILE.open("a", encoding="utf-8") as out:
        for name in img_names:
            if name in seen:
                continue
            try:
                rec = describe_image(IMG_DIR / name)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                processed += 1
            except Exception as e:
                print("⚠️", e)

    msg = f"✓ vision done – wrote {processed} new records"
    print(msg)

    # notify all web-socket clients once work is finished
    asyncio.run(_broadcast({"system": "✅ Finished processing – ask me what to wear!"}))

# ─── End-points ─────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    html = (APP_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)

@app.get("/wardrobe")
async def wardrobe():
    return load_wardrobe()

@app.post("/upload")
async def upload(
        files: List[UploadFile] = File(...),
        auto : bool             = Query(False, description="run vision immediately"),
        bg   : BackgroundTasks  = None):
    saved = []
    for f in files:
        dest = IMG_DIR / f.filename
        with dest.open("wb") as fd:
            fd.write(await f.read())
        saved.append(f.filename)

    if auto and bg:
        bg.add_task(run_vision, saved)

    return {"status": "ok", "saved": saved, "processed": auto}

@app.post("/process")
async def process(bg: BackgroundTasks):
    wardrobe_names = {r["source_image"] for r in load_wardrobe()}
    todo = [p.name for p in IMG_DIR.iterdir()
            if p.is_file() and p.name not in wardrobe_names]

    if not todo:
        return {"status": "nothing_to_do"}

    bg.add_task(run_vision, todo)
    return {"status": "started", "files": todo}

@app.get("/image/{name}")
async def get_image(name: str):
    file = IMG_DIR / name
    if not file.exists():
        raise HTTPException(404)
    return FileResponse(file)

# ─── Web-socket chat ────────────────────────────
@app.websocket("/ws")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    active_ws.add(ws)

    # greet client immediately
    await ws.send_text(json.dumps({"system": "👋 Stylist ready – upload garments or ask away!"}))

    try:
        while True:
            question = await ws.receive_text()

            # ensure wardrobe exists
            if not META_FILE.exists() or not load_wardrobe():
                await ws.send_text(json.dumps({
                    "system": "👗 Upload garments and click *Process wardrobe* first."
                }))
                continue

            reply  = stylist.invoke({"input": question})
            await ws.send_text(reply["output"])             # already JSON 👍

    except WebSocketDisconnect:
        pass
    finally:
        active_ws.discard(ws)