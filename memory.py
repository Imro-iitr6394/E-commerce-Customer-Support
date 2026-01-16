import json
import os
from datetime import datetime

MEMORY_FILE = "memory.json"


def load_memory(thread_id: str, limit: int = 20):
    """Load the last `limit` messages for a thread from disk."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    items = data.get(thread_id, [])
    return items[-limit:]


def append_memory(thread_id: str, role: str, content: str):
    """Append a message to thread memory on disk."""
    data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    data.setdefault(thread_id, []).append({
        "role": role,
        "content": content,
        "ts": datetime.utcnow().isoformat()
    })

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_thread_messages(thread_id: str, messages: list):
    """Overwrite stored messages for a thread with the provided list."""
    data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    normalized = []
    for m in messages:
        normalized.append({
            "role": m.get("role", "user"),
            "content": m.get("content", ""),
            "ts": m.get("ts") or datetime.utcnow().isoformat()
        })

    data[thread_id] = normalized

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
