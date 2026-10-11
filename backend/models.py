from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AgentRole = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]


class TicketRequest(BaseModel):
    ticket_id: int = Field(ge=1)
    objective: str = Field(min_length=1, max_length=1000)


class Delegation(BaseModel):
    from_agent: AgentRole
    to_agent: AgentRole
    task: str = Field(min_length=1, max_length=1000)
    reason: str = Field(min_length=1, max_length=1000)


class AgentFinding(BaseModel):
    agent: AgentRole
    ticket_id: int
    summary: str
    facts: list[str] = Field(default_factory=list)
    recommended_next_step: str
    needs_delegation: bool = False
    delegation: Delegation | None = None


class TeamReport(BaseModel):
    ticket_id: int
    status: Literal["resolved", "needs_human_review", "blocked"]
    facts: list[str] = Field(default_factory=list)
    findings: list[AgentFinding] = Field(default_factory=list)
    customer_safe_response: str
    human_approval_required: bool = True


class AuditEvent(BaseModel):
    timestamp: str
    run_id: str
    step: int
    agent: AgentRole
    event: Literal["agent_start", "mcp_call", "agent_result", "delegation", "team_complete", "error"]
    ticket_id: int | None = None
    tool_name: str | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    delegated_to: AgentRole | None = None
