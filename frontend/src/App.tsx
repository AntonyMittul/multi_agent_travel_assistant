import { useEffect, useRef, useState } from "react";
import ItineraryView from "./components/ItineraryView";
import ThemeToggle from "./components/ThemeToggle";
import Loader from "./components/Loader";
import Background from "./components/Background";
import HeroGlobe from "./components/HeroGlobe";
import { getHealth, sendChat } from "./lib/api";
import type { ChatTurn, HealthInfo, Itinerary } from "./types";

function initialDark(): boolean {
  const saved = localStorage.getItem("theme");
  if (saved) return saved === "dark";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? true;
}

const EXAMPLES = [
  "5-night trip from Mumbai to Goa for 2, budget ₹150000, love beach and food",
  "I want a relaxing beach holiday next month, not sure where",
  "Plan 4 days in Tokyo, budget $2500, into food and culture",
];

const REFINE_CHIPS = [
  "Show different attractions",
  "Add more food spots",
  "Add some nightlife",
  "Make it more relaxed",
  "More offbeat / hidden gems",
];

const STYLES = [
  { key: "budget", label: "Budget", icon: "💸" },
  { key: "luxury", label: "Luxury", icon: "✨" },
  { key: "family", label: "Family", icon: "👨‍👩‍👧" },
  { key: "adventure", label: "Adventure", icon: "🏔" },
  { key: "solo", label: "Solo", icon: "🎒" },
  { key: "business", label: "Business", icon: "💼" },
];

const FLOAT_CARDS = [
  { icon: "✈️", label: "Flights", sub: "routes & fares", cls: "left-0 top-4", delay: "0s" },
  { icon: "🏨", label: "Hotels", sub: "real listings", cls: "right-0 top-16", delay: "1.2s" },
  { icon: "🌤️", label: "Weather", sub: "7-day forecast", cls: "left-6 bottom-8", delay: "0.6s" },
  { icon: "💰", label: "Budget", sub: "auto-balanced", cls: "right-4 bottom-2", delay: "1.8s" },
];

const GLASS = "border border-zinc-200/70 bg-white/70 backdrop-blur-xl dark:border-white/10 dark:bg-white/[0.04]";

