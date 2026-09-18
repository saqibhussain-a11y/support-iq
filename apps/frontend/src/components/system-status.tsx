"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchHealth, fetchReadiness } from "@/lib/api";

type CheckState = "loading" | "ok" | "degraded" | "error";

export function SystemStatus() {
  const [apiState, setApiState] = useState<CheckState>("loading");
  const [dbState, setDbState] = useState<CheckState>("loading");
  const [lastChecked, setLastChecked] = useState<string | null>(null);

  const runChecks = useCallback(async () => {
    setApiState("loading");
    setDbState("loading");

    try {
      await fetchHealth();
      setApiState("ok");
    } catch {
      setApiState("error");
    }

    try {
      const readiness = await fetchReadiness();
      setDbState(readiness.database === "ok" ? "ok" : "degraded");
    } catch {
      setDbState("error");
    }

    setLastChecked(new Date().toLocaleTimeString());
  }, []);

  useEffect(() => {
    runChecks();
  }, [runChecks]);

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>System Status</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <StatusRow label="FastAPI Backend" state={apiState} />
        <StatusRow label="PostgreSQL + pgvector" state={dbState} />
        <div className="flex items-center justify-between pt-2 text-sm text-muted-foreground">
          <span>{lastChecked ? `Last checked ${lastChecked}` : "Checking..."}</span>
          <button
            onClick={runChecks}
            className="cursor-pointer font-medium text-foreground underline underline-offset-4"
          >
            Refresh
          </button>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusRow({ label, state }: { label: string; state: CheckState }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm font-medium">{label}</span>
      <StatusBadge state={state} />
    </div>
  );
}

function StatusBadge({ state }: { state: CheckState }) {
  const variant = {
    loading: { label: "Checking...", className: "bg-muted text-muted-foreground" },
    ok: { label: "Healthy", className: "bg-green-600 text-white" },
    degraded: { label: "Degraded", className: "bg-yellow-500 text-white" },
    error: { label: "Unreachable", className: "bg-red-600 text-white" },
  }[state];

  return <Badge className={variant.className}>{variant.label}</Badge>;
}
