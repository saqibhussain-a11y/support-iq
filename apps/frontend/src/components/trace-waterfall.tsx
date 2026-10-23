"use client";

import { Activity, ChevronDown, ChevronRight, ExternalLink, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";
import { fetchTrace, getJaegerUrl, TracingUnavailableError, type Trace, type TraceSpan } from "@/lib/api";

const MAX_POLL_ATTEMPTS = 10;

type LoadState = "loading" | "ready" | "missing" | "unavailable" | "error";

function spanColor(name: string): string {
  if (name.startsWith("groq.")) return "bg-primary";
  if (name.startsWith("retrieval.") || name.startsWith("agent.")) return "bg-emerald-500";
  if (name.startsWith("workflow.")) return "bg-sky-500";
  return "bg-muted-foreground/40";
}

function spanDepths(spans: TraceSpan[]): Map<string, number> {
  const byId = new Map(spans.map((span) => [span.span_id, span]));
  const depths = new Map<string, number>();
  for (const span of spans) {
    let depth = 0;
    let parentId = span.parent_span_id;
    while (parentId && byId.has(parentId)) {
      depth += 1;
      parentId = byId.get(parentId)!.parent_span_id;
    }
    depths.set(span.span_id, depth);
  }
  return depths;
}

function describeAttributes(span: TraceSpan): string {
  return Object.entries(span.attributes)
    .filter(([key]) => !key.startsWith("otel.") && key !== "internal.span.format")
    .map(([key, value]) => `${key}: ${value}`)
    .join("\n");
}

export function TraceWaterfall({ traceId, pollIntervalMs = 1000 }: { traceId: string; pollIntervalMs?: number }) {
  const [open, setOpen] = useState(false);
  const [trace, setTrace] = useState<Trace | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll(attempt: number) {
      try {
        const result = await fetchTrace(traceId);
        if (cancelled) return;
        if (result) {
          setTrace(result);
          setLoadState("ready");
        }
        if (result?.complete) return;
        if (attempt + 1 >= MAX_POLL_ATTEMPTS) {
          if (!result) setLoadState("missing");
          return;
        }
        timer = setTimeout(() => poll(attempt + 1), pollIntervalMs);
      } catch (error) {
        if (!cancelled) setLoadState(error instanceof TracingUnavailableError ? "unavailable" : "error");
      }
    }

    poll(0);
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [open, traceId, pollIntervalMs]);

  return (
    <div className="flex flex-col gap-3 border-t border-border pt-3">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-fit items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        {open ? <ChevronDown className="size-3.5" /> : <ChevronRight className="size-3.5" />}
        <Activity className="size-3.5" />
        OpenTelemetry trace
      </button>

      {open && (
        <div className="flex flex-col gap-2">
          {loadState === "loading" && (
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="size-3.5 animate-spin" />
              Fetching spans from Jaeger…
            </p>
          )}
          {loadState === "missing" && (
            <p className="text-xs text-muted-foreground">This trace isn&apos;t in Jaeger (it may have expired).</p>
          )}
          {loadState === "unavailable" && (
            <p className="text-xs text-muted-foreground">
              Jaeger isn&apos;t reachable. Start it with <code className="font-mono">docker compose up -d jaeger</code>.
            </p>
          )}
          {loadState === "error" && <p className="text-xs text-red-600 dark:text-red-400">Couldn&apos;t load this trace.</p>}
          {loadState === "ready" && trace && <SpanRows trace={trace} />}
          <a
            href={`${getJaegerUrl()}/trace/${traceId}`}
            target="_blank"
            rel="noreferrer"
            className="flex w-fit items-center gap-1 font-mono text-[0.7rem] text-muted-foreground transition-colors hover:text-primary"
          >
            {traceId}
            <ExternalLink className="size-3" />
          </a>
        </div>
      )}
    </div>
  );
}

function SpanRows({ trace }: { trace: Trace }) {
  const depths = spanDepths(trace.spans);
  const total = Math.max(trace.duration_ms, 1);

  return (
    <div className="flex flex-col gap-1">
      <p className="text-xs text-muted-foreground">
        {trace.spans.length} spans · {Math.round(trace.duration_ms).toLocaleString()} ms
        {!trace.complete && " · still arriving…"}
      </p>
      <ul className="flex flex-col gap-1">
        {trace.spans.map((span) => (
          <li
            key={span.span_id}
            data-span-name={span.name}
            title={describeAttributes(span) || undefined}
            className="grid grid-cols-[minmax(0,14rem)_1fr_3.5rem] items-center gap-2 text-[0.7rem]"
          >
            <span
              className="truncate font-mono text-foreground"
              style={{ paddingLeft: `${(depths.get(span.span_id) ?? 0) * 0.75}rem` }}
            >
              {span.name}
            </span>
            <span className="relative h-2 rounded-full bg-muted">
              <span
                className={cn("absolute inset-y-0 rounded-full", spanColor(span.name))}
                style={{
                  left: `${(span.start_offset_ms / total) * 100}%`,
                  width: `${Math.max((span.duration_ms / total) * 100, 0.75)}%`,
                }}
              />
            </span>
            <span className="text-right tabular-nums text-muted-foreground">{Math.round(span.duration_ms)} ms</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
