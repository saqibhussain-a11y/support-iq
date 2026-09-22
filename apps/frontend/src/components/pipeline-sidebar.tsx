import { CheckCircle2, CircleDashed, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { PipelineStage } from "@/lib/api";

export type StepStatus = "pending" | "active" | "done" | "skipped";

export interface PipelineStep {
  key: "classify" | "answer" | "faithfulness" | "validate";
  label: string;
  agent: string;
  status: StepStatus;
}

export const INITIAL_PIPELINE_STEPS: PipelineStep[] = [
  { key: "classify", label: "Classify ticket", agent: "Classifier Agent", status: "pending" },
  { key: "answer", label: "Respond", agent: "Response Agent", status: "pending" },
  { key: "faithfulness", label: "Check faithfulness", agent: "Faithfulness Checker", status: "pending" },
  { key: "validate", label: "Validate & escalate", agent: "Escalation Rules", status: "pending" },
];

export function startPipelineSteps(): PipelineStep[] {
  return INITIAL_PIPELINE_STEPS.map((step) =>
    step.key === "classify" ? { ...step, status: "active" } : { ...step },
  );
}

export function applyPipelineStage(steps: PipelineStep[], stage: PipelineStage): PipelineStep[] {
  return steps.map((step) => {
    if (step.key === "classify" && stage === "classify") {
      return { ...step, status: "done" };
    }
    if (step.key === "answer" && stage === "classify") {
      return { ...step, status: "active" };
    }
    if (step.key === "answer" && stage === "respond") {
      return { ...step, label: "Respond", agent: "Response Agent", status: "done" };
    }
    if (step.key === "answer" && stage === "clarify") {
      return { ...step, label: "Clarify", agent: "Clarifying Agent", status: "done" };
    }
    if (step.key === "faithfulness" && stage === "respond") {
      return { ...step, status: "active" };
    }
    if (step.key === "faithfulness" && stage === "clarify") {
      return { ...step, status: "skipped" };
    }
    if (step.key === "faithfulness" && stage === "check_faithfulness") {
      return { ...step, status: "done" };
    }
    if (step.key === "validate" && stage === "clarify") {
      return { ...step, status: "active" };
    }
    if (step.key === "validate" && stage === "check_faithfulness") {
      return { ...step, status: "active" };
    }
    if (step.key === "validate" && stage === "validate") {
      return { ...step, status: "done" };
    }
    return step;
  });
}

export function PipelineSidebar({ steps }: { steps: PipelineStep[] }) {
  return (
    <aside className="w-full shrink-0 md:w-64">
      <div className="sticky top-6 rounded-lg border border-border bg-background p-4">
        <h2 className="text-sm font-semibold">Pipeline</h2>
        <p className="mb-4 text-xs text-muted-foreground">Live agent progress for this request.</p>
        <ol className="flex flex-col gap-3">
          {steps.map((step) => (
            <li key={step.key} data-status={step.status} className="flex items-start gap-2.5">
              <StepIcon status={step.status} />
              <div className={cn("flex flex-col", step.status === "skipped" && "opacity-50")}>
                <span
                  className={cn(
                    "text-sm font-medium",
                    step.status === "pending" && "text-muted-foreground",
                  )}
                >
                  {step.label}
                </span>
                <span className="text-xs text-muted-foreground">
                  {step.status === "skipped" ? "Skipped" : step.agent}
                </span>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </aside>
  );
}

function StepIcon({ status }: { status: StepStatus }) {
  if (status === "done") {
    return <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />;
  }
  if (status === "active") {
    return <Loader2 className="mt-0.5 size-4 shrink-0 animate-spin text-blue-600 dark:text-blue-400" />;
  }
  return <CircleDashed className="mt-0.5 size-4 shrink-0 text-muted-foreground" />;
}
