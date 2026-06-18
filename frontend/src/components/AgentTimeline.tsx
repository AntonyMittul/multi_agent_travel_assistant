import type { AgentEvent } from "../types";
import { agentMeta } from "../lib/agents";

interface Props {
  events: AgentEvent[];
  running: boolean;
}

export default function AgentTimeline({ events, running }: Props) {
  return (
    <section className="rounded-md border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Agent activity</h2>
        {running && <span className="text-xs text-zinc-500">running…</span>}
      </div>

      {events.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Submit a trip to watch the orchestrator delegate to specialist agents.
        </p>
      ) : (
        <ul className="space-y-2">
          {events.map((e, i) => {
            const meta = agentMeta(e.agent);
            const revise = e.kind === "revise";
            return (
              <li key={i} className="flex gap-2.5 text-sm">
                <span className="mt-0.5 w-4 shrink-0 text-center text-zinc-400">{meta.icon}</span>
                <div>
                  <span className="font-medium text-zinc-800 dark:text-zinc-200">{meta.label}</span>
                  {revise && (
                    <span className="ml-2 rounded border border-amber-300 px-1.5 py-0.5 text-[10px] uppercase text-amber-700 dark:border-amber-700 dark:text-amber-400">
                      replan
                    </span>
                  )}
                  <p className="text-zinc-600 dark:text-zinc-400">{e.text}</p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
