import { useEffect, useRef, useState } from "react";
import ItineraryView from "./components/ItineraryView";
import ThemeToggle from "./components/ThemeToggle";
import Loader from "./components/Loader";
import { getHealth, streamPlan } from "./lib/api";
import type { HealthInfo, Itinerary } from "./types";

function initialDark(): boolean {
  const saved = localStorage.getItem("theme");
  if (saved) return saved === "dark";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

const EXAMPLES = [
  "5-night trip from Mumbai to Goa for 2, budget ₹150000, love beach and food",
  "Plan a 5-night trip from Delhi to Tokyo, budget $3000, love food and culture",
  "Adventure trip with hiking and nature, 4 nights, budget €1200",
];

export default function App() {
  const [input, setInput] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [running, setRunning] = useState(false);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dark, setDark] = useState(initialDark);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [itinerary, running]);

  async function run(query: string) {
    const q = query.trim();
    if (!q || running) return;
    setSubmitted(q);
    setInput("");
    setRunning(true);
    setItinerary(null);
    setError(null);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      for await (const ev of streamPlan(q, ctrl.signal)) {
        if (ev.kind === "done" && ev.data?.itinerary) {
          setItinerary(ev.data.itinerary as Itinerary);
        } else if (ev.kind === "error") {
          setError(ev.text);
        }
        // intermediate agent events are intentionally not shown
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setRunning(false);
    }
  }

  const empty = !submitted && !running && !itinerary;

  return (
    <div className="flex h-screen flex-col bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      {/* header */}
      <header className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
        <div>
          <h1 className="text-lg font-semibold">VoyageMind</h1>
          <p className="text-xs text-zinc-500">Multi-agent travel assistant</p>
        </div>
        <div className="flex items-center gap-3">
          {health && <span className="hidden text-xs text-zinc-500 sm:inline">{health.mode}</span>}
          <ThemeToggle dark={dark} onToggle={() => setDark((d) => !d)} />
        </div>
      </header>

      {/* conversation area */}
      <main ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-4 py-6">
          {empty ? (
            <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
              <h2 className="text-2xl font-semibold">Where would you like to go?</h2>
              <p className="mt-2 max-w-md text-sm text-zinc-500">
                Describe your trip in one message — destination (or just a vibe), dates or
                nights, travelers, budget and currency. The assistant plans the rest.
              </p>
              <div className="mt-6 grid w-full max-w-lg gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => run(ex)}
                    className="rounded-md border border-zinc-200 px-3 py-2 text-left text-sm text-zinc-600 hover:bg-zinc-100 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-900"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {submitted && (
                <div className="flex justify-end">
                  <div className="max-w-[80%] rounded-lg bg-blue-600 px-3.5 py-2 text-sm text-white">
                    {submitted}
                  </div>
                </div>
              )}
              {error && (
                <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
                  {error}
                </div>
              )}
              {running && <Loader />}
              {itinerary && <ItineraryView it={itinerary} />}
            </div>
          )}
        </div>
      </main>

      {/* chat input */}
      <footer className="border-t border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto flex max-w-4xl items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                run(input);
              }
            }}
            rows={1}
            placeholder="Describe your trip…  (e.g. 5 nights in Goa from Mumbai, budget ₹150000)"
            className="max-h-40 flex-1 resize-none rounded-lg border border-zinc-300 bg-white px-3.5 py-2.5 text-sm text-zinc-900 outline-none placeholder:text-zinc-400 focus:border-blue-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
          />
          <button
            onClick={() => run(input)}
            disabled={running || !input.trim()}
            className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? "…" : "Send"}
          </button>
        </div>
      </footer>
    </div>
  );
}
