import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { TicketResult } from "@/lib/api";
import { TicketForm } from "./ticket-form";

function stubFetchResolving(result: TicketResult) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => result }),
  );
}

function baseResult(overrides: Partial<TicketResult> = {}): TicketResult {
  return {
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
    ...overrides,
  };
}

function submit(message: string) {
  fireEvent.change(screen.getByLabelText("Describe your issue"), {
    target: { value: message },
  });
  fireEvent.click(screen.getByRole("button", { name: "Submit" }));
}

describe("TicketForm", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("disables submit until a message is entered", () => {
    render(<TicketForm />);

    expect(screen.getByRole("button", { name: "Submit" })).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Describe your issue"), {
      target: { value: "I was charged twice" },
    });

    expect(screen.getByRole("button", { name: "Submit" })).toBeEnabled();
  });

  it("filling an example message populates the textarea", () => {
    render(<TicketForm />);

    fireEvent.click(screen.getByRole("button", { name: "How do I reset my password?" }));

    expect(screen.getByLabelText("Describe your issue")).toHaveValue(
      "How do I reset my password?",
    );
  });

  it("submits the message and renders the classification, answer, and sources", async () => {
    stubFetchResolving(baseResult());
    render(<TicketForm />);

    submit("I was charged twice");

    expect(await screen.findByText("You're eligible for a refund.")).toBeInTheDocument();
    expect(screen.getByText("billing")).toBeInTheDocument();
    expect(screen.getByText("high priority")).toBeInTheDocument();
    expect(screen.getByText("frustrated")).toBeInTheDocument();
    expect(screen.getByText(/refund_policy\.md/)).toBeInTheDocument();
    expect(screen.getByText("Resolved automatically")).toBeInTheDocument();
  });

  it("shows unsupported claims when the answer is not faithful", async () => {
    stubFetchResolving(
      baseResult({
        faithfulness: { is_faithful: false, unsupported_claims: ["a fabricated 60-day window"] },
      }),
    );
    render(<TicketForm />);

    submit("I was charged twice");

    expect(await screen.findByText(/a fabricated 60-day window/)).toBeInTheDocument();
  });

  it("shows escalation status and reasons when the ticket was escalated", async () => {
    stubFetchResolving(
      baseResult({
        escalation: "immediate",
        escalation_reasons: ["message mentions a stolen payment method"],
      }),
    );
    render(<TicketForm />);

    submit("someone stole my card");

    expect(await screen.findByText("Escalated immediately")).toBeInTheDocument();
    expect(screen.getByText("message mentions a stolen payment method")).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network error")));
    render(<TicketForm />);

    submit("I was charged twice");

    expect(
      await screen.findByText(/Couldn't reach the support API/),
    ).toBeInTheDocument();
  });
});
