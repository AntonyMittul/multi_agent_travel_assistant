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

  return (
    <div className="space-y-4">
      {it.summary && (
        <section className="rounded-md border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="mb-1 text-base font-semibold text-zinc-900 dark:text-zinc-100">
            {it.destination?.name ? it.destination.name : "Your itinerary"}
            {it.logistics?.flag ? ` ${it.logistics.flag}` : ""}
          </h2>
          <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
            {it.summary}
          </p>
        </section>
      )}

      {center && (
        <Card title="Map">
          <TripMap center={center} hotels={it.hotels?.options} pois={it.activities?.pois} />
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {it.destination?.name && (
          <Card title="Destination">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">{it.destination.blurb}</p>
            {it.destination.best_time && (
              <p className="mt-2 text-xs text-zinc-500">Best time: {it.destination.best_time}</p>
            )}
            {it.destination.highlights && it.destination.highlights.length > 0 && (
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {it.destination.highlights.map((h) => (
                  <li
                    key={h}
                    className="rounded border border-zinc-200 px-2 py-0.5 text-xs text-zinc-600 dark:border-zinc-700 dark:text-zinc-400"
                  >
                    {h}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        )}

        {it.weather?.available && (
          <Card title="Weather">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">{it.weather.summary}</p>
            <div className="mt-3 flex gap-2 overflow-x-auto">
              {it.weather.days?.slice(0, 7).map((d) => (
                <div
                  key={d.date}
                  className="min-w-[60px] rounded border border-zinc-200 p-2 text-center dark:border-zinc-800"
                >
                  <div className="text-[10px] text-zinc-500">{d.date.slice(5)}</div>
                  <div className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                    {Math.round(d.high_c)}°
                  </div>
                  <div className="text-[10px] text-zinc-500">{d.rain_pct}%</div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {it.flights?.options && it.flights.options.length > 0 && (
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
        )}

        {it.hotels?.options && it.hotels.options.length > 0 && (
          <Card title="Hotels">
            <div className="space-y-1.5">
              {it.hotels.options.slice(0, 4).map((h, i) => (
                <div key={i} className={ROW}>
                  <span className="truncate pr-2 text-zinc-700 dark:text-zinc-300">
                    {h.name}
                    {h.stars ? <span className="text-zinc-500"> · {h.stars}★</span> : null}
                  </span>
                  <span className="whitespace-nowrap text-zinc-800 dark:text-zinc-200">
                    ~{money(h.total_price)}
                    <span className="text-zinc-500"> /{h.nights}n</span>
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-2 text-xs text-zinc-400">{it.hotels.source}</p>
          </Card>
        )}
      </div>

      {it.activities?.plan && it.activities.plan.length > 0 && (
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
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {b?.breakdown && (
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
                  {money(total)}
                  {target ? <span className="text-zinc-500"> / {money(target)}</span> : null}
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
        )}

        {it.logistics?.available && (
          <Card title="Local logistics">
            <p className="text-sm text-zinc-600 dark:text-zinc-400">{it.logistics.summary}</p>
            {it.critic?.issues && it.critic.issues.length > 0 && (
              <div className="mt-3 rounded border border-zinc-200 p-2 text-xs text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
                <span className="font-medium">Notes: </span>
                {it.critic.issues.join(" ")}
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}
