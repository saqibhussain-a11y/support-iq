import { SystemStatus } from "@/components/system-status";
import { TicketForm } from "@/components/ticket-form";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center gap-10 bg-zinc-50 px-6 py-16 dark:bg-black">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">SupportIQ</h1>
        <p className="max-w-md text-muted-foreground">
          AI Customer Support Intelligence Platform — classification, RAG-grounded responses,
          hallucination detection, and escalation, end to end.
        </p>
      </div>
      <TicketForm />
      <SystemStatus />
    </div>
  );
}
