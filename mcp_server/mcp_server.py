"""Read-only Campus Customs MCP server.

The server is intentionally not started by this file during HW5 Problem 3.
The tools read only from the copied database at ../data/campus_customs_new.db.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastmcp import FastMCP


HERE = Path(__file__).resolve().parent
DATABASE_PATH = HERE.parent / "data" / "campus_customs_new.db"

mcp = FastMCP("campus-customs")


def _connect() -> sqlite3.Connection:
    """Open the required database without creating or modifying it."""
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(f"Campus Customs database not found: {DATABASE_PATH}")
    connection = sqlite3.connect(f"file:{DATABASE_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _rows(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


@mcp.tool
def list_open_tickets() -> list[dict[str, Any]]:
    """List every ticket whose database status is exactly ``open``."""
    with _connect() as connection:
        cursor = connection.execute(
            """
            SELECT id, type, requester, subject, sku, size, qty,
                   lease_id, invoice_id, status, notes, created_at
            FROM tickets
            WHERE status = ?
            ORDER BY created_at, id
            """,
            ("open",),
        )
        return _rows(cursor)


@mcp.tool
def get_ticket_context(ticket_id: int) -> dict[str, Any]:
    """Return a ticket and its linked invoice, lease, product, and pricing records.

    Missing relationships are returned as null; no values are inferred.
    """
    with _connect() as connection:
        ticket_cursor = connection.execute(
            "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
        )
        ticket = ticket_cursor.fetchone()
        if ticket is None:
            return {"ticket": None, "invoice": None, "lease": None, "inventory": [], "pricing": None}

        ticket_data = dict(ticket)
        invoice = None
        if ticket_data["invoice_id"] is not None:
            row = connection.execute(
                "SELECT * FROM invoices WHERE id = ?", (ticket_data["invoice_id"],)
            ).fetchone()
            invoice = dict(row) if row else None

        lease = None
        if ticket_data["lease_id"] is not None:
            row = connection.execute(
                "SELECT * FROM leases WHERE id = ?", (ticket_data["lease_id"],)
            ).fetchone()
            lease = dict(row) if row else None

        inventory: list[dict[str, Any]] = []
        pricing = None
        if ticket_data["sku"] is not None:
            inventory = _rows(
                connection.execute(
                    "SELECT * FROM inventory WHERE sku = ? ORDER BY size",
                    (ticket_data["sku"],),
                )
            )
            row = connection.execute(
                "SELECT * FROM pricing WHERE sku = ?", (ticket_data["sku"],)
            ).fetchone()
            pricing = dict(row) if row else None

        return {
            "ticket": ticket_data,
            "invoice": invoice,
            "lease": lease,
            "inventory": inventory,
            "pricing": pricing,
        }


@mcp.tool
def check_inventory(sku: str, size: str | None = None) -> list[dict[str, Any]]:
    """Look up database inventory for a SKU, optionally limited to one size."""
    query = "SELECT * FROM inventory WHERE sku = ?"
    parameters: list[str] = [sku]
    if size is not None:
        query += " AND size = ?"
        parameters.append(size)
    query += " ORDER BY size"

    with _connect() as connection:
        return _rows(connection.execute(query, parameters))


@mcp.tool
def get_vendor_details(vendor_id: int) -> dict[str, Any] | None:
    """Return one vendor record by its database ID, or null when it is absent."""
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM vendors WHERE id = ?", (vendor_id,)
        ).fetchone()
        return dict(row) if row else None


if __name__ == "__main__":
    mcp.run()
