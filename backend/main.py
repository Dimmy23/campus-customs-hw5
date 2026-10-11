from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from audit import AUDIT_PATH, audit
from models import TeamReport
from team import run_team


BACKEND_DIR = Path(__file__).resolve().parent
HW5_DIR = BACKEND_DIR.parent
DATA_DIR = HW5_DIR / "data"
DB_PATH = DATA_DIR / "campus_customs_new.db"
ORIGINAL_DB_PATH = DATA_DIR / "campus_customs.db"

app = FastAPI(title="Campus Customs Agent Desk API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunTicketRequest(BaseModel):
    objective: str = Field(default="Review this open ticket and prepare a safe recommendation.", max_length=1000)


class ApprovalRequest(BaseModel):
    kind: str = Field(min_length=1, max_length=80)
    ref_id: int | None = None
    amount: float = Field(gt=0)
    account: str = Field(min_length=1, max_length=80)
    approved_by: str = Field(min_length=1, max_length=160)


def _connect() -> sqlite3.Connection:
    if not DB_PATH.is_file():
        raise HTTPException(status_code=500, detail="Working database is missing.")
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@app.get("/api/tickets")
def tickets() -> list[dict]:
    """Return the three ticket records and their current stored status."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, type, requester, subject, status, created_at FROM tickets ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


@app.post("/api/tickets/{ticket_id}/run", response_model=TeamReport)
async def run_ticket(ticket_id: int, request: RunTicketRequest) -> TeamReport:
    """Run the agent team for one existing ticket."""
    with _connect() as connection:
        exists = connection.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} was not found.")
    report = await run_team(ticket_id, request.objective)
    with _connect() as connection:
        connection.execute("UPDATE tickets SET status = ? WHERE id = ?", ("resolved", ticket_id))
        connection.commit()
    return report


@app.get("/api/events")
def recent_events(limit: int = 50) -> dict:
    """Return recent audit events plus a compact per-agent summary for the board."""
    limit = min(max(limit, 1), 200)
    try:
        history = json.loads(AUDIT_PATH.read_text(encoding="utf-8")) if AUDIT_PATH.exists() else []
    except (OSError, json.JSONDecodeError):
        history = []
    if not isinstance(history, list):
        history = []
    recent = history[-limit:]
    by_agent: dict[str, dict] = {}
    for event in recent:
        agent = event.get("agent", "unknown")
        item = by_agent.setdefault(agent, {"agent": agent, "said": [], "tools_used": []})
        if event.get("event") == "agent_result" and event.get("output_summary"):
            item["said"].append(event["output_summary"])
        if event.get("event") == "mcp_call" and event.get("tool_name"):
            if event["tool_name"] not in item["tools_used"]:
                item["tools_used"].append(event["tool_name"])
    return {"events": recent, "by_agent": list(by_agent.values())}


@app.post("/api/approve")
def approve_payment_or_purchase(request: ApprovalRequest) -> dict:
    """Apply a human-approved cash outflow and record it in payments."""
    with _connect() as connection:
        account = connection.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = ?",
            (request.account,),
        ).fetchone()
        if account is None:
            raise HTTPException(status_code=404, detail=f"Cash account {request.account!r} was not found.")
        if account["balance"] < request.amount:
            raise HTTPException(status_code=409, detail="The cash account does not have enough balance.")
        connection.execute(
            "UPDATE cash_accounts SET balance = balance - ? WHERE name = ?",
            (request.amount, request.account),
        )
        cursor = connection.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, datetime('now'), ?)",
            (request.kind, request.ref_id, request.amount, request.account, request.approved_by),
        )
        connection.commit()
        result = dict(connection.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = ?", (request.account,)
        ).fetchone())
        result.update({"payment_id": cursor.lastrowid, "kind": request.kind, "ref_id": request.ref_id,
                       "amount": request.amount, "approved_by": request.approved_by})
        audit(uuid.uuid4().hex, 1, "boss", "team_complete", output_summary=f"Human approval recorded: payment {cursor.lastrowid}")
        return result


@app.get("/api/cash")
def current_cash() -> dict:
    """Return the current checking-account record."""
    with _connect() as connection:
        row = connection.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = ?", ("checking",)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Checking account was not found.")
        return dict(row)


@app.post("/api/reset")
def reset_database() -> dict:
    """Restore the working database byte-for-byte from the original database."""
    if not ORIGINAL_DB_PATH.is_file():
        raise HTTPException(status_code=500, detail="Original database is missing.")
    shutil.copy2(ORIGINAL_DB_PATH, DB_PATH)
    audit(uuid.uuid4().hex, 1, "boss", "team_complete", output_summary="Working database reset from original")
    return {"reset": True, "database": str(DB_PATH)}
