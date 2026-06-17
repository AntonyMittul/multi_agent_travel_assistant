import { useEffect, useRef, useState } from "react";
import PlanForm from "./components/PlanForm";
import AgentTimeline from "./components/AgentTimeline";
import ItineraryView from "./components/ItineraryView";
import { getHealth, streamPlan } from "./lib/api";
import type { AgentEvent, HealthInfo, Itinerary } from "./types";

export default function App() {
  const [query, setQuery] = useState("");
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [running, setRunning] = useState(false);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  async function run() {
    setRunning(true);
    setEvents([]);
    setItinerary(null);
    setError(null);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      for await (const ev of streamPlan(query, ctrl.signal)) {
        if (ev.kind === "done" && ev.data?.itinerary) {
          setItinerary(ev.data.itinerary as Itinerary);
        } else if (ev.kind === "error") {
          setError(ev.text);
        } else if (ev.agent !== "system") {
          setEvents((prev) => [...prev, ev]);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Stream failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 bg-[radial-gradient(60%_50%_at_50%_0%,rgba(99,102,241,0.18),transparent)] text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="bg-gradient-to-r from-indigo-300 to-fuchsia-300 bg-clip-text text-3xl font-extrabold text-transparent">
              VoyageMind
            </h1>
            <p className="text-sm text-slate-400">
              Multi-agent travel assistant · orchestrated with LangGraph
            </p>
          </div>
          {health && (
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
              {health.mode}
            </span>
          )}
        </header>

        <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
          <div className="space-y-6">
            <PlanForm query={query} setQuery={setQuery} onSubmit={run} running={running} />
            <AgentTimeline events={events} running={running} />
          </div>

          <div>
            {error && (
              <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
                {error}
              </div>
            )}
            {itinerary ? (
              <ItineraryView it={itinerary} />
            ) : (
              <div className="flex h-full min-h-[300px] items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-8 text-center">
                <p className="max-w-sm text-sm text-slate-500">
                  Your finished itinerary will appear here once the orchestrator, specialists,
                  and critic finish coordinating.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
