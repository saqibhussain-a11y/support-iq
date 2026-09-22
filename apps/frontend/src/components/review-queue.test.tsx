import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { TicketResult } from "@/lib/api";
import { ReviewQueue } from "./review-queue";

function makeTicket(overrides: Partial<TicketResult> = {}): TicketResult {
  return {
    id: "22222222-2222-2222-2222-222222222222",
    message: "can I get a discount for referring a friend?",
    classification: { category: "other", priority: "low", sentiment: "neutral" },
    response: {
      answer: "Could you share a bit more detail about your issue so I can help?",
      sources: [],
      grounded: false,
      top_rerank_score: null,
      context: "",
    },
    faithfulness: null,
    escalation: "review",
    escalation_reasons: ["no documented policy matched this request; needs human triage"],
    status: "pending_review",
    created_at: "2026-09-22T12:00:00Z",
    resolved_at: null,
    resolution_notes: null,
    ...overrides,
  };
}

describe("ReviewQueue", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows an empty state when there are no pending tickets", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [] }));

    render(<ReviewQueue />);

    expect(await screen.findByText("Nothing waiting on review right now.")).toBeInTheDocument();
  });

  it("lists pending tickets with their escalation reasons", async () => {
    const ticket = makeTicket();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => [ticket] }));

    render(<ReviewQueue />);

    expect(await screen.findByText(/can I get a discount/)).toBeInTheDocument();
    expect(screen.getByText("no documented policy matched this request; needs human triage")).toBeInTheDocument();
    expect(screen.getByText("Escalated for review")).toBeInTheDocument();
  });

  it("resolves a ticket and removes it from the list", async () => {
    const ticket = makeTicket();
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/resolve")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ ...ticket, status: "resolved", resolution_notes: "Handled manually." }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => [ticket] });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ReviewQueue />);
    await screen.findByText(/can I get a discount/);

    fireEvent.change(screen.getByLabelText(`Resolution notes for ${ticket.id}`), {
      target: { value: "Handled manually." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Mark resolved" }));

    expect(await screen.findByText("Nothing waiting on review right now.")).toBeInTheDocument();

    const [, init] = fetchMock.mock.calls.find(([url]) => url.includes("/resolve"))!;
    expect(JSON.parse(init.body)).toEqual({ notes: "Handled manually." });
  });

  it("shows an error state when the queue fails to load", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network error")));

    render(<ReviewQueue />);

    expect(await screen.findByText(/Couldn't reach the support API/)).toBeInTheDocument();
  });
});
