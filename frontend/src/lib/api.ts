export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export interface HealthResponse {
  status: string;
}

export interface ReadinessResponse {
  status: string;
  database: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${getApiUrl()}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchReadiness(): Promise<ReadinessResponse> {
  const res = await fetch(`${getApiUrl()}/health/ready`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Readiness check failed: ${res.status}`);
  return res.json();
}
