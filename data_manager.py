"""
data_manager.py — Data Access Layer
=====================================
Defines an AbstractDataManager interface so the backend can be swapped
(JSON → SQLite → Google Sheets) without touching app.py.

Current implementation: atomic JSON file with backup-on-corruption.

Migration path
--------------
1. Create class SQLiteDataManager(AbstractDataManager) in sqlite_manager.py
2. Override all abstract methods using sqlite3
3. In app.py change:  from data_manager import JSONDataManager
                  to:  from sqlite_manager import SQLiteDataManager as JSONDataManager
"""

import copy
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import DATA_FILE, DEFAULT_DATA

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Abstract Interface
# ─────────────────────────────────────────────────────────────────────────────

class AbstractDataManager(ABC):
    """Minimal contract every backend must satisfy."""

    @abstractmethod
    def load(self) -> dict: ...

    @abstractmethod
    def save(self, data: dict) -> bool: ...

    # Categories
    @abstractmethod
    def get_categories(self, data: dict) -> list: ...

    @abstractmethod
    def add_category(self, data: dict, name: str, icon: str, color: str) -> tuple[dict, str]: ...

    @abstractmethod
    def update_category(self, data: dict, cat_id: str, name: str, icon: str, color: str) -> dict: ...

    @abstractmethod
    def delete_category(self, data: dict, cat_id: str) -> dict: ...

    # Scripts
    @abstractmethod
    def add_script(self, data: dict, cat_id: str, title: str, content: str, tags: list) -> tuple[dict, str]: ...

    @abstractmethod
    def update_script(self, data: dict, cat_id: str, scr_id: str, title: str, content: str, tags: list) -> dict: ...

    @abstractmethod
    def delete_script(self, data: dict, cat_id: str, scr_id: str) -> dict: ...

    # Utilities
    @abstractmethod
    def search_scripts(self, data: dict, query: str) -> list: ...

    @abstractmethod
    def get_stats(self, data: dict) -> dict: ...


# ─────────────────────────────────────────────────────────────────────────────
# JSON Implementation
# ─────────────────────────────────────────────────────────────────────────────

