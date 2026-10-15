import { Sparkles } from "lucide-react";

import { TicketForm } from "@/components/ticket-form";

export default function Home() {
  return (
    <main className="flex-1 px-8 py-10 md:px-10">
      <div className="mx-auto w-full max-w-5xl">
        <div className="mb-6">
          <span className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
            <Sparkles className="size-3" />
            Agentic RAG pipeline
          </span>
          <h1 className="text-xl font-semibold tracking-tight">Ask a support question</h1>
          <p className="text-sm text-muted-foreground">
            Classified, answered from documented policy, checked for accuracy, and escalated to a
            human when it should be.
          </p>
        </div>
        <TicketForm />
      </div>
    </main>
  );
}
