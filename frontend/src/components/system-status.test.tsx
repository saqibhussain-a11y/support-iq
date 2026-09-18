import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SystemStatus } from "./system-status";

describe("SystemStatus", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows healthy badges when the API and database are reachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation((url: string) => {
        if (url.endsWith("/health/ready")) {
          return Promise.resolve({
            ok: true,
            json: async () => ({ status: "ok", database: "ok" }),
          });
        }
        return Promise.resolve({ ok: true, json: async () => ({ status: "ok" }) });
      }),
    );

    render(<SystemStatus />);

    expect(await screen.findAllByText("Healthy")).toHaveLength(2);
  });

  it("shows unreachable badges when requests fail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network error")));

    render(<SystemStatus />);

    expect(await screen.findAllByText("Unreachable")).toHaveLength(2);
  });
});
