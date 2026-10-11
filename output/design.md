# Campus Customs Agent Dashboard — Design Notes

## Layout

The dashboard uses a two-column operations desk on desktop: a sticky ticket rail on the left and a selected-ticket workspace on the right. A compact top bar establishes that the desk is live, while the opening headline—“Good decisions feel coordinated.”—makes the product feel like a calm collaboration tool rather than a technical console.

The workspace is organized in a deliberate order: ticket identity and the primary “Run agent team” action, a live run-status strip, five agent cards, the completed team summary, and finally the human-approval form. The checking balance and open-ticket count stay above the work area as persistent context.

## How the agents read differently

Each agent has a pastel card with a distinct tint and a shared visual language: a role avatar, a status line, the latest thing the agent said, and small MCP-tool chips. The differences are quiet rather than noisy: Boss uses lavender, Inventory mint, Accounting lemon, Facilities sky blue, and Customer Service peach. This makes the team scannable while still feeling like one coordinated desk.

During a run, the board polls `/api/events` and changes the cards from “Waiting for a task” to live activity. After the run, the typed report becomes a summary grid with each agent’s finding and recommended next step. The UI never pretends that a recommendation is an action.

## Resolved tickets and cash

The ticket rail uses a green dot for open work and a check icon plus `resolved` label after the backend finishes a run. The selected workspace also changes its status strip to “Run finished · ticket marked resolved.” This gives a clear closure signal without hiding the underlying agent summary.

Cash is intentionally a visible, calm metric rather than a dramatic alert: the checking balance is always shown near the top. The approval panel is warm yellow to distinguish a consequential human action from ordinary agent activity. It requires amount, approver, account, and optional reference ID; after approval, the balance refreshes from `/api/cash` and visibly drops.

## Creative choices

Pastel colors, rounded cards, soft shadows, and a few hand-drawn-feeling color blocks make the board feel welcoming and human without becoming playful at the expense of trust. “Agents prepare. People approve.” is a small reminder of the safety model. Tool names appear as compact evidence chips, giving an operator confidence about what happened without forcing them to read raw logs. The generous whitespace, friendly copy, keyboard-friendly buttons, responsive mobile layout, and direct API-docs link are designed to make a real operator enjoy returning to the desk.
