import { afterEach, describe, expect, it, vi } from "vitest";

import { submitTicket, type TicketResult } from "./api";

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("submitTicket posts the message and returns the parsed result", async () => {
    const result: TicketResult = {
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
    };
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
});
