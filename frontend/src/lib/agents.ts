// Minimal display metadata per agent — icon + label only (no decorative color).
export interface AgentMeta {
  label: string;
  icon: string;
}

export const AGENTS: Record<string, AgentMeta> = {
  orchestrator: { label: "Orchestrator", icon: "◆" },
  destination: { label: "Destination", icon: "◉" },
  weather: { label: "Weather", icon: "☂" },
  flight: { label: "Flights", icon: "✈" },
  hotel: { label: "Hotels", icon: "⌂" },
  activities: { label: "Activities", icon: "❖" },
  logistics: { label: "Logistics", icon: "⚐" },
  budget: { label: "Budget", icon: "▤" },
  critic: { label: "Critic", icon: "✓" },
  finalize: { label: "Finalize", icon: "★" },
  system: { label: "System", icon: "•" },
};

export function agentMeta(name: string): AgentMeta {
  return AGENTS[name] ?? { label: name, icon: "•" };
}
