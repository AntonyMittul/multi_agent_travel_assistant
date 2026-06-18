# VoyageMind — Multi-Agent Travel Assistant

An **agentic, multi-agent travel planner** built on **LangGraph**. An orchestrator
decomposes a natural-language goal ("plan a 5-night trip from Mumbai to Tokyo for 2,
budget $3000, love food & culture") into subtasks and delegates each to a specialized
agent. Agents share state, a **critic** validates the merged plan, and the system
**autonomously replans** when constraints (e.g. budget) are violated — all streamed
live to a React UI.

**Real data, not mocks** — geocoding, weather, flight schedules, hotels, points of
interest and maps all come from live APIs. The only estimated values are flight fares
and hotel room rates (no free API provides those), and they're clearly labeled.

---

## Why this isn't just sequential tool calls

| Capability | How it's implemented |
|---|---|
| **Orchestration** | An `orchestrator` node decomposes the goal and dynamically routes to the next specialist via LangGraph **conditional edges**. |
| **State-aware agents** | A shared `TravelState` (TypedDict) — the weather/hotel/activities agents reuse the destination's geocoded coordinates; the budget agent sees every cost. |
| **Autonomous decisions** | The `critic` agent inspects the assembled plan and decides to **approve or replan**. |
| **Dynamic routing / fallback** | Over budget → critic downgrades tiers and re-runs only the cost-bearing agents. |
| **Scalability / customizability** | Add an agent = one node function + one line in `SPECIALISTS`. Swap a data tool without touching the agent. |
| **Fail-safe** | Bounded `MAX_REVISIONS` + LangGraph `recursion_limit` → no infinite loops, no dead ends. |

## Real data sources

| Agent | Source | Key needed |
|---|---|---|
| **Destination + Logistics** | **OpenCage** geocoding + annotations (coords, currency, timezone, flag, country) | `OPENCAGE_API_KEY` |
| | **GeoDB Cities** (population, region, autocomplete) | optional (free no-key fallback) |
| **Weather** | **Open-Meteo** 7-day forecast | none |
| **Flights** | **AviationStack** real schedules/airlines on the route + **estimated** fares¹ | `AVIATIONSTACK_API_KEY` |
| **Hotels** | **OpenStreetMap** (Overpass) real listings + **estimated** rates¹ | none |
| **Activities** | **OpenStreetMap** (Overpass) real attractions/museums/parks, organized by Gemini | none |
| **Map** | **OpenStreetMap** tiles via Leaflet | none |
| **Reasoning** | **Gemini `gemini-3.1-flash-lite`** (goal parsing, narrative, day planning) | `GOOGLE_API_KEY` |

¹ AviationStack returns no fares at any plan and OSM has no prices, so flight fares
(distance-based) and hotel rates (tier/star-based) are transparent estimates flagged
`price_estimated`. To get *real* prices later, swap in the Amadeus Self-Service API.

> **Graceful degradation:** every key is optional. Each tool returns an "unavailable"
> slice if its key is missing, and the graph still completes. Minimum useful set:
> `OPENCAGE_API_KEY` + `GOOGLE_API_KEY`.

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

## Project layout

```
backend/
  app/
    main.py            # FastAPI + SSE streaming + /api/cities autocomplete
    config.py          # env / keys / mode flags
    state.py           # shared TravelState
    llm.py             # Gemini wrapper (offline-safe)
    graph/
      builder.py       # LangGraph wiring
      agents/          # one file per agent
    tools/
      geo_tool.py      # OpenCage geocoding + annotations
      weather_tool.py  # Open-Meteo
      flights_tool.py  # AviationStack + distance fare estimate
      osm_tool.py      # OpenStreetMap Overpass (hotels + POIs)
      geodb_tool.py    # GeoDB Cities search
      airports.py      # bundled IATA/coords table
      countries_tool.py# language lookup
  requirements.txt
  run.py
frontend/              # Vite + React + TypeScript + Tailwind v4
  src/
    App.tsx            # layout + light/dark theme toggle
    lib/api.ts         # SSE client
    components/        # PlanForm, AgentTimeline, ItineraryView, TripMap, ThemeToggle
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

cp .env.example .env          # add your keys (see below)
python run.py                 # serves http://localhost:8000
```

**API keys** (all free tiers; add to `backend/.env`):

| Variable | Where to get it | Required? |
|---|---|---|
| `GOOGLE_API_KEY` | https://aistudio.google.com/app/apikey | for reasoning |
| `OPENCAGE_API_KEY` | https://opencagedata.com/ | for geo/weather/hotels |
| `AVIATIONSTACK_API_KEY` | https://aviationstack.com/ | for live flight schedules |
| `GEODB_API_KEY` | https://rapidapi.com/wirefreethought/api/geodb-cities | optional |

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                   # serves http://localhost:5173 (proxies /api → :8000)
```

Open <http://localhost:5173>, describe a trip, and watch the agents coordinate. Toggle
light/dark from the header.

---

## Extending

- **Add an agent**: write `backend/app/graph/agents/foo.py` returning a partial state
  update, then add it to `SPECIALISTS` and `PLAN` in `graph/builder.py` / `orchestrator.py`.
- **Real prices**: add the Amadeus Self-Service API (free tier) for live flight fares
  and hotel room rates; replace `flights_tool.py` / the hotel pricing in `agents/hotel.py`.
- **Tune the fail-safe**: `MAX_REVISIONS` in `.env`.

## API

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Mode (live/demo) + model |
| `GET` | `/api/cities?q=` | City autocomplete (GeoDB) |
| `POST` | `/api/plan` | `{ "query": "..." }` → SSE stream of agent events + final itinerary |
