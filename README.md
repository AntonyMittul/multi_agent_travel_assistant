<div align="center">

<img src="frontend/public/logo.svg" width="92" alt="Navora logo" />

# Navora

### Plan smarter. Travel better.

**An AI multi-agent travel assistant that turns a single sentence into a complete, grounded trip plan.**

Tell Navora *“5 nights in Goa from Mumbai for 2, budget ₹150000, love beach and food”* — and a team of specialized AI agents collaborate to research the destination, check the weather, find flights and hotels, curate attractions, balance the budget, and hand back a polished, downloadable itinerary.

Built with **LangGraph · FastAPI · Google Gemini · React · TypeScript · Tailwind**.

</div>

---

## ✨ What makes it different

Most “AI trip planners” are a single prompt that hallucinates an itinerary. Navora is a **true multi-agent system**: an orchestrator decomposes your goal into subtasks and routes each to a specialist agent. The agents **share state**, a **critic** validates the merged plan, and the system **autonomously re-plans** when constraints (like budget) are violated — all powered by **real data**, not made-up details.

> **Real data, not mocks.** Geocoding, weather, flight schedules, hotels, attractions, restaurants, currency and maps all come from live sources. The only estimated values are flight fares and hotel room rates (no free API provides those) — and they’re always clearly labeled.

---

## 🌟 Features

- 🧭 **Conversational planning** — a chat interface that asks clarifying questions (“Which city are you flying from?”) and refines on follow-ups (“show different attractions”, “make it more luxury”, “add nightlife”).
- 🤝 **Multi-agent orchestration** — 8 specialist agents + a critic, coordinated by LangGraph with dynamic routing and a bounded self-correction loop.
- 🌍 **Real destinations & maps** — OpenCage geocoding + an interactive OpenStreetMap with a **numbered flight-route** between attractions.
- ☀️ **Live weather** — real 7-day forecast (Open-Meteo) that even shapes the plan (rainy → indoor-leaning activities).
- ✈️ **Flights & 🏨 hotels** — real airline schedules (AviationStack) and real hotel listings (OpenStreetMap), with transparent estimated pricing.
- 📍 **Smart attractions** — Gemini curates the iconic must-sees for *any* destination, each with a **reason badge** (“Best Sunset Spot”), a category, and a real photo.
- 💰 **Auto-balanced budget in local currency** — costs convert to the traveler’s currency (₹/$/€/¥…); if you’re over budget the **critic downgrades tiers and re-plans**.
- 🎒 **Travel styles** — Budget · Luxury · Family · Adventure · Solo · Business, each producing a genuinely different plan for the same city.
- 🧠 **Agent activity panel** — a transparent, collapsible log of what each agent actually did (great for demos).
- 📄 **One-click PDF export** — a polished trip document (cover page, map, day-by-day, hotels, budget) generated server-side.
- 🌓 **Premium UI** — light/dark themes, a cinematic world-map + flight-route background, glassmorphism cards, and a tabbed itinerary (Overview · Itinerary · Budget · Map).
- 🛟 **Graceful degradation** — every API key is optional; missing keys disable only their feature and the system still completes.

---

## 🧩 How it works

```
            ┌──────────────┐   replan loop (bounded)
   ┌────────│ Orchestrator │◀──────────────────┐
   │        └──────┬───────┘                    │
   │  decompose &  │  dynamic routing           │
   │  route        ▼                            │
   │   ┌───────┬────────┬────────┬──────────┬───┴──────┬────────┐
   │ Destination Weather Flight  Hotel  Activities  Logistics  Budget
   │   └───────┴────────┴────────┴──────────┴──────────┴────────┘
   │              │  (all read & write a shared TravelState)
   │        ┌─────▼──────┐
   └────────│   Critic   │── approve → Finalize → PDF / UI
            └────────────┘
```

A natural-language request enters through the **chat endpoint**, where Gemini gathers preferences (asking follow-ups if needed). The **orchestrator** then builds a plan and routes subtasks to specialists that all read/write a shared `TravelState` (so the hotel agent sees the flight, the budget agent sees everything). The **critic** checks the assembled plan; if it’s over budget it adjusts tiers and sends the cost-bearing agents back to work — bounded by `MAX_REVISIONS` + a recursion limit so it can never loop forever.

### The agents

| Agent | Responsibility | Data source |
|---|---|---|
| **Orchestrator** | Parse the goal, plan & route subtasks, apply constraints | Gemini / heuristics |
| **Destination** | Normalize the place (region → gateway city), describe it, fetch a photo | OpenCage · Gemini · Wikipedia |
| **Weather** | 7-day forecast that influences the plan | Open-Meteo *(no key)* |
| **Flight** | Real schedules on the route + estimated fares | AviationStack · bundled airport/IATA table |
| **Hotel** | Real lodging near the destination + estimated rates | OpenStreetMap *(no key)* |
| **Activities** | Curate iconic attractions + real restaurants → day-by-day plan | Gemini · OpenStreetMap · Wikipedia/Openverse |
| **Logistics** | Currency, language, timezone | OpenCage annotations |
| **Budget** | Aggregate every cost, convert currency, check vs target | Computed · open.er-api.com *(no key)* |
| **Critic** | Validate the merged plan, trigger bounded re-plans | Rule-based |

