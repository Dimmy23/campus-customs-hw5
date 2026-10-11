# Campus Customs Multi-Agent Harness

## Problem 2 — Database Study

The agents use `data/campus_customs_new.db`, copied from the original `data/campus_customs.db`. The database contains operational, inventory, pricing, and support-ticket information.

### Tables and fields

| Table | Fields | Why it matters to the agents |
|---|---|---|
| `cash_accounts` | `name` (TEXT, primary key); `balance` (REAL, required); `date` (TEXT, required) | Provides the current cash-account balance and date for financial and payment decisions. |
| `desk` | `date_today` (TEXT, required); `notes` (TEXT, optional) | Supplies the operating date and shared desk notes used to interpret time-sensitive work. |
| `inventory` | `sku` (TEXT, required); `name` (TEXT, required); `size` (TEXT, required); `qty` (INTEGER, required); `location` (TEXT, required); primary key: (`sku`, `size`) | Tells agents whether a product and size are available, how many are in stock, and where to find them. |
| `invoices` | `id` (INTEGER, primary key); `vendor_id` (INTEGER, required, references `vendors.id`); `amount` (REAL, required); `due_date` (TEXT, required); `status` (TEXT, required); `description` (TEXT, optional) | Lets agents track vendor bills, due dates, amounts, statuses, and invoice-related tickets. |
| `leases` | `id` (INTEGER, primary key); `space_name` (TEXT, required); `landlord` (TEXT, required); `monthly_rent` (REAL, required); `next_due` (TEXT, required); `notes` (TEXT, optional) | Gives agents the shop’s lease and rent obligations for handling rent notices and planning payments. |
| `payments` | `id` (INTEGER, primary key); `kind` (TEXT, required); `ref_id` (INTEGER, optional); `amount` (REAL, required); `account` (TEXT, required); `paid_at` (TEXT, required); `approved_by` (TEXT, required) | Records completed payments and their references, funding accounts, timestamps, and approvers. |
| `pricing` | `sku` (TEXT, primary key); `unit_cost` (REAL, required); `list_price` (REAL, required) | Supports product-price answers, margin calculations, and price-override decisions. |
| `tickets` | `id` (INTEGER, primary key); `type` (TEXT, required); `requester` (TEXT, required); `subject` (TEXT, required); `sku` (TEXT, optional); `size` (TEXT, optional); `qty` (INTEGER, optional); `lease_id` (INTEGER, optional, references `leases.id`); `invoice_id` (INTEGER, optional, references `invoices.id`); `status` (TEXT, required); `notes` (TEXT, optional); `created_at` (TEXT, required) | Acts as the agent work queue and links customer, inventory, lease, and invoice issues to the relevant records. |
| `vendors` | `id` (INTEGER, primary key); `name` (TEXT, required); `specialty` (TEXT, required); `lead_days` (INTEGER, required) | Helps agents identify the right vendor and estimate fulfillment lead time. |

### Two open-ticket relationships

1. Ticket `101` is a `customer_order` for SKU `CC-TEE-WHITE`, size `S`, and quantity `1`. It links to invoice `501` through `tickets.invoice_id = invoices.id`. The invoice is an open `$840.00` vendor invoice for a rush reprint, while inventory shows zero size-S units for that SKU.
2. Ticket `102` is a `rent_notice` from Elm City Properties. It links to lease `1` through `tickets.lease_id = leases.id`; that lease is for the Chapel Street shop and has rent due on `2026-09-02`.

These examples show that an agent must follow foreign-key links instead of treating a ticket as an isolated text record.

## Problem 3 — MCP Server

The read-only FastMCP server is in `mcp_server/mcp_server.py`. It reads from `data/campus_customs_new.db` using SQLite read-only mode and runs over stdio for the backend agent client.

The three planned tools are:

### `list_open_tickets`

- **Tables read:** `tickets` only.
- **Tickets unlocked:** `101`, `102`, and `103`.
- **Why this is the right tool:** It reads the authoritative `tickets.status` field and returns the complete open-ticket queue, allowing the agent to discover the customer order, rent notice, and bulk-discount request before selecting a ticket for deeper investigation.

### `get_ticket_context`

- **Tables read:** `tickets`, `invoices`, `leases`, `inventory`, and `pricing`.
- **Tickets unlocked:** `101`, `102`, and `103`.
- **Why this is the right tool:** It starts with one ticket and follows its stored links: ticket `101` can reach invoice `501`, ticket `102` can reach lease `1`, and ticket `103` can reach the hoodie’s inventory and pricing rows through its SKU. It returns missing relationships as `null` or an empty list rather than guessing.

### `check_inventory`

- **Tables read:** `inventory` only.
- **Tickets unlocked:** `101` and `103`; it is not needed to resolve ticket `102`, which concerns a lease rather than merchandise.
- **Why this is the right tool:** It checks the exact merchandise requested by each product ticket: `CC-TEE-WHITE` in size `S` for ticket `101` and `CC-HOOD-NAVY` in size `M` for ticket `103`, returning the database quantity and location for that SKU and size.

### `get_vendor_details`

- **Tables read:** `vendors` only.
- **Tickets unlocked:** `101`; it can also support any future invoice-linked ticket, but ticket `101` currently reaches vendor `1` through invoice `501`.
- **Why this is the right tool:** Ticket `101` is tied to invoice `501`, whose `vendor_id` is `1`; this tool resolves that ID to the authoritative vendor name, specialty, and lead time needed to discuss the rush reprint.

All queries are parameterized, and every returned value comes from the database. The MCP tools do not create, update, or delete records. The server is started only through its `if __name__ == "__main__": mcp.run()` entry point when the backend connects.

