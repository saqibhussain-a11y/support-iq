import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchHealth, fetchReadiness } from "./api";

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("fetchHealth returns parsed JSON on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok" }),
      }),
    );

    await expect(fetchHealth()).resolves.toEqual({ status: "ok" });
  });

  it("fetchReadiness throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({}) }),
    );

    await expect(fetchReadiness()).rejects.toThrow("Readiness check failed: 503");
  });
});
