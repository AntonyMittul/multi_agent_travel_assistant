# VoyageMind — Multi-Agent Travel Assistant

An **agentic, multi-agent travel planner** built on **LangGraph**. An orchestrator
decomposes a natural-language goal ("plan a 5-night trip from Mumbai to Tokyo for 2,
budget $3000, love food & culture") into subtasks and delegates each to a specialized
agent. Agents share state, a **critic** validates the merged plan, and the system
**autonomously replans** when constraints (e.g. budget) are violated — all streamed
live to a React UI.

> Runs in two modes: **live** (Google Gemini) or **offline demo** (rule-based
> orchestrator + mock data) so it works with zero API keys.

---

## Why this isn't just sequential tool calls

| Capability | How it's implemented |
|---|---|
| **Orchestration** | An `orchestrator` node decomposes the goal and dynamically routes to the next specialist via LangGraph **conditional edges**. |
| **State-aware agents** | A shared `TravelState` (TypedDict) — the hotel agent sees the flight, the budget agent sees both, the critic sees everything. |
| **Autonomous decisions** | The `critic` agent inspects the assembled plan and decides to **approve or replan**. |
| **Dynamic routing / fallback** | Over budget → critic downgrades tiers and re-runs only the cost-bearing agents. |
| **Scalability / customizability** | Add an agent = one node function + one line in `SPECIALISTS`. Swap a mock tool for a real API without touching the agent. |
| **Fail-safe** | Bounded `MAX_REVISIONS` + LangGraph `recursion_limit` → no infinite loops, no dead ends. |

## Architecture

```
        ┌──────────────┐   replan loop
   ┌────│ Orchestrator │◀─────────────────┐
   │    └──────┬───────┘                  │
   │           │ dynamic routing          │
   │   ┌───────┼────────┬─────────┬───────┴──┬──────────┐
   │ Destination Weather Flight  Hotel  Activities Logistics Budget
   │   └───────┴────────┴─────────┴──────────┴──────────┘
   │           │  (all read/write shared TravelState)
   │     ┌─────▼──────┐
   └─────│   Critic   │── approve → Finalize → END
         └────────────┘
```

### Agents

| Agent | Job | Data source |
|---|---|---|
| **Orchestrator** | Parse goal → preferences, plan & route subtasks | Gemini / heuristics |
| **Destination** | Pick (if unspecified) & describe the place | Gemini / curated fallback |
| **Weather** | 7-day forecast | Open-Meteo (free, no key) |
| **Flight** | Routes, times, fares | Mock (real-API-ready) |
| **Hotel** | Lodging by tier/budget | Mock (real-API-ready) |
| **Activities** | Day-by-day plan from interests + weather | Gemini / templated |
| **Logistics** | Currency, language, timezone | Local dataset / Gemini |
| **Budget** | Aggregate costs, check vs target | Computed |
| **Critic** | Validate plan, trigger replans | Rule-based |

---

## Project layout

```
backend/
  app/
    main.py            # FastAPI + SSE streaming
    config.py          # env / mode flags
    state.py           # shared TravelState
    llm.py             # Gemini wrapper (offline-safe)
    graph/
      builder.py       # LangGraph wiring
      agents/          # one file per agent
    tools/             # weather / flights / hotels / countries
  requirements.txt
  run.py
frontend/              # Vite + React + TypeScript + Tailwind v4
  src/
    App.tsx
    lib/api.ts         # SSE client
    components/        # PlanForm, AgentTimeline, ItineraryView
```

---

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # optional — add your Gemini key for live mode
python run.py                 # serves http://localhost:8000
```

Get a free Gemini key at <https://aistudio.google.com/app/apikey> and set
`GOOGLE_API_KEY` in `.env`. Leave it blank to run in offline demo mode.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                   # serves http://localhost:5173
```

The dev server proxies `/api/*` to the backend on port 8000.

Open <http://localhost:5173>, describe a trip, and watch the agents coordinate.

---

## Extending

- **Add an agent**: write `backend/app/graph/agents/foo.py` returning a partial
  state update, then add it to `SPECIALISTS` and `PLAN`.
- **Use real travel data**: replace `tools/flights_tool.py` / `hotels_tool.py`
  with an Amadeus/Kiwi client — keep the function signature and return shape.
- **Tune the fail-safe**: `MAX_REVISIONS` in `.env`.

## API

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Mode (live/demo) + model |
| `POST` | `/api/plan` | `{ "query": "..." }` → SSE stream of agent events + final itinerary |
