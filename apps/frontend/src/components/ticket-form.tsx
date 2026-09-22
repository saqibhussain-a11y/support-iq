"use client";

import { Loader2, MessageSquareWarning, Send } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { streamTicket, type TicketResult } from "@/lib/api";
import {
  applyPipelineStage,
  INITIAL_PIPELINE_STEPS,
  PipelineSidebar,
  startPipelineSteps,
  type PipelineStep,
} from "@/components/pipeline-sidebar";
import { CategoryBadge, ESCALATION_META, PriorityBadge } from "@/components/ticket-badges";

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
  const [steps, setSteps] = useState<PipelineStep[]>(INITIAL_PIPELINE_STEPS);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!message.trim() || state === "loading") return;

    setState("loading");
    setResult(null);
    setSteps(startPipelineSteps());
    try {
      for await (const streamEvent of streamTicket(message.trim())) {
        if (streamEvent.type === "stage") {
          setSteps((current) => applyPipelineStage(current, streamEvent.stage));
        } else {
          setResult(streamEvent.result);
        }
      }
      setState("idle");
    } catch {
      setState("error");
    }
  }

  return (
    <div className="flex flex-col gap-6 md:flex-row md:items-start">
      <div className="flex min-w-0 flex-1 flex-col gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-sm font-semibold">New support request</h2>
            <p className="text-sm text-muted-foreground">
              Describe the issue the way a customer would.
            </p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <Textarea
                id="ticket-message"
                aria-label="Describe your issue"
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="e.g. I was charged twice for my subscription..."
                rows={4}
              />

              <div className="flex flex-wrap gap-2">
                {EXAMPLE_MESSAGES.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => setMessage(example)}
                    className="cursor-pointer rounded-md border border-border bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:border-foreground/20 hover:bg-muted hover:text-foreground"
                  >
                    {example.length > 40 ? `${example.slice(0, 40)}…` : example}
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-between border-t border-border pt-4">
                {state === "error" ? (
                  <p className="text-sm font-medium text-red-600 dark:text-red-400">
                    Couldn&apos;t reach the support API. Is the backend running?
                  </p>
                ) : (
                  <span />
                )}
                <Button type="submit" disabled={state === "loading" || !message.trim()}>
                  {state === "loading" ? (
                    <>
                      <Loader2 className="animate-spin" />
                      Analyzing…
                    </>
                  ) : (
                    <>
                      <Send />
                      Submit
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {result && <TicketResultCard result={result} />}
      </div>

      <PipelineSidebar steps={steps} />
    </div>
  );
}

function TicketResultCard({ result }: { result: TicketResult }) {
  const escalation = ESCALATION_META[result.escalation];

  return (
    <Card className="overflow-hidden py-0">
      <div className={cn("flex items-center gap-2 border-b border-border px-4 py-3", escalation.bannerClassName)}>
        <escalation.icon className="size-4" />
        <span className="text-sm font-semibold">{escalation.label}</span>
      </div>

      <CardContent className="flex flex-col gap-4 py-4">
        <div className="flex flex-wrap gap-2">
          <CategoryBadge category={result.classification.category} />
          <PriorityBadge priority={result.classification.priority} />
          <Badge variant="outline" className="rounded-md capitalize">
            {result.classification.sentiment}
          </Badge>
        </div>

        <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.response.answer}</p>

        {result.response.sources.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 border-t border-border pt-3">
            <span className="text-xs font-medium text-muted-foreground">Sources</span>
            {result.response.sources.map((source) => (
              <Badge key={source} variant="secondary" className="rounded-md font-mono text-[0.7rem] font-normal">
                {source}
              </Badge>
            ))}
          </div>
        )}

        {result.faithfulness && !result.faithfulness.is_faithful && (
          <div className="flex gap-2 rounded-md bg-amber-50 p-3 text-amber-800 ring-1 ring-inset ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-400/20">
            <MessageSquareWarning className="size-4 shrink-0 translate-y-0.5" />
            <div className="flex flex-col gap-1 text-xs">
              <p className="font-semibold">Unsupported claims detected</p>
              <ul className="ml-4 list-disc">
                {result.faithfulness.unsupported_claims.map((claim) => (
                  <li key={claim}>{claim}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {result.escalation_reasons.length > 0 && (
          <div className={cn("flex gap-2 rounded-md p-3 text-xs ring-1 ring-inset", escalation.calloutClassName)}>
            <escalation.icon className="size-4 shrink-0 translate-y-0.5" />
            <div className="flex flex-col gap-1">
              <p className="font-semibold">Why this was escalated</p>
              <ul className="ml-4 list-disc">
                {result.escalation_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
