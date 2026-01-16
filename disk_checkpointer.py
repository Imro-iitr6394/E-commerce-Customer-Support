import os
import pickle
import json
from typing import Any
from langgraph.checkpoint.memory import InMemorySaver


class DiskBackedSaver(InMemorySaver):
    """In-memory checkpointer that persists state to disk.
    
    Extends LangGraph's InMemorySaver to automatically save and restore
    checkpoint state from a pickle file for durability across restarts.
    """

    def __init__(self, filename: str = "lg_checkpoint.pkl", *args: Any, **kwargs: Any):
        self.filename = filename
        super().__init__(*args, **kwargs)
        
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "rb") as f:
                    state = pickle.load(f)
                self.storage = state.get("storage", self.storage)
                self.writes = state.get("writes", self.writes)
                self.blobs = state.get("blobs", self.blobs)
            except Exception:
                pass

    def _persist(self) -> None:
        """Save checkpoint state to disk."""
        try:
            state = {"storage": self.storage, "writes": self.writes, "blobs": self.blobs}
            with open(self.filename + ".tmp", "wb") as f:
                pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(self.filename + ".tmp", self.filename)
            
            try:
                self._persist_json()
            except Exception:
                pass
        except Exception:
            pass

    def _persist_json(self) -> None:
        """Save a human-readable JSON snapshot of checkpoint state."""
        summary = {}
        try:
            for thread_id, ns_map in self.storage.items():
                summary.setdefault(thread_id, {})
                for ns, checkpoints in ns_map.items():
                    summary[thread_id].setdefault(ns, {})
                    for cid, (checkpoint_b, metadata_b, parent) in checkpoints.items():
                        try:
                            chk = self.serde.loads_typed(checkpoint_b)
                        except Exception:
                            try:
                                chk = checkpoint_b
                            except Exception:
                                chk = str(checkpoint_b)

                        try:
                            meta = self.serde.loads_typed(metadata_b)
                        except Exception:
                            meta = str(metadata_b)

                        def _safe(o):
                            try:
                                json.dumps(o)
                                return o
                            except Exception:
                                return str(o)

                        summary[thread_id][ns][cid] = {
                            "checkpoint": _safe(chk),
                            "metadata": _safe(meta),
                            "parent": parent
                        }

            with open(os.path.splitext(self.filename)[0] + ".json.tmp", "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            os.replace(os.path.splitext(self.filename)[0] + ".json.tmp", os.path.splitext(self.filename)[0] + ".json")
        except Exception:
            pass

    def put(self, config, checkpoint, metadata, new_versions):
        res = super().put(config, checkpoint, metadata, new_versions)
        self._persist()
        return res

    def put_writes(self, config, writes, task_id: str, task_path: str = ""):
        res = super().put_writes(config, writes, task_id, task_path)
        self._persist()
        return res

    def delete_thread(self, thread_id: str) -> None:
        res = super().delete_thread(thread_id)
        self._persist()
        return res
