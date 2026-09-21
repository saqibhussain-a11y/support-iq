"use client";

import { AlertTriangle, CheckCircle2, Loader2, MessageSquareWarning, Send, ShieldAlert } from "lucide-react";
import { useState, type ComponentType, type FormEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  submitTicket,
  type EscalationLevel,
  type TicketCategory,
  type TicketPriority,
  type TicketResult,
} from "@/lib/api";

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
    <div className="flex flex-col gap-6">
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

const CATEGORY_STYLES: Record<TicketCategory, string> = {
  billing: "bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-500/10 dark:text-blue-400 dark:ring-blue-400/20",
  shipping:
    "bg-purple-50 text-purple-700 ring-purple-600/20 dark:bg-purple-500/10 dark:text-purple-400 dark:ring-purple-400/20",
  product:
    "bg-indigo-50 text-indigo-700 ring-indigo-600/20 dark:bg-indigo-500/10 dark:text-indigo-400 dark:ring-indigo-400/20",
  account: "bg-cyan-50 text-cyan-700 ring-cyan-600/20 dark:bg-cyan-500/10 dark:text-cyan-400 dark:ring-cyan-400/20",
  other: "bg-gray-100 text-gray-700 ring-gray-500/20 dark:bg-gray-500/10 dark:text-gray-400 dark:ring-gray-400/20",
};

function CategoryBadge({ category }: { category: TicketCategory }) {
  return (
    <Badge className={cn("rounded-md capitalize ring-1 ring-inset", CATEGORY_STYLES[category])}>
      {category}
    </Badge>
  );
}

const PRIORITY_STYLES: Record<TicketPriority, string> = {
  low: "bg-slate-100 text-slate-700 ring-slate-500/20 dark:bg-slate-500/10 dark:text-slate-400 dark:ring-slate-400/20",
  medium:
    "bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-400/20",
  high: "bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-400/20",
};

function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return (
    <Badge className={cn("rounded-md capitalize ring-1 ring-inset", PRIORITY_STYLES[priority])}>
      {priority} priority
    </Badge>
  );
}

const ESCALATION_META: Record<
  EscalationLevel,
  {
    label: string;
    icon: ComponentType<{ className?: string }>;
    bannerClassName: string;
    calloutClassName: string;
  }
> = {
  none: {
    label: "Resolved automatically",
    icon: CheckCircle2,
    bannerClassName: "bg-emerald-50 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400",
    calloutClassName:
      "bg-emerald-50 text-emerald-800 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-400 dark:ring-emerald-400/20",
  },
  review: {
    label: "Escalated for review",
    icon: AlertTriangle,
    bannerClassName: "bg-amber-50 text-amber-800 dark:bg-amber-500/10 dark:text-amber-400",
    calloutClassName:
      "bg-amber-50 text-amber-800 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-400/20",
  },
  immediate: {
    label: "Escalated immediately",
    icon: ShieldAlert,
    bannerClassName: "bg-red-50 text-red-800 dark:bg-red-500/10 dark:text-red-400",
    calloutClassName:
      "bg-red-50 text-red-800 ring-red-600/20 dark:bg-red-500/10 dark:text-red-400 dark:ring-red-400/20",
  },
};
