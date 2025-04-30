# localfile "MCP" layer
# mcp_store.py

import json, pathlib, uuid
from typing import List, Dict

WARDROBE_NDJSON = pathlib.Path("closet.ndjson")

def add_item(item: Dict):
    """Write (or overwrite) a garment in the local wardrobe file."""
    item = item.copy()
    item.setdefault("id", str(uuid.uuid4()))
    WARDROBE_NDJSON.parent.mkdir(parents=True, exist_ok=True)

    # read all, replace if id already exists
    records: List[Dict] = load_wardrobe()
    records = [r for r in records if r["id"] != item["id"]] + [item]
    with WARDROBE_NDJSON.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def load_wardrobe() -> List[Dict]:
    if not WARDROBE_NDJSON.exists():
        return []
    with WARDROBE_NDJSON.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]