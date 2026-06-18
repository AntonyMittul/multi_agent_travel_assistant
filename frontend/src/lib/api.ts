import type { HealthInfo, Itinerary } from "../types";

export async function getHealth(): Promise<HealthInfo> {
  const res = await fetch("/api/health");
  return res.json();
}

export interface ChatResponse {
  kind: "message" | "plan";
  content: string;
  itinerary?: Itinerary;
}

/** Send the conversation; backend either asks a follow-up or returns a plan. */
export async function sendChat(
  messages: { role: string; content: string }[],
  signal?: AbortSignal
): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
    signal,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}
