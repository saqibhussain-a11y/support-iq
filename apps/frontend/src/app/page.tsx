import { TicketForm } from "@/components/ticket-form";

export default function Home() {
  return (
    <main className="flex flex-1 justify-center px-6 py-12">
      <div className="w-full max-w-2xl">
        <div className="mb-6">
          <h1 className="text-lg font-semibold tracking-tight">Ask a support question</h1>
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