---

## 🛠️ Tech stack

**Backend** — Python · [FastAPI](https://fastapi.tiangolo.com/) · [LangGraph](https://langchain-ai.github.io/langgraph/) · Google **Gemini** (`gemini-3.1-flash-lite` via `langchain-google-genai`) · ReportLab (PDF) · Pillow · staticmap

**Frontend** — [Vite](https://vitejs.dev/) · React 18 · TypeScript · Tailwind CSS v4 · Leaflet (OpenStreetMap)

**APIs (all free; only OpenCage + Gemini keys required):**

| Need | Source | Key? |
|---|---|---|
| Reasoning | Google Gemini | ✅ |
| Geocoding + country annotations | OpenCage | ✅ |
| Weather | Open-Meteo | — |
| Hotels / attractions / restaurants / map | OpenStreetMap | — |
| Currency rates | open.er-api.com | — |
| Place photos | Wikipedia / Openverse | — |
| Flight schedules *(optional)* | AviationStack | optional |

---

## 🚀 Getting started

### Prerequisites
- Python 3.10+ and Node.js 18+
- A free **Gemini** key — <https://aistudio.google.com/app/apikey>
- A free **OpenCage** key — <https://opencagedata.com/>

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then add your keys
python run.py               # serves http://localhost:8000
```

`.env`:
```
GOOGLE_API_KEY=your_gemini_key
OPENCAGE_API_KEY=your_opencage_key
GEMINI_MODEL=gemini-3.1-flash-lite
# AVIATIONSTACK_API_KEY=optional
```

> Visit `http://localhost:8000/api/health` to confirm both keys work — it live-tests Gemini and OpenCage and reports per-key status.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                 # serves http://localhost:5173 (proxies /api → :8000)
```

Open <http://localhost:5173> and start planning.

---

## 🧭 Walkthrough

1. **Describe your trip** in the chat — a destination or just a vibe, how long, who’s going, and a budget. Optionally pick a **travel style** chip (Budget/Luxury/Family/…).
2. **Navora asks if it needs more** — e.g. “Which city are you flying from?” — then plans.
3. **Watch it think** — a loading animation runs while the agents collaborate behind the scenes.
4. **Get your itinerary**, organized into tabs:
   - **Overview** — narrative summary, trip stats, destination, weather, a photo gallery of attractions (each with a “why”), local logistics, and the **Agent activity** log.
   - **Itinerary** — a day-by-day plan (with real attractions & restaurants), flights, and hotels.
   - **Budget** — a breakdown in your local currency vs your target.
   - **Map** — the numbered flight route across real attraction pins.
5. **Refine by chatting** — “show different attractions”, “more offbeat / hidden gems”, “make it more relaxed”. The plan regenerates, avoiding repeats.
6. **Download the PDF** — a polished, shareable trip document.

---

## 📁 Project structure

```
backend/
  app/
    main.py              # FastAPI: /api/chat, /api/export, /api/health, /api/plan
    config.py            # env / keys / mode flags
    state.py             # shared TravelState
    llm.py               # Gemini wrapper (offline-safe)
    report.py            # PDF generation (ReportLab)
    graph/
      builder.py         # LangGraph wiring
      agents/            # one file per agent
    tools/               # geo, weather, flights, osm, fx, image, airports …
    fonts/               # bundled DejaVu Sans (Unicode currency glyphs)
  requirements.txt
  run.py
frontend/
  src/
    App.tsx              # chat UI + theme
    components/          # ItineraryView, TripMap, Background, Loader, ThemeToggle
    lib/                 # api client, generated world-map paths
render.yaml              # one-click Render deploy (backend + frontend)
DEPLOY.md                # deployment guide
```

---

## ☁️ Deployment

A **Render Blueprint** (`render.yaml`) deploys both the API and the static frontend on Render’s free tier in a few clicks — the frontend↔backend URL is wired automatically. See **[DEPLOY.md](DEPLOY.md)** for the step-by-step.

---

## 🔌 API reference

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Live-tests Gemini + OpenCage; reports per-key status |
| `POST` | `/api/chat` | `{ messages, style?, previous? }` → a follow-up question **or** a full itinerary |
| `POST` | `/api/export` | `{ itinerary }` → a PDF trip plan (download) |
| `POST` | `/api/plan` | `{ query }` → SSE stream of agent events + final itinerary (legacy) |

---

## ⚠️ Notes & limitations

- **Estimated prices.** No free API provides real airfares or hotel room rates, so those are transparent, clearly-labeled estimates (flights by great-circle distance; hotels by tier/stars). Swap in the **Amadeus Self-Service API** for real prices.
- **Free-tier cold start.** On Render’s free tier the backend sleeps after idle; the first request then takes ~30–60s to wake.
- **AviationStack** free tier is limited (100 req/month, no fares) — schedules are a nice-to-have; the plan works fine without it.

---

## 🗺️ Roadmap ideas

- Amadeus integration for real fares & room rates
- Day-ordered map route (Day 1 → Day N)
- Saved trips / shareable links
- Multi-city itineraries

---

<div align="center">
Built by <a href="https://github.com/AntonyMittul">Antony Mittul</a> · powered by collaborating AI agents.
</div>
