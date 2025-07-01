import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st

logger = logging.getLogger(__name__)

class SessionManager:
    """Simple file-based session persistence"""

    def __init__(self, app_name: str = "whisperforge", expiry_days: int = 7):
        self.session_dir = Path.home() / f".{app_name}_sessions"
        self.session_file = self.session_dir / "session.json"
        self.expiry_days = expiry_days
        self.data = {
            "authenticated": False,
            "user_id": None,
            "user_email": None,
            "preferences": {},
            "current_page": "Transform",
            "pipeline_active": False,
            "created_at": None,
            "last_activity": None,
        }
        self._load()

    def _load(self):
        if self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if loaded.get("created_at"):
                    created = datetime.fromisoformat(loaded["created_at"])
                    if datetime.utcnow() - created > timedelta(days=self.expiry_days):
                        self.session_file.unlink()
                        return
                self.data.update(loaded)
                st.session_state.update(self.data)
            except Exception as e:
                logger.error(f"Session load failed: {e}")

    def _save(self):
        try:
            self.session_dir.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
        except Exception as e:
            logger.error(f"Session save failed: {e}")

    def authenticate_user(self, user_id: str, email: str) -> bool:
        self.data.update({
            "authenticated": True,
            "user_id": str(user_id),
            "user_email": email,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        })
        st.session_state.update(self.data)
        self._save()
        return True

    def logout(self) -> bool:
        for key in ["authenticated", "user_id", "user_email", "preferences", "current_page", "pipeline_active"]:
            self.data[key] = False if key == "authenticated" else None if key.endswith("id") else {}
        st.session_state.clear()
        self._save()
        return True

    def is_authenticated(self) -> bool:
        return bool(self.data.get("authenticated"))

    def get_user_id(self):
        return self.data.get("user_id")

    def get_user_email(self):
        return self.data.get("user_email")

    def set_preference(self, key: str, value):
        self.data.setdefault("preferences", {})[key] = value
        st.session_state.preferences = self.data["preferences"]
        self._save()
        return True

    def get_preference(self, key: str, default=None):
        return self.data.get("preferences", {}).get(key, default)

    def set_current_page(self, page: str):
        self.data["current_page"] = page
        st.session_state.current_page = page
        self._save()

    def get_current_page(self) -> str:
        return self.data.get("current_page", "Transform")

    def set_pipeline_active(self, active: bool):
        self.data["pipeline_active"] = active
        st.session_state.pipeline_active = active
        self._save()

    def is_pipeline_active(self) -> bool:
        return bool(self.data.get("pipeline_active"))

    def get_session_info(self):
        return {
            "user_email": self.get_user_email(),
            "session_file": str(self.session_file),
            "created_at": self.data.get("created_at"),
            "last_activity": self.data.get("last_activity"),
        }

def get_session_manager() -> SessionManager:
    if "_session_manager" not in st.session_state:
        st.session_state._session_manager = SessionManager()
    return st.session_state._session_manager
