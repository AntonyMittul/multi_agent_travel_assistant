import { useEffect, useRef, useState } from "react";
import PlanForm from "./components/PlanForm";
import AgentTimeline from "./components/AgentTimeline";
import ItineraryView from "./components/ItineraryView";
import ThemeToggle from "./components/ThemeToggle";
import { getHealth, streamPlan } from "./lib/api";
import type { AgentEvent, HealthInfo, Itinerary } from "./types";

function initialDark(): boolean {
  const saved = localStorage.getItem("theme");
  if (saved) return saved === "dark";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

export default function App() {
  const [query, setQuery] = useState("");
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [running, setRunning] = useState(false);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dark, setDark] = useState(initialDark);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

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
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <header className="mb-6 flex items-center justify-between border-b border-zinc-200 pb-4 dark:border-zinc-800">
          <div>
            <h1 className="text-xl font-semibold">VoyageMind</h1>
            <p className="text-sm text-zinc-500">Multi-agent travel assistant · LangGraph</p>
          </div>
          <div className="flex items-center gap-3">
            {health && <span className="hidden text-xs text-zinc-500 sm:inline">{health.mode}</span>}
            <ThemeToggle dark={dark} onToggle={() => setDark((d) => !d)} />
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <div className="space-y-6">
            <PlanForm query={query} setQuery={setQuery} onSubmit={run} running={running} />
            <AgentTimeline events={events} running={running} />
          </div>

          <div>
            {error && (
              <div className="mb-4 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
                {error}
              </div>
            )}
            {itinerary ? (
              <ItineraryView it={itinerary} />
            ) : (
              <div className="flex min-h-[280px] items-center justify-center rounded-md border border-dashed border-zinc-300 p-8 text-center dark:border-zinc-700">
                <p className="max-w-sm text-sm text-zinc-500">
                  Your itinerary appears here once the orchestrator, specialists, and critic
                  finish coordinating.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
