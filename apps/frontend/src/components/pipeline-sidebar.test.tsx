import { describe, expect, it } from "vitest";

import type { ToolCallEvent } from "@/lib/api";
import {
  applyPipelineStage,
  applyToolCallEvent,
  INITIAL_PIPELINE_STEPS,
  startPipelineSteps,
} from "./pipeline-sidebar";

function statusOf(steps: ReturnType<typeof applyPipelineStage>, key: string) {
  return steps.find((step) => step.key === key)?.status;
}

function toolCallsOf(steps: ReturnType<typeof applyPipelineStage>) {
  return steps.find((step) => step.key === "answer")?.toolCalls ?? [];
}

describe("INITIAL_PIPELINE_STEPS", () => {
  it("starts every step pending, with no step active before a submission", () => {
    expect(INITIAL_PIPELINE_STEPS.every((step) => step.status === "pending")).toBe(true);
  });
});

describe("startPipelineSteps", () => {
  it("marks only classify as active when a submission begins", () => {
    const steps = startPipelineSteps();

    expect(statusOf(steps, "classify")).toBe("active");
    expect(statusOf(steps, "answer")).toBe("pending");
    expect(statusOf(steps, "faithfulness")).toBe("pending");
    expect(statusOf(steps, "validate")).toBe("pending");
  });
});

describe("applyPipelineStage", () => {
  it("walks the respond branch: classify -> respond -> check_faithfulness -> validate", () => {
    let steps = INITIAL_PIPELINE_STEPS.map((step) => ({ ...step }));

    steps = applyPipelineStage(steps, "classify");
    expect(statusOf(steps, "classify")).toBe("done");
    expect(statusOf(steps, "answer")).toBe("active");

    steps = applyPipelineStage(steps, "respond");
    expect(statusOf(steps, "answer")).toBe("done");
    expect(steps.find((step) => step.key === "answer")?.agent).toBe("Response Agent");
    expect(statusOf(steps, "faithfulness")).toBe("active");

    steps = applyPipelineStage(steps, "check_faithfulness");
    expect(statusOf(steps, "faithfulness")).toBe("done");
    expect(statusOf(steps, "validate")).toBe("active");

    steps = applyPipelineStage(steps, "validate");
    expect(statusOf(steps, "validate")).toBe("done");
  });

  it("walks the clarify branch and skips faithfulness checking", () => {
    let steps = INITIAL_PIPELINE_STEPS.map((step) => ({ ...step }));

    steps = applyPipelineStage(steps, "classify");
    steps = applyPipelineStage(steps, "clarify");

    expect(statusOf(steps, "answer")).toBe("done");
    expect(steps.find((step) => step.key === "answer")?.agent).toBe("Clarifying Agent");
    expect(statusOf(steps, "faithfulness")).toBe("skipped");
    expect(statusOf(steps, "validate")).toBe("active");

    steps = applyPipelineStage(steps, "validate");
    expect(statusOf(steps, "validate")).toBe("done");
  });
});

describe("applyToolCallEvent", () => {
  it("adds an active tool call entry on start", () => {
    let steps = INITIAL_PIPELINE_STEPS.map((step) => ({ ...step }));
    const startEvent: ToolCallEvent = {
      type: "tool",
      phase: "start",
      tool: "search_knowledge_base",
      arguments: { query: "refund policy" },
    };

    steps = applyToolCallEvent(steps, startEvent);

    expect(toolCallsOf(steps)).toEqual([
      { tool: "search_knowledge_base", detail: "refund policy", status: "active" },
    ]);
  });

  it("marks the matching entry done and attaches a found summary on end", () => {
    let steps = INITIAL_PIPELINE_STEPS.map((step) => ({ ...step }));
    steps = applyToolCallEvent(steps, {
      type: "tool",
      phase: "start",
      tool: "search_knowledge_base",
      arguments: { query: "refund policy" },
    });

    steps = applyToolCallEvent(steps, {
      type: "tool",
      phase: "end",
      tool: "search_knowledge_base",
      found: true,
      sources: ["refund_policy.md"],
    });

    expect(toolCallsOf(steps)).toEqual([
      {
        tool: "search_knowledge_base",
        detail: "refund policy",
        status: "done",
        resultSummary: "Found in refund_policy.md",
      },
    ]);
  });

  it("marks the entry done with a not-found summary when nothing matched", () => {
    let steps = INITIAL_PIPELINE_STEPS.map((step) => ({ ...step }));
    steps = applyToolCallEvent(steps, {
      type: "tool",
      phase: "start",
      tool: "get_full_document",
      arguments: { document_name: "missing.md" },
    });

    steps = applyToolCallEvent(steps, {
      type: "tool",
      phase: "end",
      tool: "get_full_document",
      found: false,
      sources: [],
    });

    expect(toolCallsOf(steps)[0]).toMatchObject({ status: "done", resultSummary: "No results found" });
  });

  it("tracks multiple sequential tool calls independently", () => {
    let steps = INITIAL_PIPELINE_STEPS.map((step) => ({ ...step }));
    steps = applyToolCallEvent(steps, {
      type: "tool",
      phase: "start",
      tool: "search_knowledge_base",
      arguments: { query: "a" },
    });
    steps = applyToolCallEvent(steps, {
      type: "tool",
      phase: "end",
      tool: "search_knowledge_base",
      found: true,
      sources: ["a.md"],
    });
    steps = applyToolCallEvent(steps, {
      type: "tool",
      phase: "start",
      tool: "get_full_document",
      arguments: { document_name: "b.md" },
    });

    const toolCalls = toolCallsOf(steps);
    expect(toolCalls).toHaveLength(2);
    expect(toolCalls[0]).toMatchObject({ tool: "search_knowledge_base", status: "done" });
    expect(toolCalls[1]).toMatchObject({ tool: "get_full_document", status: "active" });
  });
});
