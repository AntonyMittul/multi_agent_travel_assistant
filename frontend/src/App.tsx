import { useEffect, useRef, useState } from "react";
import ItineraryView from "./components/ItineraryView";
import ThemeToggle from "./components/ThemeToggle";
import Loader from "./components/Loader";
import { getHealth, sendChat } from "./lib/api";
import type { ChatTurn, HealthInfo, Itinerary } from "./types";

function initialDark(): boolean {
  const saved = localStorage.getItem("theme");
  if (saved) return saved === "dark";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
}

const EXAMPLES = [
  "5-night trip from Mumbai to Goa for 2, budget ₹150000, love beach and food",
  "I want a relaxing beach holiday next month, not sure where",
  "Plan 4 days in Tokyo, budget $2500, into food and culture",
];

export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [running, setRunning] = useState(false);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [showBanner, setShowBanner] = useState(true);
  const [dark, setDark] = useState(initialDark);
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
  }, [messages, running]);

  async function send(text: string) {
    const q = text.trim();
    if (!q || running) return;
    const history = [...messages, { role: "user" as const, content: q }];
    setMessages(history);
    setInput("");
    setRunning(true);

    try {
      const wire = history
        .filter((m) => m.content)
        .map((m) => ({ role: m.role, content: m.content as string }));
      const res = await sendChat(wire);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.content, itinerary: res.itinerary },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: e instanceof Error ? e.message : "Request failed" },
      ]);
    } finally {
      setRunning(false);
    }
  }

  const empty = messages.length === 0;
  const keyWarn =
    health && (!health.gemini.ok || !health.opencage.ok) ? health : null;

  return (
    <div className="flex h-screen flex-col bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <header className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
        <div>
          <h1 className="text-lg font-semibold">VoyageMind</h1>
          <p className="text-xs text-zinc-500">Your travel planning assistant</p>
        </div>
        <div className="flex items-center gap-3">
          {health && <span className="hidden text-xs text-zinc-500 sm:inline">{health.mode}</span>}
          <ThemeToggle dark={dark} onToggle={() => setDark((d) => !d)} />
        </div>
      </header>

      {keyWarn && showBanner && (
        <div className="flex items-start justify-between gap-3 border-b border-amber-300 bg-amber-50 px-4 py-2 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-300">
          <div>
            <span className="font-medium">Setup needed: </span>
            {!keyWarn.gemini.ok && (
              <span>
                Gemini {keyWarn.gemini.key_present ? `key set but failing (${keyWarn.gemini.error ?? "error"})` : "key missing"} — replies use built-in fallbacks.{" "}
              </span>
            )}
            {!keyWarn.opencage.ok && (
              <span>
                OpenCage {keyWarn.opencage.key_present ? "key set but failing" : "key missing"} — weather, hotels, map &amp; places will be empty.
              </span>
            )}
            <span className="block opacity-80">Add keys to backend/.env and restart the server.</span>
          </div>
          <button onClick={() => setShowBanner(false)} className="shrink-0 font-medium">✕</button>
        </div>
      )}

      <main ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl px-4 py-6">
          {empty ? (
            <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
              <h2 className="text-2xl font-semibold">Where would you like to go?</h2>
              <p className="mt-2 max-w-md text-sm text-zinc-500">
                Tell me about your trip — a destination or just a vibe, how long, who's going,
                and your budget. I'll ask if I need more, then plan it.
              </p>
              <div className="mt-6 grid w-full max-w-lg gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => send(ex)}
                    className="rounded-md border border-zinc-200 px-3 py-2 text-left text-sm text-zinc-600 hover:bg-zinc-100 dark:border-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-900"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((m, i) =>
                m.role === "user" ? (
                  <div key={i} className="flex justify-end">
                    <div className="max-w-[80%] rounded-lg bg-blue-600 px-3.5 py-2 text-sm text-white">
                      {m.content}
                    </div>
                  </div>
                ) : (
                  <div key={i} className="space-y-3">
                    {m.content && (
                      <div className="max-w-[90%] rounded-lg bg-white px-3.5 py-2.5 text-sm leading-relaxed text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200">
                        {m.content}
                      </div>
                    )}
                    {m.itinerary && <ItineraryView it={m.itinerary as Itinerary} />}
                  </div>
                )
              )}
              {running && <Loader />}
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-zinc-200 bg-zinc-50 px-4 py-3 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto flex max-w-4xl items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            rows={1}
            placeholder="Message VoyageMind…  (e.g. 5 nights in Goa from Mumbai, budget ₹150000)"
            className="max-h-40 flex-1 resize-none rounded-lg border border-zinc-300 bg-white px-3.5 py-2.5 text-sm text-zinc-900 outline-none placeholder:text-zinc-400 focus:border-blue-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
          />
          <button
            onClick={() => send(input)}
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
