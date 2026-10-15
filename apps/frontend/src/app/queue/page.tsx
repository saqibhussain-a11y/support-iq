import { ShieldAlert } from "lucide-react";

import { ReviewQueue } from "@/components/review-queue";

export default function QueuePage() {
  return (
    <main className="flex-1 px-8 py-10 md:px-10">
      <div className="mx-auto w-full max-w-3xl">
        <div className="mb-6">
          <span className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
            <ShieldAlert className="size-3" />
            Human-in-the-loop
          </span>
          <h1 className="text-xl font-semibold tracking-tight">Review queue</h1>
          <p className="text-sm text-muted-foreground">
            Tickets the AI couldn&apos;t confidently resolve on its own.
          </p>
        </div>
        <ReviewQueue />
      </div>
    </main>
  );
}
