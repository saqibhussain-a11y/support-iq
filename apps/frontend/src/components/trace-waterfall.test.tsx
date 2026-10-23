import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Trace } from "@/lib/api";
import { TraceWaterfall } from "./trace-waterfall";

const TRACE_ID = "b36ee8ce2ecbb2c45cafe579e39a2db3";

function makeTrace(overrides: Partial<Trace> = {}): Trace {
  return {
    trace_id: TRACE_ID,
    duration_ms: 4355,
    complete: true,
    spans: [
      {
        span_id: "root",
        parent_span_id: null,
        name: "POST /api/tickets/stream",
        start_offset_ms: 0,
        duration_ms: 4355,
        attributes: {},
      },
      {
        span_id: "classify",
        parent_span_id: "root",
        name: "workflow.classify",
        start_offset_ms: 90,
        duration_ms: 1469,
        attributes: { "classification.category": "account" },
      },
      {
        span_id: "groq",
        parent_span_id: "classify",
        name: "groq.chat.completions",
        start_offset_ms: 90,
        duration_ms: 1469,
        attributes: { "llm.usage.total_tokens": 287 },
      },
    ],
    ...overrides,
  };
}

function jsonResponse(status: number, body: unknown) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

describe("TraceWaterfall", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("does not fetch the trace until it is expanded", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<TraceWaterfall traceId={TRACE_ID} />);

    expect(screen.getByRole("button", { name: /OpenTelemetry trace/ })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders the real spans with durations, nested by parent, once expanded", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, makeTrace()));
    vi.stubGlobal("fetch", fetchMock);

    render(<TraceWaterfall traceId={TRACE_ID} />);
    fireEvent.click(screen.getByRole("button", { name: /OpenTelemetry trace/ }));

    expect(await screen.findByText("workflow.classify")).toBeInTheDocument();
    expect(screen.getByText("groq.chat.completions")).toBeInTheDocument();
    expect(screen.getByText("3 spans · 4,355 ms")).toBeInTheDocument();
    expect(screen.getAllByText("1469 ms")).toHaveLength(2);
    expect(fetchMock.mock.calls[0][0]).toBe(`http://localhost:8000/api/traces/${TRACE_ID}`);

    const groqRow = screen.getByText("groq.chat.completions").closest("li")!;
    expect(groqRow).toHaveAttribute("title", "llm.usage.total_tokens: 287");
    const groqLabel = screen.getByText("groq.chat.completions");
    expect(groqLabel).toHaveStyle({ paddingLeft: "1.5rem" });
  });

  it("links to the full trace in Jaeger", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, makeTrace())));

    render(<TraceWaterfall traceId={TRACE_ID} />);
    fireEvent.click(screen.getByRole("button", { name: /OpenTelemetry trace/ }));

    const link = await screen.findByRole("link", { name: new RegExp(TRACE_ID) });
    expect(link).toHaveAttribute("href", `http://localhost:16686/trace/${TRACE_ID}`);
  });

  it("keeps polling until the root span has arrived", async () => {
    const partial = makeTrace({ complete: false, spans: makeTrace().spans.slice(1) });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(404, {}))
      .mockResolvedValueOnce(jsonResponse(200, partial))
      .mockResolvedValue(jsonResponse(200, makeTrace()));
    vi.stubGlobal("fetch", fetchMock);

    render(<TraceWaterfall traceId={TRACE_ID} pollIntervalMs={1} />);
    fireEvent.click(screen.getByRole("button", { name: /OpenTelemetry trace/ }));

    expect(await screen.findByText("POST /api/tickets/stream")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("explains how to start Jaeger when the tracing backend is unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(503, {})));

    render(<TraceWaterfall traceId={TRACE_ID} />);
    fireEvent.click(screen.getByRole("button", { name: /OpenTelemetry trace/ }));

    expect(await screen.findByText(/Jaeger isn't reachable/)).toBeInTheDocument();
  });
});
