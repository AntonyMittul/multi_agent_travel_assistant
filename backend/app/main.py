"""FastAPI server: conversational chat + the LangGraph planning engine."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from .config import (AVIATIONSTACK_API_KEY, GEMINI_MODEL, GOOGLE_API_KEY,
                     OPENCAGE_API_KEY, llm_available)
from .graph.agents.orchestrator import _heuristic_parse, _normalize
from .graph.builder import GRAPH, RECURSION_LIMIT
from .llm import get_llm, llm_json
from .tools.geo_tool import geocode

app = FastAPI(title="VoyageMind — Multi-Agent Travel Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo: open CORS. Lock down for production.
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────── health / diagnostics ───────────────────────────
_DIAG: Dict[str, Any] | None = None


def _diagnose() -> Dict[str, Any]:
    """Live-test each key once per process so the UI can show what works."""
    global _DIAG
    if _DIAG is not None:
        return _DIAG

    gemini = {"key_present": bool(GOOGLE_API_KEY), "model": GEMINI_MODEL,
              "ok": False, "error": None}
    if llm_available():
        try:
            get_llm().invoke("Reply with the single word: ok")
            gemini["ok"] = True
        except Exception as exc:  # noqa: BLE001
            gemini["error"] = str(exc)[:300]

    opencage = {"key_present": bool(OPENCAGE_API_KEY), "ok": False, "error": None}
    if OPENCAGE_API_KEY:
        g = geocode("Paris, France")
        opencage["ok"] = bool(g.get("available"))
        if not opencage["ok"]:
            opencage["error"] = g.get("summary")

    if gemini["ok"]:
        mode = "live (Gemini)"
    elif GOOGLE_API_KEY:
        mode = "Gemini key set but call failed — check the key/model"
    else:
        mode = "offline (no Gemini key)"

    _DIAG = {
        "status": "ok",
        "mode": mode,
        "gemini": gemini,
        "opencage": opencage,
        "aviationstack": {"key_present": bool(AVIATIONSTACK_API_KEY)},
    }
    return _DIAG


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return _diagnose()


# ─────────────────────────── conversational chat ────────────────────────────
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    style: str | None = None  # travel style: budget/luxury/family/adventure/solo/business


_INTAKE_PROMPT = (
    "You are VoyageMind, an expert, warm, concise travel-planning assistant. "
    "From the conversation, extract the traveler's trip preferences and decide whether "
    "you have enough to build a full itinerary.\n"
    "You can plan once you know a destination (OR a clear vibe/interest so you can pick one) "
    "AND the trip length (nights or dates).\n"
    "IMPORTANT: the origin city is needed to estimate flights and their cost. If the user "
    "hasn't given an origin and the trip would involve flying, ask for it first (e.g. "
    "\"Which city will you be flying from?\"). Budget (+currency), travelers and interests "
    "also improve the plan — ask for the single most useful missing detail.\n"
    "If an important detail is missing or ambiguous, set ready=false and ask ONE short, "
    "friendly follow-up question. Don't interrogate — once you can make a good plan, do it.\n"
    "When ready, write a one-sentence friendly lead-in.\n"
    'Return ONLY JSON: {"ready": bool, "question": string|null, "lead": string|null, '
    '"preferences": {"origin": str|null, "destination": str|null, "budget": number|null, '
    '"budget_currency": str|null, "travelers": int, "nights": int|null, '
    '"interests": [str], "vibe": str|null}}.\n\nConversation:\n'
)


def _intake(history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Decide whether to ask a follow-up or plan now (LLM, with offline fallback)."""
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")

    if not llm_available():
        # offline: no conversation, just plan from the latest message
        return {"ready": True, "preferences": _heuristic_parse(last_user), "lead": None}

    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history[-10:])
    result = llm_json(_INTAKE_PROMPT + convo, fallback=None)
    if not isinstance(result, dict):
        return {"ready": True, "preferences": _heuristic_parse(last_user), "lead": None}

    # fail-safe: don't loop forever asking questions
    if sum(1 for m in history if m["role"] == "user") >= 4:
        result["ready"] = True
        result.setdefault("preferences", _heuristic_parse(last_user))
    return result


@app.post("/api/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    history = [{"role": m.role, "content": m.content} for m in req.messages]
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")

    intake = _intake(history)
    if not intake.get("ready"):
        return {
            "kind": "message",
            "content": intake.get("question") or "Tell me a bit more about your trip?",
        }

    prefs_in = intake.get("preferences") or _heuristic_parse(last_user)
    if req.style:
        prefs_in["style"] = req.style
    prefs = _normalize(prefs_in)
    try:
        final = GRAPH.invoke(
            {"query": last_user, "preferences": prefs, "messages": [], "errors": []},
            config={"recursion_limit": RECURSION_LIMIT},
        )
    except Exception as exc:  # noqa: BLE001
        return {"kind": "message", "content": f"Sorry — planning failed: {exc}"}

    return {
        "kind": "plan",
        "content": intake.get("lead") or "Here's a plan based on what you told me:",
        "itinerary": final.get("final_itinerary", {}),
    }


# ─────────────────────────── PDF export ─────────────────────────────────────
class ExportRequest(BaseModel):
    itinerary: Dict[str, Any]


@app.post("/api/export")
def export(req: ExportRequest):
    from .report import build_pdf

    pdf = build_pdf(req.itinerary)
    dest = ((req.itinerary.get("destination") or {}).get("name") or "trip").split(",")[0]
    safe = "".join(c for c in dest if c.isalnum() or c in " -_").strip().replace(" ", "_") or "trip"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="VoyageMind_{safe}.pdf"'},
    )


# ─────────────────────────── streaming plan (legacy) ────────────────────────
class PlanRequest(BaseModel):
    query: str
    preferences: Dict[str, Any] | None = None


def _sse(event: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event)}\n\n"


def _run_stream(query: str, preferences: Dict[str, Any] | None):
    initial: Dict[str, Any] = {"query": query, "messages": [], "errors": []}
    if preferences:
        initial["preferences"] = preferences

    yield _sse({"agent": "system", "kind": "start", "text": "Orchestration started.", "data": {}})

    final_state: Dict[str, Any] = {}
    try:
        for chunk in GRAPH.stream(initial, config={"recursion_limit": RECURSION_LIMIT},
                                  stream_mode="updates"):
            for _node, update in chunk.items():
                for m in (update.get("messages", []) if update else []):
                    yield _sse(m)
                if update:
                    final_state.update(update)
    except Exception as exc:  # noqa: BLE001
        yield _sse({"agent": "system", "kind": "error", "text": str(exc), "data": {}})
        return

    yield _sse({"agent": "system", "kind": "done", "text": "Itinerary complete.",
                "data": {"itinerary": final_state.get("final_itinerary", {})}})


@app.post("/api/plan")
def plan(req: PlanRequest):
    return StreamingResponse(
        _run_stream(req.query, req.preferences),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
