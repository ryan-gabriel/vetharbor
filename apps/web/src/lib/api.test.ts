import { describe, expect, it, vi } from "vitest";
import { ApiError, apiJson, isApiErrorCode, parseErrorEnvelope } from "@/lib/api";

describe("parseErrorEnvelope", () => {
  it("accepts a valid backend envelope", () => {
    const parsed = parseErrorEnvelope({
      error: { code: "forbidden", message: "no membership here", correlation_id: "abc" },
    });
    expect(parsed).toEqual({
      code: "forbidden",
      message: "no membership here",
      correlationId: "abc",
    });
  });

  it("degrades malformed bodies to server with null correlation", () => {
    expect(parseErrorEnvelope(null)).toEqual({
      code: "server",
      message: "The request could not be completed.",
      correlationId: null,
    });
    expect(parseErrorEnvelope({ error: { code: "weird" } }).code).toBe("server");
  });

  it("validates only the documented error union", () => {
    expect(isApiErrorCode("waking_up")).toBe(true);
    expect(isApiErrorCode("read_only")).toBe(true);
    expect(isApiErrorCode("candidate_rejected")).toBe(false);
    expect(isApiErrorCode(42)).toBe(false);
  });
});

describe("apiJson", () => {
  it("passes through successful JSON payloads and stamps a correlation id", async () => {
    const payload = { status: "ok" };
    let seenInput: URL | RequestInfo | undefined;
    let seenHeaders: Headers | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: URL | RequestInfo, init?: RequestInit) => {
        seenInput = input;
        seenHeaders = new Headers(init?.headers);
        return Promise.resolve(new Response(JSON.stringify(payload), { status: 200 }));
      }),
    );

    await expect(apiJson<{ status: string }>("/healthz")).resolves.toEqual(payload);
    expect(seenInput).toBe("/healthz");
    expect(seenHeaders?.has("X-Request-ID")).toBe(true);
    expect(seenHeaders?.get("Accept")).toBe("application/json");
  });

  it("prefixes requests with the configured API base url", async () => {
    let seenInput: URL | RequestInfo | undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: URL | RequestInfo) => {
        seenInput = input;
        return Promise.resolve(new Response("{}", { status: 200 }));
      }),
    );
    vi.stubEnv("VITE_API_URL", "https://api.example.test");

    await apiJson("/documents");
    expect(seenInput).toBe("https://api.example.test/documents");
  });

  it("throws ApiError with code and correlation id from the envelope", async () => {
    const envelope = {
      error: { code: "read_only", message: "demo is read-only", correlation_id: "corr-9" },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify(envelope), { status: 403 }))),
    );

    let error: unknown;
    try {
      await apiJson("/documents", { method: "POST" });
      expect.unreachable("apiJson should have thrown");
    } catch (caught) {
      error = caught;
    }
    expect(error).toBeInstanceOf(ApiError);
    if (error instanceof ApiError) {
      expect(error.code).toBe("read_only");
      expect(error.correlationId).toBe("corr-9");
      expect(error.status).toBe(403);
    }
  });

  it("handles non-JSON failure bodies", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Response("<html>", { status: 502 })),
    );

    let error: unknown;
    try {
      await apiJson("/x");
      expect.unreachable("apiJson should have thrown");
    } catch (caught) {
      error = caught;
    }
    expect(error).toBeInstanceOf(ApiError);
    if (error instanceof ApiError) {
      expect(error.code).toBe("server");
    }
  });
});
