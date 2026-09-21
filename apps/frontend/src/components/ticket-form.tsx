"use client";

import { useState, type FormEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { submitTicket, type EscalationLevel, type TicketResult } from "@/lib/api";

const EXAMPLE_MESSAGES = [
  "I was charged twice for my subscription this month and I want a refund.",
  "I think someone stole my card",
  "How do I reset my password?",
];

type SubmitState = "idle" | "loading" | "error";

export function TicketForm() {
  const [message, setMessage] = useState("");
  const [state, setState] = useState<SubmitState>("idle");
  const [result, setResult] = useState<TicketResult | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!message.trim() || state === "loading") return;

    setState("loading");
    try {
      const ticketResult = await submitTicket(message.trim());
      setResult(ticketResult);
      setState("idle");
    } catch {
      setState("error");
    }
  }

  return (
    <div className="flex w-full max-w-2xl flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Ask SupportIQ</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <label htmlFor="ticket-message" className="text-sm font-medium">
              Describe your issue
            </label>
            <Textarea
              id="ticket-message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="e.g. I was charged twice for my subscription..."
              rows={3}
            />
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_MESSAGES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setMessage(example)}
                  className="cursor-pointer rounded-full border border-border px-3 py-1 text-xs text-muted-foreground hover:bg-muted"
                >
                  {example.length > 42 ? `${example.slice(0, 42)}…` : example}
                </button>
              ))}
            </div>
            <Button type="submit" disabled={state === "loading" || !message.trim()}>
              {state === "loading" ? "Thinking..." : "Submit ticket"}
            </Button>
          </form>
          {state === "error" && (
            <p className="text-sm text-destructive">
              Something went wrong reaching the support API. Is the backend running?
            </p>
          )}
        </CardContent>
      </Card>

      {result && <TicketResultCard result={result} />}
    </div>
  );
}

function TicketResultCard({ result }: { result: TicketResult }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Result</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{result.classification.category}</Badge>
          <Badge variant="secondary">{result.classification.priority} priority</Badge>
          <Badge variant="secondary">{result.classification.sentiment}</Badge>
          <EscalationBadge level={result.escalation} />
        </div>

        <p className="text-sm whitespace-pre-wrap">{result.response.answer}</p>

        {result.response.sources.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span>Sources:</span>
            {result.response.sources.map((source) => (
              <Badge key={source} variant="outline">
                {source}
              </Badge>
            ))}
          </div>
        )}

        {result.faithfulness && !result.faithfulness.is_faithful && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-xs text-destructive">
            <p className="font-medium">Unsupported claims detected</p>
            <ul className="ml-4 list-disc">
              {result.faithfulness.unsupported_claims.map((claim) => (
                <li key={claim}>{claim}</li>
              ))}
            </ul>
          </div>
        )}

        {result.escalation_reasons.length > 0 && (
          <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-3 text-xs">
            <p className="font-medium">Escalation reasons</p>
            <ul className="ml-4 list-disc">
              {result.escalation_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EscalationBadge({ level }: { level: EscalationLevel }) {
  const variant = {
    none: { label: "Auto-resolved", className: "bg-green-600 text-white" },
    review: { label: "Escalated: review", className: "bg-yellow-500 text-white" },
    immediate: { label: "Escalated: immediate", className: "bg-red-600 text-white" },
  }[level];

  return <Badge className={variant.className}>{variant.label}</Badge>;
}
