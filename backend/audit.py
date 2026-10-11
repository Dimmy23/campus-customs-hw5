from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from models import AuditEvent


AUDIT_PATH = Path(__file__).resolve().parents[1] / "output" / "audit_trail.json"
_LOCK = Lock()


def append_event(event: AuditEvent) -> None:
    """Append an audit event without exposing secrets or replacing prior runs."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        try:
            history = json.loads(AUDIT_PATH.read_text(encoding="utf-8")) if AUDIT_PATH.exists() else []
            if not isinstance(history, list):
                history = []
        except (OSError, json.JSONDecodeError):
            history = []
        history.append(event.model_dump(mode="json"))
        AUDIT_PATH.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")


def audit(run_id: str, step: int, agent: str, event: str, **kwargs: object) -> None:
    append_event(AuditEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        run_id=run_id, step=step, agent=agent, event=event, **kwargs
    ))
