export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export interface HealthResponse {
  status: string;
}

export interface ReadinessResponse {
  status: string;
  database: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${getApiUrl()}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const res = await fetch(`${getApiUrl()}/health/ready`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Readiness check failed: ${res.status}`);
  return res.json();
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

export interface TicketResult {
  classification: TicketClassification;
  response: SupportResponse;
  faithfulness: FaithfulnessVerdict | null;
  escalation: EscalationLevel;
  escalation_reasons: string[];
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
