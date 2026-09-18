import { SystemStatus } from "@/components/system-status";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 bg-zinc-50 px-6 py-24 dark:bg-black">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-semibold tracking-tight">SupportIQ</h1>
        <p className="max-w-md text-muted-foreground">
          AI Customer Support Intelligence Platform — Module 1: Foundation
        </p>
      </div>
      <SystemStatus />
    </div>
  );
}
