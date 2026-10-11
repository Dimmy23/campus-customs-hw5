# Campus Customs Multi-Agent Team

HW5 builds a read-only MCP-backed Campus Customs operations team with a FastAPI backend and a React + Vite dashboard.

## Layout

- `data/` — the original `campus_customs.db` and working `campus_customs_new.db` databases.
- `mcp_server/` — FastMCP tools that read the working database.
- `backend/` — PydanticAI agents, prompts, MCP client, audit writer, and FastAPI routes.
- `frontend/` — the Vite/TypeScript dashboard.
- `output/` — harness documentation, smoke evidence, ticket desk, design notes, audit trail, reflection, and resolution artifacts.

## Run

1. Copy `.env.example` to `.env` and add a Portkey key. Never commit `.env`.
2. Install Python dependencies with `pip install -r requirements.txt`.
3. Start the backend from `backend/`: `uvicorn main:app --port 8000`.
4. Install frontend dependencies in `frontend/` with `npm install`.
5. Start the dashboard in `frontend/` with `npm run dev`.

The agents use Portkey with `gpt-6-luna`; shop facts come through the MCP server. Agents prepare recommendations, while human approval is required before cash-changing actions.