class JSONDataManager(AbstractDataManager):
    """
    Reads/writes a local data.json file.

    Atomic writes: data is first written to a .tmp file then renamed,
    so the main file is never left half-written if the process crashes.
    """

    def __init__(self, filepath: Path = DATA_FILE):
        self.filepath = filepath

    # ── I/O ──────────────────────────────────────────────────────────────────

    def load(self) -> dict:
        """Return data dict; creates defaults on first run; recovers on corruption."""
        if not self.filepath.exists():
            return self._initialise()
        try:
            with open(self.filepath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not self._is_valid(data):
                raise ValueError("Unexpected top-level structure.")
            return data
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            logger.warning("data.json unreadable (%s) — recovering.", exc)
            return self._recover()
        except Exception as exc:
            logger.error("Unexpected load error: %s", exc)
            return self._recover()

    def save(self, data: dict) -> bool:
        """Atomic write — returns True on success."""
        try:
            tmp = self.filepath.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
            tmp.rename(self.filepath)
            return True
        except Exception as exc:
            logger.error("Save failed: %s", exc)
            return False

    def _is_valid(self, data: object) -> bool:
        return isinstance(data, dict) and isinstance(data.get("categories"), list)

    def _initialise(self) -> dict:
        data = copy.deepcopy(DEFAULT_DATA)
        self.save(data)
        return data

    def _recover(self) -> dict:
        """Back up the broken file and re-initialise."""
        try:
            ts = int(datetime.now().timestamp())
            self.filepath.rename(self.filepath.with_suffix(f".bak_{ts}"))
            logger.info("Corrupted file backed up.")
        except Exception:
            pass
        return self._initialise()

    # ── Category operations ───────────────────────────────────────────────────

    def get_categories(self, data: dict) -> list:
        return data.get("categories", [])

    def add_category(self, data: dict, name: str, icon: str, color: str) -> tuple[dict, str]:
        """Add category; raises ValueError on duplicate name."""
        name = name.strip()
        if any(c["name"].lower() == name.lower() for c in data["categories"]):
            raise ValueError(f"La categoría '{name}' ya existe.")
        new_cat = {
            "id": f"cat_{uuid.uuid4().hex[:8]}",
            "name": name,
            "icon": icon,
            "color": color,
            "scripts": [],
        }
        data["categories"].append(new_cat)
        return data, new_cat["id"]

    def update_category(self, data: dict, cat_id: str, name: str, icon: str, color: str) -> dict:
        """Update category fields; raises ValueError / KeyError."""
        name = name.strip()
        for i, cat in enumerate(data["categories"]):
            if cat["id"] == cat_id:
                others = [c["name"].lower() for c in data["categories"] if c["id"] != cat_id]
                if name.lower() in others:
                    raise ValueError(f"El nombre '{name}' ya está en uso.")
                data["categories"][i].update({"name": name, "icon": icon, "color": color})
                return data
        raise KeyError(f"Categoría '{cat_id}' no encontrada.")

    def delete_category(self, data: dict, cat_id: str) -> dict:
        """Delete category and all its scripts."""
        original = len(data["categories"])
        data["categories"] = [c for c in data["categories"] if c["id"] != cat_id]
        if len(data["categories"]) == original:
            raise KeyError(f"Categoría '{cat_id}' no encontrada.")
        return data

    # ── Script operations ─────────────────────────────────────────────────────

    def add_script(self, data: dict, cat_id: str, title: str, content: str, tags: list) -> tuple[dict, str]:
        """Add script to a category; raises ValueError / KeyError."""
        cat = self._find_cat(data, cat_id)
        title = title.strip()
        content = content.strip()
        if any(s["title"].lower() == title.lower() for s in cat["scripts"]):
            raise ValueError(f"El script '{title}' ya existe en esta categoría.")
        now = datetime.now().isoformat()
        new_scr = {
            "id": f"scr_{uuid.uuid4().hex[:8]}",
            "title": title,
            "content": content,
            "tags": [t.strip() for t in tags if t.strip()],
            "created_at": now,
            "updated_at": now,
        }
        cat["scripts"].append(new_scr)
        return data, new_scr["id"]

    def update_script(
        self, data: dict, cat_id: str, scr_id: str,
        title: str, content: str, tags: list,
    ) -> dict:
        """Update script fields; raises ValueError / KeyError."""
        cat = self._find_cat(data, cat_id)
        title   = title.strip()
        content = content.strip()
        for i, scr in enumerate(cat["scripts"]):
            if scr["id"] == scr_id:
                others = [s["title"].lower() for s in cat["scripts"] if s["id"] != scr_id]
                if title.lower() in others:
                    raise ValueError(f"El título '{title}' ya existe en esta categoría.")
                cat["scripts"][i].update({
                    "title":      title,
                    "content":    content,
                    "tags":       [t.strip() for t in tags if t.strip()],
                    "updated_at": datetime.now().isoformat(),
                })
                return data
        raise KeyError(f"Script '{scr_id}' no encontrado.")

    def delete_script(self, data: dict, cat_id: str, scr_id: str) -> dict:
        """Remove a script from its category."""
        cat = self._find_cat(data, cat_id)
        original = len(cat["scripts"])
        cat["scripts"] = [s for s in cat["scripts"] if s["id"] != scr_id]
        if len(cat["scripts"]) == original:
            raise KeyError(f"Script '{scr_id}' no encontrado.")
        return data

    # ── Utilities ─────────────────────────────────────────────────────────────

    def search_scripts(self, data: dict, query: str) -> list:
        """
        Full-text search across title, content, and tags.
        Returns flat list of script dicts augmented with category metadata.
        """
        q = query.lower().strip()
        if not q:
            return []
        results = []
        for cat in data["categories"]:
            for scr in cat["scripts"]:
                haystack = " ".join([
                    scr["title"].lower(),
                    scr["content"].lower(),
                    " ".join(scr.get("tags", [])),
                ])
                if q in haystack:
                    results.append({
                        **scr,
                        "cat_id":    cat["id"],
                        "cat_name":  cat["name"],
                        "cat_icon":  cat["icon"],
                        "cat_color": cat.get("color", "#e05252"),
                    })
        return results

    def get_stats(self, data: dict) -> dict:
        cats = data.get("categories", [])
        return {
            "total_categories": len(cats),
            "total_scripts":    sum(len(c["scripts"]) for c in cats),
            "breakdown": [
                {
                    "name":  c["name"],
                    "icon":  c["icon"],
                    "color": c.get("color", "#e05252"),
                    "count": len(c["scripts"]),
                }
                for c in cats
            ],
        }

    # ── Private ───────────────────────────────────────────────────────────────

    def _find_cat(self, data: dict, cat_id: str) -> dict:
        cat = next((c for c in data["categories"] if c["id"] == cat_id), None)
        if cat is None:
            raise KeyError(f"Categoría '{cat_id}' no encontrada.")
        return cat