export default function App() {
  const [input, setInput] = useState("");
  const [style, setStyle] = useState<string | null>(null);
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
      const lastItin = [...history].reverse().find((m) => m.role === "assistant" && m.itinerary)?.itinerary;
      const previous = lastItin
        ? {
            destination: lastItin.destination?.name ?? null,
            attractions: (lastItin.activities?.pois ?? []).map((p) => p.name),
          }
        : null;
      const res = await sendChat(wire, style, previous);
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
  const keyWarn = health && (!health.gemini.ok || !health.opencage.ok) ? health : null;

  return (
    <div className="relative flex h-screen flex-col text-zinc-900 dark:text-zinc-100">
      <Background dark={dark} />

      <header className={`flex items-center justify-between px-5 py-3.5 ${GLASS} border-x-0 border-t-0`}>
        <div className="flex items-center gap-3">
          <img
            src="/logo.svg"
            alt="Navora"
            className="h-11 w-11 rounded-xl drop-shadow-[0_0_12px_rgba(212,175,55,0.45)]"
          />
          <div className="leading-tight">
            <h1 className="text-xl font-semibold tracking-tight">Navora</h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Plan smarter. Travel better.</p>
          </div>
        </div>
        <ThemeToggle dark={dark} onToggle={() => setDark((d) => !d)} />
      </header>

      {keyWarn && showBanner && (
        <div className="flex items-start justify-between gap-3 border-b border-amber-300/60 bg-amber-50/80 px-4 py-2 text-xs text-amber-800 backdrop-blur dark:border-amber-500/30 dark:bg-amber-950/40 dark:text-amber-300">
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
            <div className="relative isolate mx-auto flex min-h-[72vh] max-w-2xl flex-col items-center justify-center text-center">
              <HeroGlobe />
              {FLOAT_CARDS.map((c) => (
                <div
                  key={c.label}
                  className={`vm-float pointer-events-none absolute hidden items-center gap-2 rounded-xl px-3 py-2 lg:flex ${GLASS} ${c.cls}`}
                  style={{ animationDelay: c.delay }}
                >
                  <span className="text-lg">{c.icon}</span>
                  <span className="text-left">
                    <span className="block text-xs font-medium text-zinc-800 dark:text-zinc-100">{c.label}</span>
                    <span className="block text-[10px] text-zinc-500 dark:text-zinc-400">{c.sub}</span>
                  </span>
                </div>
              ))}

              <span className="mb-5 rounded-full border border-white/15 bg-white/60 px-3 py-1 text-xs text-blue-600 backdrop-blur dark:bg-white/5 dark:text-cyan-300">
                ✦ Powered by collaborating AI agents
              </span>
              <h2 className="bg-gradient-to-r from-blue-600 via-cyan-500 to-indigo-500 bg-clip-text text-4xl font-bold tracking-tight text-transparent sm:text-5xl dark:from-blue-400 dark:via-cyan-300 dark:to-indigo-300">
                Your next journey starts here.
              </h2>
              <p className="mt-4 max-w-md text-sm text-zinc-600 dark:text-zinc-400">
                Tell me about your trip — a destination or just a vibe, how long, who's going,
                and your budget. I'll ask if I need more, then plan it end to end.
              </p>
              <div className="mt-8 grid w-full max-w-lg gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex}
                    onClick={() => send(ex)}
                    className={`rounded-xl px-4 py-2.5 text-left text-sm text-zinc-700 transition hover:border-blue-400/60 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-white ${GLASS}`}
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
                    <div className="max-w-[80%] rounded-2xl bg-blue-600 px-3.5 py-2 text-sm text-white shadow-lg shadow-blue-600/20">
                      {m.content}
                    </div>
                  </div>
                ) : (
                  <div key={i} className="space-y-3">
                    {m.content && (
                      <div className={`max-w-[90%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed text-zinc-800 dark:text-zinc-200 ${GLASS}`}>
                        {m.content}
                      </div>
                    )}
                    {m.itinerary && <ItineraryView it={m.itinerary as Itinerary} />}
                    {m.itinerary && i === messages.length - 1 && !running && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        <span className="self-center text-xs text-zinc-500">Refine:</span>
                        {REFINE_CHIPS.map((c) => (
                          <button
                            key={c}
                            onClick={() => send(c)}
                            className={`rounded-full px-2.5 py-1 text-xs text-zinc-600 transition hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white ${GLASS}`}
                          >
                            {c}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )
              )}
              {running && <Loader />}
            </div>
          )}
        </div>
      </main>

      <footer className={`px-4 py-3 ${GLASS} border-x-0 border-b-0`}>
        <div className="mx-auto mb-2 flex max-w-4xl flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs text-zinc-500">Travel style:</span>
          {STYLES.map((s) => {
            const active = style === s.key;
            return (
              <button
                key={s.key}
                onClick={() => setStyle(active ? null : s.key)}
                className={
                  "rounded-full border px-2.5 py-1 text-xs transition " +
                  (active
                    ? "border-blue-500 bg-blue-600 text-white shadow shadow-blue-600/30"
                    : "border-zinc-300/70 text-zinc-600 hover:bg-white/60 dark:border-white/10 dark:text-zinc-400 dark:hover:bg-white/10")
                }
              >
                {s.icon} {s.label}
              </button>
            );
          })}
        </div>
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
            placeholder="Message Navora…  (e.g. 5 nights in Goa from Mumbai, budget ₹150000)"
            className="max-h-40 flex-1 resize-none rounded-xl border border-zinc-300/70 bg-white/80 px-3.5 py-2.5 text-sm text-zinc-900 outline-none backdrop-blur placeholder:text-zinc-400 focus:border-blue-500 dark:border-white/10 dark:bg-white/5 dark:text-zinc-100"
          />
          <button
            onClick={() => send(input)}
            disabled={running || !input.trim()}
            className="rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-blue-600/25 transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {running ? "…" : "Send"}
          </button>
        </div>
      </footer>
    </div>
  );
}
