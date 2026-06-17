import type { Itinerary } from "../types";

function Card({ title, icon, children }: { title: string; icon: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-200">
        <span>{icon}</span> {title}
      </h3>
      {children}
    </div>
  );
}

export default function ItineraryView({ it }: { it: Itinerary }) {
  const b = it.budget;
  const total = b?.total ?? 0;
  const target = b?.target ?? null;

  return (
    <div className="space-y-4">
      {it.summary && (
        <div className="rounded-2xl border border-fuchsia-500/30 bg-gradient-to-br from-fuchsia-500/10 to-indigo-500/10 p-5">
          <h2 className="mb-1 text-lg font-bold text-white">
            Your itinerary {it.destination?.name ? `— ${it.destination.name}` : ""}
          </h2>
          <p className="text-sm text-slate-200">{it.summary}</p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {/* Destination */}
        {it.destination?.name && (
          <Card title="Destination" icon="📍">
            <p className="text-sm text-slate-300">{it.destination.blurb}</p>
            {it.destination.best_time && (
              <p className="mt-2 text-xs text-slate-400">Best time: {it.destination.best_time}</p>
            )}
            {it.destination.highlights && (
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {it.destination.highlights.map((h) => (
                  <li key={h} className="rounded-full bg-rose-500/15 px-2.5 py-0.5 text-xs text-rose-200">
                    {h}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        )}

        {/* Weather */}
        {it.weather?.summary && (
          <Card title="Weather" icon="🌤️">
            <p className="text-sm text-slate-300">{it.weather.summary}</p>
            <div className="mt-3 flex gap-2 overflow-x-auto">
              {it.weather.days?.slice(0, 7).map((d) => (
                <div key={d.date} className="min-w-[64px] rounded-lg bg-slate-900/50 p-2 text-center">
                  <div className="text-[10px] text-slate-400">{d.date.slice(5)}</div>
                  <div className="text-sm font-semibold text-slate-100">{Math.round(d.high_c)}°</div>
                  <div className="text-[10px] text-sky-300">{d.rain_pct}%💧</div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Flights */}
        {it.flights?.options && (
          <Card title="Flights" icon="✈️">
            <div className="space-y-2">
              {it.flights.options.slice(0, 3).map((f, i) => (
                <div
                  key={i}
                  className={`flex items-center justify-between rounded-lg p-2 text-sm ${
                    i === 0 ? "bg-cyan-500/15 ring-1 ring-cyan-400/30" : "bg-slate-900/40"
                  }`}
                >
                  <span className="text-slate-200">
                    {f.airline} <span className="text-xs text-slate-400">· {f.stops} stop · {f.duration_h}h</span>
                  </span>
                  <span className="font-semibold text-slate-100">${f.total_price.toFixed(0)}</span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Hotels */}
        {it.hotels?.options && (
          <Card title="Hotels" icon="🏨">
            <div className="space-y-2">
              {it.hotels.options.slice(0, 3).map((h, i) => (
                <div
                  key={i}
                  className={`flex items-center justify-between rounded-lg p-2 text-sm ${
                    i === 0 ? "bg-amber-500/15 ring-1 ring-amber-400/30" : "bg-slate-900/40"
                  }`}
                >
                  <span className="text-slate-200">
                    {h.name} <span className="text-xs text-amber-300">{h.rating}★</span>
                  </span>
                  <span className="font-semibold text-slate-100">
                    ${h.total_price.toFixed(0)}
                    <span className="text-xs text-slate-400"> /{h.nights}n</span>
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Day-by-day */}
      {it.activities?.plan && (
        <Card title="Day-by-day plan" icon="🗺️">
          <div className="space-y-2">
            {it.activities.plan.map((d) => (
              <div key={d.day} className="rounded-lg bg-slate-900/40 p-3">
                <div className="mb-1 text-xs font-semibold text-emerald-300">Day {d.day}</div>
                <div className="grid gap-1 text-sm text-slate-300 sm:grid-cols-3">
                  <span>🌅 {d.morning}</span>
                  <span>☀️ {d.afternoon}</span>
                  <span>🌙 {d.evening}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {/* Budget */}
        {b?.breakdown && (
          <Card title="Budget" icon="💰">
            <div className="space-y-1.5">
              {Object.entries(b.breakdown).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-slate-400">{k.replace("_", " ")}</span>
                  <span className="text-slate-200">${Number(v).toFixed(0)}</span>
                </div>
              ))}
              <div className="mt-2 flex items-center justify-between border-t border-white/10 pt-2 text-sm font-semibold">
                <span className="text-slate-200">Total</span>
                <span className={b.over_budget ? "text-red-300" : "text-green-300"}>
                  ${total.toFixed(0)}
                  {target ? <span className="text-xs text-slate-400"> / ${target.toFixed(0)}</span> : null}
                </span>
              </div>
              {target ? (
                <div className="mt-1">
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      className={`h-full ${b.over_budget ? "bg-red-400" : "bg-green-400"}`}
                      style={{ width: `${Math.min((total / target) * 100, 100)}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-slate-400">
                    {b.over_budget
                      ? "Over budget — the critic auto-downgraded tiers to compensate."
                      : `$${(b.remaining ?? 0).toFixed(0)} under budget.`}
                  </p>
                </div>
              ) : null}
            </div>
          </Card>
        )}

        {/* Logistics */}
        {it.logistics?.summary && (
          <Card title="Local logistics" icon="🛂">
            <p className="text-sm text-slate-300">
              {it.logistics.flag} {it.logistics.summary}
            </p>
            {it.critic?.issues && it.critic.issues.length > 0 && (
              <div className="mt-3 rounded-lg bg-orange-500/10 p-2 text-xs text-orange-200">
                <span className="font-semibold">Critic notes: </span>
                {it.critic.issues.join(" ")}
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
