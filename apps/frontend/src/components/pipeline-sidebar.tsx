import { CheckCircle2, CircleDashed, Loader2, Wrench } from "lucide-react";

import { cn } from "@/lib/utils";
import type { PipelineStage, ToolCallEvent } from "@/lib/api";

export type StepStatus = "pending" | "active" | "done" | "skipped";

export interface ToolCallEntry {
  tool: string;
  detail: string;
  status: "active" | "done";
  resultSummary?: string;
}

export interface PipelineStep {
  key: "classify" | "answer" | "faithfulness" | "validate";
  label: string;
  agent: string;
  status: StepStatus;
  toolCalls?: ToolCallEntry[];
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

function describeArguments(event: ToolCallEvent): string {
  const args = event.arguments ?? {};
  return args.query ?? args.document_name ?? Object.values(args)[0] ?? "";
}

export function applyToolCallEvent(steps: PipelineStep[], event: ToolCallEvent): PipelineStep[] {
  return steps.map((step) => {
    if (step.key !== "answer") return step;
    const toolCalls = step.toolCalls ?? [];

    if (event.phase === "start") {
      const entry: ToolCallEntry = { tool: event.tool, detail: describeArguments(event), status: "active" };
      return { ...step, toolCalls: [...toolCalls, entry] };
    }

    const activeIndex = toolCalls.map((call) => call.status).lastIndexOf("active");
    if (activeIndex === -1) return step;
    const updated = [...toolCalls];
    updated[activeIndex] = {
      ...updated[activeIndex],
      status: "done",
      resultSummary:
        event.found && event.sources && event.sources.length > 0
          ? `Found in ${event.sources.join(", ")}`
          : "No results found",
    };
    return { ...step, toolCalls: updated };
  });
}

const TOOL_LABELS: Record<string, string> = {
  search_knowledge_base: "Searching knowledge base",
  get_full_document: "Fetching document",
};

export function PipelineSidebar({ steps }: { steps: PipelineStep[] }) {
  return (
    <aside className="w-full shrink-0 md:w-72">
      <div className="sticky top-6 rounded-lg border border-border bg-background p-4">
        <h2 className="text-sm font-semibold">Pipeline</h2>
        <p className="mb-4 text-xs text-muted-foreground">Live agent progress for this request.</p>
        <ol className="flex flex-col gap-3">
          {steps.map((step) => (
            <li key={step.key} data-status={step.status} className="flex flex-col gap-2">
              <div className="flex items-start gap-2.5">
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
              </div>

              {step.toolCalls && step.toolCalls.length > 0 && (
                <ul className="ml-[1.375rem] flex flex-col gap-1.5 border-l border-border pl-3">
                  {step.toolCalls.map((call, index) => (
                    <li key={index} data-tool-status={call.status} className="flex items-start gap-2">
                      <ToolCallIcon status={call.status} />
                      <div className="flex flex-col">
                        <span className="text-xs font-medium">
                          {TOOL_LABELS[call.tool] ?? call.tool}
                          {call.detail && (
                            <span className="font-normal text-muted-foreground"> &ldquo;{call.detail}&rdquo;</span>
                          )}
                        </span>
                        {call.resultSummary && (
                          <span className="text-[0.7rem] text-muted-foreground">{call.resultSummary}</span>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
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

function ToolCallIcon({ status }: { status: "active" | "done" }) {
  if (status === "done") {
    return <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />;
  }
  return <Wrench className="mt-0.5 size-3.5 shrink-0 animate-pulse text-blue-600 dark:text-blue-400" />;
}
