export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export type TicketCategory = "billing" | "shipping" | "product" | "account" | "other";
export type TicketPriority = "low" | "medium" | "high";
export type TicketSentiment = "positive" | "neutral" | "frustrated" | "angry";
export type EscalationLevel = "none" | "review" | "immediate";

export interface TicketClassification {
  category: TicketCategory;
  priority: TicketPriority;
  sentiment: TicketSentiment;
}

export interface SupportResponse {
  answer: string;
  sources: string[];
  grounded: boolean;
  top_rerank_score: number | null;
  context: string;
}

export interface FaithfulnessVerdict {
  is_faithful: boolean;
  unsupported_claims: string[];
}

export type TicketStatus = "auto_resolved" | "pending_review" | "resolved";

export interface TicketResult {
  id: string;
  message: string;
  classification: TicketClassification;
  response: SupportResponse;
  faithfulness: FaithfulnessVerdict | null;
  escalation: EscalationLevel;
  escalation_reasons: string[];
  status: TicketStatus;
  created_at: string;
  resolved_at: string | null;
  resolution_notes: string | null;
}

export async function submitTicket(message: string): Promise<TicketResult> {
  const res = await fetch(`${getApiUrl()}/api/tickets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Ticket submission failed: ${res.status}`);
  return res.json();
}

export async function fetchTicketQueue(status: TicketStatus = "pending_review"): Promise<TicketResult[]> {
  const res = await fetch(`${getApiUrl()}/api/tickets?status=${status}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Fetching tickets failed: ${res.status}`);
  return res.json();
}

export async function resolveTicket(ticketId: string, notes: string | null): Promise<TicketResult> {
  const res = await fetch(`${getApiUrl()}/api/tickets/${ticketId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notes }),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Resolving ticket failed: ${res.status}`);
  return res.json();
}

export type PipelineStage = "classify" | "respond" | "clarify" | "check_faithfulness" | "validate";

export type StreamEvent =
  | { type: "stage"; stage: PipelineStage }
  | { type: "result"; result: TicketResult };

export async function* streamTicket(message: string): AsyncGenerator<StreamEvent> {
  const res = await fetch(`${getApiUrl()}/api/tickets/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
    cache: "no-store",
  });
  if (!res.ok || !res.body) throw new Error(`Ticket submission failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let separatorIndex = buffer.indexOf("\n\n");
    while (separatorIndex !== -1) {
      const event = parseSseEvent(buffer.slice(0, separatorIndex));
      buffer = buffer.slice(separatorIndex + 2);
      if (event) yield event;
      separatorIndex = buffer.indexOf("\n\n");
    }
  }
}

function parseSseEvent(raw: string): StreamEvent | null {
  let eventType = "";
  let data = "";
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) eventType = line.slice("event:".length).trim();
    else if (line.startsWith("data:")) data += line.slice("data:".length).trim();
  }
  if (!data) return null;

  const payload = JSON.parse(data);
  if (eventType === "stage") return { type: "stage", stage: payload.stage as PipelineStage };
  if (eventType === "result") return { type: "result", result: payload as TicketResult };
  return null;
}
