# storage.py
import json
from pathlib import Path
from print_request import PrintRequest

DATA_FILE = Path("data/requests.json")

def save_requests(requests: list):
    """
    Write atomically: write to a .tmp file then replace the real file.
    Each item is a dict produced by PrintRequest.to_dict()
    """
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in requests], f, ensure_ascii=False, indent=2)
    tmp.replace(DATA_FILE)

def load_requests() -> list:
    """
    Load requests from disk and return a list of PrintRequest instances.
    If file is missing or corrupt, returns an empty list (prints an error).
    """
    if not DATA_FILE.exists():
        return []
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        # raw should be a list of dicts
        return [PrintRequest.from_dict(item) for item in raw]
    except Exception as e:
        # don't crash the bot on corrupt file; log and return empty list
        print(f"[storage] failed to load {DATA_FILE}: {e}")
        return []