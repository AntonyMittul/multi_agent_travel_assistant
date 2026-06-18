import type { HealthInfo, Itinerary } from "../types";

/** Request a PDF of the trip plan and return it as a Blob. */
export async function exportPdf(itinerary: Itinerary): Promise<Blob> {
  const res = await fetch("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ itinerary }),
  });
  if (!res.ok) {
    let detail = `Export failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error */
    }
    throw new Error(detail);
  }
  return res.blob();
}

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
  style?: string | null,
  signal?: AbortSignal
): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, style: style ?? null }),
    signal,
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}