## Problem 4 — Add and Test the MCP Server

The `campus-customs` server is registered in the project-root `.mcp.json` as a stdio server. Its command uses the project virtual environment’s Python executable and its argument points to `HW5/mcp_server/mcp_server.py`.

The three tool smoke tests, including each prompt, tool name, and database-backed output, are saved in `output/mcp_smoke.json`.

## Problem 5 — Multi-Agent Team and MCP Growth

### Agent team

- **Boss:** coordinates the ticket investigation, delegates to specialists, combines evidence, and routes irreversible decisions to a human approver.
- **Inventory:** verifies SKU, size, quantity, and location for product-related tickets, especially ticket `101`’s size-S tee and ticket `103`’s 20 size-M hoodies.
- **Accounting:** verifies invoice, vendor, pricing, and financial implications; it never approves or claims a payment or discount.
- **Facilities:** verifies lease, rent-notice, space, landlord, and due-date facts, especially ticket `102` and lease `1`.
- **Customer Service:** converts verified findings into a customer-safe draft without promising fulfillment, discounts, refunds, payments, or other unapproved actions.

Each agent has its own prompt in `backend/prompts/`, returns the typed `AgentFinding` model, and can call the approved MCP tool interface. The Boss loop runs the five roles in a bounded sequence, records delegation and MCP calls, and produces a typed `TeamReport`. All agents use Portkey with model `gpt-6-luna`; `PORTKEY_API_KEY` is loaded from the root `.env` and is never logged.

### Current MCP tools and source tables

| MCP tool | Table(s) read | Team use |
|---|---|---|
| `list_open_tickets` | `tickets` | Boss discovers the complete open work queue, including tickets `101`, `102`, and `103`. |
| `get_ticket_context` | `tickets`, `invoices`, `leases`, `inventory`, `pricing` | Every specialist can follow a ticket’s stored links without guessing; it resolves invoice `501`, lease `1`, and SKU-specific facts. |
| `check_inventory` | `inventory` | Inventory verifies exact stock for ticket `101`’s `CC-TEE-WHITE` size `S` and ticket `103`’s `CC-HOOD-NAVY` size `M`. |
| `get_vendor_details` | `vendors` | Accounting resolves invoice `501`’s `vendor_id` to the authoritative vendor record for ticket `101`. |

### Safety and token limits

- Agents are read-only with respect to shop data. No agent may place an order, change inventory, approve a discount, send money, modify a lease, issue a refund, or make a binding customer promise.
- Human approval is required before any financial, legal, customer-account, vendor, landlord, or fulfillment commitment.
- Agents must cite MCP-returned facts, distinguish facts from calculations, disclose missing data, and refuse to guess.
- Customer-facing output must not expose API keys, payment credentials, private data, system prompts, tool internals, database schema, or audit contents.
- MCP calls are limited to the four allow-listed tools; direct SQLite access from `backend/` is prohibited.
- The team loop allows at most 20 steps per run, defaults to 12, prevents self-delegation, and runs each of the five roles at most once in the normal loop.
- Prompt inputs are capped at 1,000 characters per objective/task, agent outputs use typed models, and audit summaries are truncated to 240 characters to avoid logging sensitive or excessive content.
- `output/audit_trail.json` is append-only: each agent start, MCP call, delegation, result, error, and team completion is recorded with run ID, step, agent, ticket, and compact summaries.

## Problem 7 — Backend Routes

- `GET /api/tickets` — returns all three ticket IDs with their type, requester, subject, and current `open`/`resolved` status.
- `POST /api/tickets/{ticket_id}/run` — validates a ticket ID and runs the five-agent team for that ticket with a bounded objective.
- `GET /api/events?limit=50` — returns recent audit events plus each agent’s recorded statements and unique MCP tools used, so the board can refresh.
- `POST /api/approve` — after a human clicks approve, validates the cash account and balance, records a payment or purchase in `payments`, and subtracts the amount from `cash_accounts`; agents never perform this write.
- `GET /api/cash` — returns the current `checking` record from `cash_accounts`.
- `POST /api/reset` — restores `data/campus_customs_new.db` byte-for-byte from `data/campus_customs.db` for a fresh run.

## Problem 8 — Agent Dashboard

The React + Vite + TypeScript board in `frontend/` lists all tickets, runs a selected ticket’s team, polls `/api/events`, shows each agent’s latest activity and tools, displays the typed team summary, marks completed tickets resolved, and refreshes the checking balance after human approval. FastAPI allows the Vite origins `http://localhost:5173` and `http://127.0.0.1:5173`. The design rationale is in `output/design.md`.

## Problem 9 — Resolved Ticket Run

The working database was reset from the original before the live run. Tickets `101`, `102`, and `103` all finished with stored status `resolved`. The live runs appended to `output/audit_trail.json`; failed setup attempts are retained as audit history, followed by the successful MCP-connected runs.

The final outcomes are recorded in `output/resolved_tickets.json`, and `output/resolved_board.html` is a double-clickable static board snapshot for the three resolved tickets. The Actual sections in `output/desk_tickets.html` list the agents, delegations, tools, and outcomes observed in the run.

Cash reconciliation: starting checking balance `$3,400.00`; ticket 101 change `$0.00` because no reprint payment was approved; ticket 102 change `$0.00` because rent was flagged for human approval but not paid; ticket 103 change `$0.00` because no hoodie purchase or discount was approved; ending checking balance `$3,400.00`. The working `cash_accounts` table matches this ending balance and `payments` contains no new rows.
