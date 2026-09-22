"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { fetchTicketQueue, resolveTicket, type TicketResult, type TicketStatus } from "@/lib/api";
import {
  CategoryBadge,
  ESCALATION_META,
  PriorityBadge,
  StatusBadge,
  TokenUsageSummary,
} from "@/components/ticket-badges";

type LoadState = "loading" | "ready" | "error";
type QueueTab = Extract<TicketStatus, "pending_review" | "resolved">;

const TABS: { key: QueueTab; label: string }[] = [
  { key: "pending_review", label: "Pending" },
  { key: "resolved", label: "Resolved" },
];

export function ReviewQueue() {
  const [tab, setTab] = useState<QueueTab>("pending_review");
  const [tickets, setTickets] = useState<TicketResult[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  useEffect(() => {
    let cancelled = false;
    setLoadState("loading");
    fetchTicketQueue(tab)
      .then((result) => {
        if (cancelled) return;
        setTickets(result);
        setLoadState("ready");
      })
      .catch(() => {
        if (!cancelled) setLoadState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [tab]);

  function handleResolved(ticketId: string) {
    setTickets((current) => current.filter((ticket) => ticket.id !== ticketId));
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        {TABS.map((option) => (
          <button
            key={option.key}
            type="button"
            onClick={() => setTab(option.key)}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              tab === option.key
                ? "bg-foreground text-background"
                : "bg-muted text-muted-foreground hover:text-foreground",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      {loadState === "loading" && <p className="text-sm text-muted-foreground">Loading tickets…</p>}

      {loadState === "error" && (
        <p className="text-sm font-medium text-red-600 dark:text-red-400">
          Couldn&apos;t reach the support API. Is the backend running?
        </p>
      )}

      {loadState === "ready" && tickets.length === 0 && (
        <p className="text-sm text-muted-foreground">
          {tab === "pending_review" ? "Nothing waiting on review right now." : "No resolved tickets yet."}
        </p>
      )}

      {loadState === "ready" && tickets.length > 0 && (
        <div className="flex flex-col gap-4">
          {tickets.map((ticket) => (
            <QueueItem key={ticket.id} ticket={ticket} onResolved={() => handleResolved(ticket.id)} />
          ))}
        </div>
      )}
    </div>
  );
}

function QueueItem({ ticket, onResolved }: { ticket: TicketResult; onResolved: () => void }) {
  const escalation = ESCALATION_META[ticket.escalation];
  const [notes, setNotes] = useState("");
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState(false);
  const isPending = ticket.status === "pending_review";

  async function handleResolve() {
    setResolving(true);
    setError(false);
    try {
      await resolveTicket(ticket.id, notes.trim() || null);
      onResolved();
    } catch {
      setError(true);
      setResolving(false);
    }
  }

  return (
    <Card className="overflow-hidden py-0">
      <div
        className={cn("flex items-center gap-2 border-b border-border px-4 py-3", escalation.bannerClassName)}
      >
        <escalation.icon className="size-4" />
        <span className="text-sm font-semibold">{escalation.label}</span>
        <span className="ml-auto text-xs text-muted-foreground">
          {new Date(ticket.created_at).toLocaleString()}
        </span>
      </div>

      <CardContent className="flex flex-col gap-4 py-4">
        <div className="flex flex-wrap gap-2">
          <StatusBadge status={ticket.status} />
          <CategoryBadge category={ticket.classification.category} />
          <PriorityBadge priority={ticket.classification.priority} />
          <Badge variant="outline" className="rounded-md capitalize">
            {ticket.classification.sentiment}
          </Badge>
        </div>

        <p className="text-sm text-muted-foreground">
          <span className="font-medium text-foreground">Customer said: </span>
          {ticket.message}
        </p>

        <p className="border-t border-border pt-3 text-sm leading-relaxed whitespace-pre-wrap">
          {ticket.response.answer}
        </p>

        {ticket.escalation_reasons.length > 0 && (
          <div className={cn("flex gap-2 rounded-md p-3 text-xs ring-1 ring-inset", escalation.calloutClassName)}>
            <escalation.icon className="size-4 shrink-0 translate-y-0.5" />
            <div className="flex flex-col gap-1">
              <p className="font-semibold">Why this was escalated</p>
              <ul className="ml-4 list-disc">
                {ticket.escalation_reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {isPending ? (
          <div className="flex flex-col gap-2 border-t border-border pt-3">
            <Textarea
              aria-label={`Resolution notes for ${ticket.id}`}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Optional notes about how this was resolved…"
              rows={2}
            />
            <div className="flex items-center justify-between">
              {error ? (
                <p className="text-xs font-medium text-red-600 dark:text-red-400">
                  Couldn&apos;t resolve this ticket.
                </p>
              ) : (
                <span />
              )}
              <Button type="button" onClick={handleResolve} disabled={resolving}>
                {resolving ? "Resolving…" : "Mark resolved"}
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-1 border-t border-border pt-3 text-xs text-muted-foreground">
            <span>
              Resolved{ticket.resolved_at ? ` ${new Date(ticket.resolved_at).toLocaleString()}` : ""}
            </span>
            {ticket.resolution_notes && <p className="text-foreground">{ticket.resolution_notes}</p>}
          </div>
        )}

        {ticket.token_usage && <TokenUsageSummary usage={ticket.token_usage} />}
      </CardContent>
    </Card>
  );
}
