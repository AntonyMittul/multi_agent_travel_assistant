import { useState } from "react";
import type { Itinerary } from "../types";
import TripMap from "./TripMap";

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-md border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">{title}</h3>
      {children}
    </section>
  );
}

const ROW = "flex items-center justify-between text-sm";

export default function ItineraryView({ it }: { it: Itinerary }) {
  const sym = it.currency?.symbol ?? "$";
  const money = (v: number | undefined | null) =>
    `${sym}${Math.round(v ?? 0).toLocaleString()}`;

  const b = it.budget;
  const total = b?.total ?? 0;
  const target = b?.target ?? null;
  const geo = it.destination?.geo;
  const center: [number, number] | null =
    geo?.lat != null && geo?.lon != null ? [geo.lat, geo.lon] : null;
  const places = it.activities?.pois ?? [];

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const prefs = (it.preferences ?? {}) as Record<string, any>;
  const nights = Number(prefs.nights) || it.hotels?.best_value?.nights;
  const travelers = Number(prefs.travelers);
  const temp = it.weather?.avg_high_c;
  const styleIcon: Record<string, string> = {
    budget: "💸", luxury: "✨", family: "👨‍👩‍👧", adventure: "🏔", solo: "🎒", business: "💼",
  };
  const style = prefs.style ? String(prefs.style) : "";
  const stats = [
    it.destination?.name && { icon: "📍", value: it.destination.name.split(",")[0], label: "Destination" },
    style && { icon: styleIcon[style] ?? "🎒", value: style.charAt(0).toUpperCase() + style.slice(1), label: "Style" },
    nights && { icon: "🗓", value: `${nights + 1}`, label: "Days" },
    nights && { icon: "🏨", value: `${nights}`, label: "Nights" },
    travelers && { icon: "👥", value: `${travelers}`, label: travelers > 1 ? "Travelers" : "Traveler" },
    b?.total != null && { icon: "💰", value: money(b.total), label: "Est. total" },
    temp != null && { icon: "🌤", value: `${Math.round(temp)}°C`, label: "Avg high" },
    places.length > 0 && { icon: "📌", value: `${places.length}`, label: "Attractions" },
  ].filter(Boolean) as { icon: string; value: string; label: string }[];

  // ── card fragments ───────────────────────────────────────────────────────
  const destinationCard = it.destination?.name && (
    <Card title="Destination">
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{it.destination.blurb}</p>
      {it.destination.best_time && (
        <p className="mt-2 text-xs text-zinc-500">Best time: {it.destination.best_time}</p>
      )}
      {it.destination.highlights && it.destination.highlights.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {it.destination.highlights.map((h) => (
            <li key={h} className="rounded border border-zinc-200 px-2 py-0.5 text-xs text-zinc-600 dark:border-zinc-700 dark:text-zinc-400">
              {h}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );

  const weatherCard = it.weather?.available && (
    <Card title="Weather">
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{it.weather.summary}</p>
      <div className="mt-3 flex gap-2 overflow-x-auto">
        {it.weather.days?.slice(0, 7).map((d) => (
          <div key={d.date} className="min-w-[60px] rounded border border-zinc-200 p-2 text-center dark:border-zinc-800">
            <div className="text-[10px] text-zinc-500">{d.date.slice(5)}</div>
            <div className="text-sm font-medium text-zinc-800 dark:text-zinc-200">{Math.round(d.high_c)}°</div>
            <div className="text-[10px] text-zinc-500">{d.rain_pct}%</div>
          </div>
        ))}
      </div>
    </Card>
  );

  const placesCard = places.length > 0 && (
    <Card title="Places you'll see">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {places.slice(0, 6).map((p, i) => (
          <figure key={p.name} className="relative overflow-hidden rounded-md border border-zinc-200 dark:border-zinc-800">
            <span className="absolute left-2 top-2 z-[1] flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-blue-600 text-xs font-semibold text-white shadow">
              {i + 1}
            </span>
            {p.image ? (
              <img src={p.image} alt={p.name} className="h-28 w-full object-cover" loading="lazy" />
            ) : (
              <div className="flex h-28 w-full items-center justify-center bg-zinc-100 text-3xl dark:bg-zinc-800">
                {p.icon || "📍"}
              </div>
            )}
            <figcaption className="px-2.5 py-2">
              <div className="truncate text-sm font-medium text-zinc-800 dark:text-zinc-200">{p.name}</div>
              {p.tag && (
                <div className="mt-1 inline-block rounded bg-blue-50 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                  {p.icon ? `${p.icon} ` : ""}{p.tag}
                </div>
              )}
              {p.category && <div className="mt-1 text-xs text-zinc-500">{p.category}</div>}
            </figcaption>
          </figure>
        ))}
      </div>
    </Card>
  );

  const flightsCard = it.flights?.options && it.flights.options.length > 0 && (
    <Card title={`Flights · ${it.flights.route ?? ""}`}>
      <div className="space-y-1.5">
        {it.flights.options.slice(0, 3).map((f, i) => (
          <div key={i} className={ROW}>
            <span className="text-zinc-700 dark:text-zinc-300">
              {f.airline}
              {f.depart_time ? <span className="text-zinc-500"> · {f.depart_time}</span> : null}
            </span>
            <span className="text-zinc-800 dark:text-zinc-200">~{money(f.total_price)}</span>
          </div>
        ))}
      </div>
      <p className="mt-2 text-xs text-zinc-400">{it.flights.source} · prices estimated</p>
    </Card>
  );

  const hotelsCard = it.hotels?.options && it.hotels.options.length > 0 && (
    <Card title="Hotels">
      <div className="space-y-1.5">
        {it.hotels.options.slice(0, 4).map((h, i) => (
          <div key={i} className={ROW}>
            <span className="truncate pr-2 text-zinc-700 dark:text-zinc-300">
              {h.name}
              {h.stars ? <span className="text-zinc-500"> · {h.stars}★</span> : null}
            </span>
            <span className="whitespace-nowrap text-zinc-800 dark:text-zinc-200">
              ~{money(h.total_price)}<span className="text-zinc-500"> /{h.nights}n</span>
            </span>
          </div>
        ))}
      </div>
      <p className="mt-2 text-xs text-zinc-400">{it.hotels.source}</p>
    </Card>
  );

  const dayPlanCard = it.activities?.plan && it.activities.plan.length > 0 && (
    <Card title="Day-by-day plan">
      <div className="space-y-2">
        {it.activities.plan.map((d) => (
          <div key={d.day} className="rounded border border-zinc-200 p-3 dark:border-zinc-800">
            <div className="mb-1 text-xs font-medium text-zinc-500">Day {d.day}</div>
            <div className="grid gap-1 text-sm text-zinc-700 sm:grid-cols-3 dark:text-zinc-300">
              <span>AM · {d.morning}</span>
              <span>PM · {d.afternoon}</span>
              <span>Eve · {d.evening}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );

  const budgetCard = b?.breakdown && (
    <Card title="Budget (estimated)">
      <div className="space-y-1">
        {Object.entries(b.breakdown).map(([k, v]) => (
          <div key={k} className={ROW}>
            <span className="capitalize text-zinc-500">{k.replace("_", " ")}</span>
            <span className="text-zinc-700 dark:text-zinc-300">{money(Number(v))}</span>
          </div>
        ))}
        <div className="mt-2 flex items-center justify-between border-t border-zinc-200 pt-2 text-sm font-medium dark:border-zinc-800">
          <span className="text-zinc-700 dark:text-zinc-300">Total</span>
          <span className={b.over_budget ? "text-red-600 dark:text-red-400" : "text-zinc-900 dark:text-zinc-100"}>
            {money(total)}{target ? <span className="text-zinc-500"> / {money(target)}</span> : null}
          </span>
        </div>
        {target ? (
          <div className="mt-2">
            <div className="h-1.5 w-full overflow-hidden rounded bg-zinc-200 dark:bg-zinc-800">
              <div
                className={b.over_budget ? "h-full bg-red-500" : "h-full bg-blue-600"}
                style={{ width: `${Math.min((total / target) * 100, 100)}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-zinc-400">
              {b.over_budget
                ? "Over budget — the planner auto-downgraded tiers to compensate."
                : `${money(b.remaining)} under budget.`}
            </p>
          </div>
        ) : null}
      </div>
    </Card>
  );

  const logisticsCard = it.logistics?.available && (
    <Card title="Local logistics">
      <p className="text-sm text-zinc-600 dark:text-zinc-400">{it.logistics.summary}</p>
      {it.critic?.issues && it.critic.issues.length > 0 && (
        <div className="mt-3 rounded border border-zinc-200 p-2 text-xs text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
          <span className="font-medium">Notes: </span>{it.critic.issues.join(" ")}
        </div>
      )}
    </Card>
  );

  const agentLog = it.agent_log && it.agent_log.length > 0 && (
    <details className="group rounded-md border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">
        <span className="transition-transform group-open:rotate-90">▸</span>
        <span>🧠 Agent activity</span>
        <span className="ml-auto text-xs font-normal text-zinc-400">{it.agent_log.length} steps</span>
      </summary>
      <ul className="space-y-2 border-t border-zinc-200 px-4 py-3 dark:border-zinc-800">
        {it.agent_log.map((a, i) => (
          <li key={i} className="flex gap-2 text-sm">
            <span className="text-green-600 dark:text-green-400">✓</span>
            <span>
              <span className="font-medium text-zinc-800 dark:text-zinc-200">{a.label}</span>
              <span className="text-zinc-600 dark:text-zinc-400"> — {a.detail}</span>
            </span>
          </li>
        ))}
      </ul>
    </details>
  );

  // ── tabs ───────────────────────────────────────────────────────────────
  const tabs = [
    { key: "overview", label: "Overview" },
    (dayPlanCard || flightsCard || hotelsCard) && { key: "itinerary", label: "Itinerary" },
    budgetCard && { key: "budget", label: "Budget" },
    center && { key: "map", label: "Map" },
  ].filter(Boolean) as { key: string; label: string }[];

  const [tab, setTab] = useState("overview");

  return (
    <div className="space-y-4">
      {it.summary && (
        <section className="overflow-hidden rounded-md border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
          {it.destination?.image && (
            <img src={it.destination.image} alt={it.destination?.name ?? "destination"} className="h-44 w-full object-cover" loading="lazy" />
          )}
          <div className="p-4">
            <h2 className="mb-1 text-base font-semibold text-zinc-900 dark:text-zinc-100">
              {it.destination?.name ? it.destination.name : "Your itinerary"}
              {it.logistics?.flag ? ` ${it.logistics.flag}` : ""}
            </h2>
            <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">{it.summary}</p>
          </div>
        </section>
      )}

      {stats.length > 0 && (
        <section className="rounded-md border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <h3 className="mb-3 text-sm font-medium text-zinc-700 dark:text-zinc-300">Trip overview</h3>
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
            {stats.map((s) => (
              <div key={s.label} className="flex flex-col items-center rounded-md border border-zinc-200 px-2 py-3 text-center dark:border-zinc-800">
                <span className="text-xl">{s.icon}</span>
                <span className="mt-1 truncate text-sm font-semibold text-zinc-900 dark:text-zinc-100">{s.value}</span>
                <span className="text-[11px] text-zinc-500">{s.label}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* tab bar */}
      <div className="flex gap-1 border-b border-zinc-200 dark:border-zinc-800">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={
              "-mb-px border-b-2 px-3.5 py-2 text-sm font-medium transition " +
              (tab === t.key
                ? "border-blue-600 text-blue-600 dark:text-blue-400"
                : "border-transparent text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200")
            }
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* tab panels */}
      {tab === "overview" && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {destinationCard}
            {weatherCard}
          </div>
          {placesCard}
          {logisticsCard}
          {agentLog}
        </div>
      )}

      {tab === "itinerary" && (
        <div className="space-y-4">
          {dayPlanCard}
          <div className="grid gap-4 md:grid-cols-2">
            {flightsCard}
            {hotelsCard}
          </div>
        </div>
      )}

      {tab === "budget" && <div className="space-y-4">{budgetCard}</div>}

      {tab === "map" && center && (
        <Card title="Map">
          <TripMap center={center} attractions={places} hotels={it.hotels?.options} />
        </Card>
      )}
    </div>
  );
}
