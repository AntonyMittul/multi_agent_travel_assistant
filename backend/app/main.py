"""FastAPI server: bridges the LangGraph engine to the React UI over SSE."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .config import GEMINI_MODEL, llm_available
from .graph.builder import GRAPH, RECURSION_LIMIT

app = FastAPI(title="VoyageMind — Multi-Agent Travel Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo: open CORS. Lock down for production.
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    query: str
    # optional structured overrides (the form can pre-fill these)
    preferences: Dict[str, Any] | None = None


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "mode": "live (Gemini)" if llm_available() else "offline (no Gemini key)",
        "model": GEMINI_MODEL if llm_available() else None,
    }


def _sse(event: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event)}\n\n"


def _run_stream(query: str, preferences: Dict[str, Any] | None):
    """Drive the graph and yield SSE events as each node completes."""
    initial: Dict[str, Any] = {"query": query, "messages": [], "errors": []}
    if preferences:
        initial["preferences"] = preferences

    yield _sse({"agent": "system", "kind": "start", "text": "Orchestration started.", "data": {}})

    final_state: Dict[str, Any] = {}
    try:
        for chunk in GRAPH.stream(
            initial,
            config={"recursion_limit": RECURSION_LIMIT},
            stream_mode="updates",
        ):
            # chunk = {node_name: state_update}
            for node, update in chunk.items():
                msgs: List[Dict[str, Any]] = update.get("messages", []) if update else []
                for m in msgs:
                    yield _sse(m)
                if update:
                    final_state.update(update)
    except Exception as exc:  # noqa: BLE001
        yield _sse({"agent": "system", "kind": "error", "text": str(exc), "data": {}})
        return

    itinerary = final_state.get("final_itinerary", {})
    yield _sse({"agent": "system", "kind": "done", "text": "Itinerary complete.",
                "data": {"itinerary": itinerary}})


@app.post("/api/plan")
def plan(req: PlanRequest):
    return StreamingResponse(
        _run_stream(req.query, req.preferences),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
