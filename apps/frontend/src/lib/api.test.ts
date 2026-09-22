import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchTicketQueue, resolveTicket, submitTicket, type TicketResult } from "./api";

function makeResult(overrides: Partial<TicketResult> = {}): TicketResult {
  return {
    id: "11111111-1111-1111-1111-111111111111",
    message: "I was charged twice for my subscription this month.",
    classification: { category: "billing", priority: "high", sentiment: "frustrated" },
    response: {
      answer: "You're eligible for a refund.",
      sources: ["refund_policy.md"],
      grounded: true,
      top_rerank_score: 5.9,
      context: "policy text",
    },
    faithfulness: { is_faithful: true, unsupported_claims: [] },
    escalation: "none",
    escalation_reasons: [],
    token_usage: null,
    status: "auto_resolved",
    created_at: "2026-09-22T12:00:00Z",
    resolved_at: null,
    resolution_notes: null,
    ...overrides,
  };
}

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submitTicket posts the message and returns the parsed result", async () => {
    const result = makeResult();
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => result });
    vi.stubGlobal("fetch", fetchMock);

    await expect(submitTicket("I was charged twice")).resolves.toEqual(result);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/tickets");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ message: "I was charged twice" });
  });

  it("submitTicket throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({}) }),
    );

    await expect(submitTicket("hello")).rejects.toThrow("Ticket submission failed: 500");
  });

  it("fetchTicketQueue requests the pending_review status by default", async () => {
    const tickets = [makeResult({ status: "pending_review" })];
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => tickets });
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchTicketQueue()).resolves.toEqual(tickets);

    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/tickets?status=pending_review");
  });

  it("resolveTicket posts notes and returns the resolved ticket", async () => {
    const result = makeResult({ status: "resolved", resolution_notes: "Confirmed refund manually." });
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => result });
    vi.stubGlobal("fetch", fetchMock);

    await expect(resolveTicket(result.id, "Confirmed refund manually.")).resolves.toEqual(result);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`http://localhost:8000/api/tickets/${result.id}/resolve`);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ notes: "Confirmed refund manually." });
  });
});
