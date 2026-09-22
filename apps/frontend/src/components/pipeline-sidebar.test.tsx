import { describe, expect, it } from "vitest";

import { applyPipelineStage, INITIAL_PIPELINE_STEPS } from "./pipeline-sidebar";

function statusOf(steps: ReturnType<typeof applyPipelineStage>, key: string) {
  return steps.find((step) => step.key === key)?.status;
}

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
