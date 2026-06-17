// Display metadata for each agent — icon, label, accent color.
export interface AgentMeta {
  label: string;
  icon: string;
  color: string; // tailwind text/border accent
}

export const AGENTS: Record<string, AgentMeta> = {
  orchestrator: { label: "Orchestrator", icon: "🧭", color: "text-indigo-300 border-indigo-500/40" },
  destination: { label: "Destination", icon: "📍", color: "text-rose-300 border-rose-500/40" },
  weather: { label: "Weather", icon: "🌤️", color: "text-sky-300 border-sky-500/40" },
  flight: { label: "Flights", icon: "✈️", color: "text-cyan-300 border-cyan-500/40" },
  hotel: { label: "Hotels", icon: "🏨", color: "text-amber-300 border-amber-500/40" },
  activities: { label: "Activities", icon: "🗺️", color: "text-emerald-300 border-emerald-500/40" },
  logistics: { label: "Logistics", icon: "🛂", color: "text-violet-300 border-violet-500/40" },
  budget: { label: "Budget", icon: "💰", color: "text-lime-300 border-lime-500/40" },
  critic: { label: "Critic", icon: "🧐", color: "text-orange-300 border-orange-500/40" },
  finalize: { label: "Finalize", icon: "✅", color: "text-green-300 border-green-500/40" },
  system: { label: "System", icon: "⚙️", color: "text-slate-300 border-slate-500/40" },
};

export function agentMeta(name: string): AgentMeta {
  return AGENTS[name] ?? { label: name, icon: "•", color: "text-slate-300 border-slate-500/40" };
}
