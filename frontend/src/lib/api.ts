import type { AgentEvent, HealthInfo } from "../types";

export async function getHealth(): Promise<HealthInfo> {
  const res = await fetch("/api/health");
  return res.json();
}

/** Stream the planning run, yielding each agent event as it arrives (SSE). */
export async function* streamPlan(
  query: string,
  signal?: AbortSignal
): AsyncGenerator<AgentEvent> {
  const res = await fetch("/api/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`Request failed: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const dataLine = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!dataLine) continue;
      const payload = dataLine.slice(5).trim();
      if (payload) {
        try {
          yield JSON.parse(payload) as AgentEvent;
        } catch {
          // ignore malformed frame
        }
      }
    }
  }
}
