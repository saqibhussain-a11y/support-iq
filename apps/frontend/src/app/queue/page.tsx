import { ReviewQueue } from "@/components/review-queue";

export default function QueuePage() {
  return (
    <main className="flex flex-1 justify-center px-6 py-12">
      <div className="w-full max-w-2xl">
        <div className="mb-6">
          <h1 className="text-lg font-semibold tracking-tight">Review queue</h1>
          <p className="text-sm text-muted-foreground">
            Tickets the AI couldn&apos;t confidently resolve on its own.
          </p>
        </div>
        <ReviewQueue />
      </div>
    </main>
  );
}
