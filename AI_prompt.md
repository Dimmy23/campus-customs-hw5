# Campus Customs Multi-Agent — AI Prompt Log

This file is the single source of truth for the prompts used while developing the HW5 Campus Customs multi-agent system. It will be updated throughout the assignment. Spelling, grammar, and wording are corrected as requirements evolve without changing their intended meaning.

## Problem 1 — [Title to be added]

### Prompts

_Prompts for this problem will be added here._

## Problem 2 — Study the Campus Customs Database

### Prompt 2.1 — Database inspection and copy

Inspect every table and field in `data/campus_customs.db`. Copy the original database to `data/campus_customs_new.db` before making any HW5 database changes.

Study two open tickets so the agents understand how tickets connect to related tables. Document those relationships in the harness.

Start `output/harness.md`. For every table, list all fields and add one short sentence explaining why the table matters to the agents.

## Problem 3 — Build the MCP Server

### Prompt 3.1 — Build the MCP server

Build a read-only FastMCP server in `mcp_server/` that reads from `data/campus_customs_new.db`. Do not connect or run the server yet.

Implement three clearly named tools needed for the Campus Customs tickets in the database. The tools must retrieve only database-backed information and must never invent, infer, or fabricate data.

For each MCP tool, document in `output/harness.md` the tables it reads, the ticket or tickets it helps unlock among tickets `101`, `102`, and `103`, and one specific sentence explaining why it is appropriate for those tickets. Also add a short `mcp_server/README.md` explaining the server’s purpose, database file, and three tools.

Grow the MCP server with any additional read-only tool the agent team needs, and update the harness and README so every current tool is documented.

## Problem 4 — Add and Test the MCP Server

### Prompt 4.1 — Connect and smoke-test the MCP server

Add the Campus Customs MCP server to the project’s root `.mcp.json` so the vibe coder can call it. Save the connection JSON there, using the `HW5/mcp_server/mcp_server.py` entry point.

Test each of the three MCP tools and save evidence in `output/mcp_smoke.json`. For every tool, include the prompt used, the tool name, and the tool output. The output must match values in `data/campus_customs_new.db` exactly.

## Problem 5 — Build the Multi-Agent Team and Grow MCP Tools

### Prompt 5.1 — Build the multi-agent team

Build a fully connected PydanticAI agent team for Campus Customs with five clear roles: Boss, Inventory, Accounting, Facilities, and Customer Service. Give each role a detailed prompt in `backend/prompts/`, use typed data models in `backend/models.py`, and implement bounded delegation and agent-loop behavior under `backend/`.

Use the root `.env` `PORTKEY_API_KEY` through Portkey and use only `gpt-6-luna` for every agent. Shop facts must come from the Campus Customs MCP server and `data/campus_customs_new.db`; do not create a second database-tools layer. Append auditable events for every agent-loop step to `output/audit_trail.json` without deleting earlier runs.

Document every agent, every current MCP tool, its source table, safety guardrails, and token-use limits in `output/harness.md`. Update `mcp_server/README.md` whenever the tool list changes.

## Problem 6 — Plan the Three Open Tickets

Before running or changing the backend, document what the team is expected to do for open tickets `101`, `102`, and `103`. Build `output/desk_tickets.html` as a standalone page with one tab per ticket. Each ticket tab must contain an `Expected` section and reserved space for an `Actual` section to be completed after the agents run. Add empty `Cash` and `Reflection` tabs labeled as coming later.

## Problem 7 — Backend Routes

Use FastAPI in `backend/main.py` to expose the ticket desk: list ticket statuses, run the agent team for a ticket ID, return recent per-agent audit events and tools used, apply a human-approved payment or purchase, return the checking balance, and reset the working database from the original values. Document every route in `output/harness.md`. Run the backend from `backend/` with Uvicorn on port 8000.

## Problem 8 — Agent Dashboard

Build a polished React + Vite + TypeScript dashboard in `frontend/`. It must list the three tickets, let a user select and run the team, show agent activity and summaries, mark a ticket resolved after a completed run, expose human approval for payments or purchases, and show the checking balance updating after approval. Use pastel colors, intuitive controls, Vite-origin CORS, and document the layout and creative design choices in `output/design.md`.

## Problem 9 — Resolve the Tickets

Reset `data/campus_customs_new.db` from the original values before running tickets `101`, `102`, and `103` through the board. Fill only the Actual sections of `output/desk_tickets.html` from the live audit trail, add the verified cash ledger to its Cash tab, save `output/resolved_tickets.json`, and create a double-clickable `output/resolved_board.html` snapshot page. Append real runs to `output/audit_trail.json` and finish `output/harness.md` with the database tables, MCP tools, five agents, routes, dashboard, and safety rules.

## Problem 10 — Reflection

Keep the Reflection tab in `output/desk_tickets.html` open and available for the student to complete. Include questions about agent performance, Actual-versus-Expected differences, when one tool-using agent would be simpler, three solvable future Campus Customs problems, and three problems that require new tools or agents.

## Problem 11 — Submit to GitHub

Prepare the HW5 submission in the expected layout and push it to a public GitHub repository. Record the repository URL in `output/github_url.txt`. Never include the real `.env`; include `.env.example`. Include both `data/campus_customs.db` and `data/campus_customs_new.db`.
