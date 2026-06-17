import type { AgentEvent } from "../types";
import { agentMeta } from "../lib/agents";

interface Props {
  events: AgentEvent[];
  running: boolean;
}

const KIND_BADGE: Record<string, string> = {
  plan: "bg-indigo-500/20 text-indigo-200",
  route: "bg-slate-500/20 text-slate-300",
  result: "bg-emerald-500/20 text-emerald-200",
  revise: "bg-orange-500/20 text-orange-200",
  approve: "bg-green-500/20 text-green-200",
  final: "bg-fuchsia-500/20 text-fuchsia-200",
  error: "bg-red-500/20 text-red-200",
};

export default function AgentTimeline({ events, running }: Props) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-200">Agent activity</h2>
        {running && (
          <span className="flex items-center gap-2 text-xs text-indigo-300">
            <span className="h-2 w-2 animate-pulse rounded-full bg-indigo-400" />
            live
          </span>
        )}
      </div>

      {events.length === 0 && (
        <p className="text-sm text-slate-500">
          Submit a trip to watch the orchestrator delegate to specialist agents in real time.
        </p>
      )}

      <ol className="relative space-y-3 border-l border-white/10 pl-5">
        {events.map((e, i) => {
          const meta = agentMeta(e.agent);
          return (
            <li key={i} className="relative">
              <span className="absolute -left-[27px] flex h-5 w-5 items-center justify-center rounded-full bg-slate-900 text-xs ring-1 ring-white/10">
                {meta.icon}
              </span>
              <div className={`rounded-xl border bg-slate-900/40 p-3 ${meta.color}`}>
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-xs font-semibold">{meta.label}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide ${
                      KIND_BADGE[e.kind] ?? "bg-slate-500/20 text-slate-300"
                    }`}
                  >
                    {e.kind}
                  </span>
                </div>
                <p className="text-sm text-slate-200">{e.text}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
