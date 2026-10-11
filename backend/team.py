from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from audit import audit
from mcp_client import call_mcp
from models import AgentFinding, AgentRole, Delegation, TeamReport


ROOT = Path(__file__).resolve().parents[2]
PROMPTS = Path(__file__).resolve().parent / "prompts"
MODEL_NAME = "gpt-6-luna"
ROLES: tuple[AgentRole, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")


def _api_key() -> str:
    key = os.getenv("PORTKEY_API_KEY")
    if key:
        return key
    env_file = ROOT / ".env"
    for line in env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []:
        if line.startswith("PORTKEY_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise RuntimeError("PORTKEY_API_KEY is not configured in the environment or root .env")


def _model() -> OpenAIChatModel:
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(
        base_url="https://api.portkey.ai/v1", api_key=_api_key()
    ), settings={"openai_reasoning_effort": "none"})


def _prompt(role: AgentRole) -> str:
    return (PROMPTS / f"{role}.md").read_text(encoding="utf-8")


class TeamDeps:
    def __init__(self, run_id: str, ticket_id: int, step: int = 0):
        self.run_id, self.ticket_id, self.step = run_id, ticket_id, step


def _make_agent(role: AgentRole) -> Agent[TeamDeps, AgentFinding]:
    agent = Agent(_model(), output_type=AgentFinding, deps_type=TeamDeps,
                  system_prompt=_prompt(role))

    async def _call_mcp(ctx: RunContext[TeamDeps], tool_name: str, arguments: dict[str, Any]) -> Any:
        ctx.deps.step += 1
        audit(ctx.deps.run_id, ctx.deps.step, role, "mcp_call", ticket_id=ctx.deps.ticket_id,
              tool_name=tool_name, input_summary=str(arguments)[:240])
        result = await call_mcp(tool_name, arguments)
        audit(ctx.deps.run_id, ctx.deps.step, role, "mcp_call", ticket_id=ctx.deps.ticket_id,
              tool_name=tool_name, output_summary=str(result)[:240])
        return result

    @agent.tool
    async def list_open_tickets(ctx: RunContext[TeamDeps]) -> Any:
        """List the database's currently open Campus Customs tickets."""
        return await _call_mcp(ctx, "list_open_tickets", {})

    @agent.tool
    async def get_ticket_context(ctx: RunContext[TeamDeps], ticket_id: int) -> Any:
        """Get a ticket and its database-linked invoice, lease, inventory, and pricing."""
        return await _call_mcp(ctx, "get_ticket_context", {"ticket_id": ticket_id})

    @agent.tool
    async def check_inventory(ctx: RunContext[TeamDeps], sku: str, size: str | None = None) -> Any:
        """Check the database inventory for a SKU and optional size."""
        return await _call_mcp(ctx, "check_inventory", {"sku": sku, "size": size})

    @agent.tool
    async def get_vendor_details(ctx: RunContext[TeamDeps], vendor_id: int) -> Any:
        """Get one vendor's database record."""
        return await _call_mcp(ctx, "get_vendor_details", {"vendor_id": vendor_id})

    @agent.tool
    async def delegate(ctx: RunContext[TeamDeps], to_agent: AgentRole, task: str) -> str:
        """Run a bounded specialist delegation with the shared team context."""
        if to_agent == role:
            raise ValueError("An agent cannot delegate to itself.")
        if ctx.deps.step >= 20:
            raise ValueError("The maximum delegation step limit has been reached.")
        ctx.deps.step += 1
        audit(ctx.deps.run_id, ctx.deps.step, role, "delegation", ticket_id=ctx.deps.ticket_id,
              delegated_to=to_agent, input_summary=task[:240])
        delegated = await AGENTS[to_agent].run(
            f"Ticket {ctx.deps.ticket_id}. Delegated task: {task}. Return only database-backed facts.",
            deps=ctx.deps,
        )
        return delegated.output.model_dump_json()

    return agent


AGENTS = {role: _make_agent(role) for role in ROLES}


async def run_team(ticket_id: int, objective: str, max_steps: int = 12) -> TeamReport:
    """Run the five-role team with a bounded, auditable specialist loop."""
    if max_steps < 5 or max_steps > 20:
        raise ValueError("max_steps must be between 5 and 20")
    run_id = uuid.uuid4().hex
    deps = TeamDeps(run_id, ticket_id)
    findings: list[AgentFinding] = []
    order: tuple[AgentRole, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")
    for role in order:
        if deps.step >= max_steps:
            break
        audit(run_id, deps.step, role, "agent_start", ticket_id=ticket_id,
              input_summary=objective[:240])
        result = await AGENTS[role].run(
            f"Ticket {ticket_id}. Objective: {objective}. Review only database-backed facts and report your role's findings.",
            deps=deps,
        )
        findings.append(result.output)
        audit(run_id, deps.step, role, "agent_result", ticket_id=ticket_id,
              output_summary=result.output.model_dump_json()[:240])
    facts = [fact for finding in findings for fact in finding.facts]
    report = TeamReport(
        ticket_id=ticket_id,
        status="needs_human_review",
        facts=facts,
        findings=findings,
        customer_safe_response="The request was reviewed by the Campus Customs team and requires human approval before any commitment.",
        human_approval_required=True,
    )
    audit(run_id, deps.step + 1, "boss", "team_complete", ticket_id=ticket_id,
          output_summary=report.model_dump_json()[:240])
    return report
