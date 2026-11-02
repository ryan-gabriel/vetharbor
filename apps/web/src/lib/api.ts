/**
 * Client for the Vetharbor API. All HTTP goes through here - components never
 * call fetch (AGENTS.md §9). The error union mirrors app/core/errors.py
 * (docs/ARCHITECTURE.md §11).
 */

export type ApiErrorCode =
  | "unauthenticated"
  | "waking_up"
  | "forbidden"
  | "not_found"
  | "rate_limited"
  | "read_only"
  | "server";

export interface ErrorEnvelope {
  error: {
    code: ApiErrorCode;
    message: string;
    correlation_id: string | null;
  };
}

export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly status: number;
  readonly correlationId: string | null;

  constructor(code: ApiErrorCode, message: string, status: number, correlationId: string | null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.correlationId = correlationId;
  }
}

export function isApiErrorCode(value: unknown): value is ApiErrorCode {
  const codes: ApiErrorCode[] = [
    "unauthenticated",
    "waking_up",
    "forbidden",
    "not_found",
    "rate_limited",
    "read_only",
    "server",
  ];
  return typeof value === "string" && (codes as string[]).includes(value);
}

/** Parse the stable error envelope; tolerate malformed bodies as `server`. */
export function parseErrorEnvelope(body: unknown): {
  code: ApiErrorCode;
  message: string;
  correlationId: string | null;
} {
  const envelope = body as Partial<ErrorEnvelope> | null;
  const error = envelope?.error;
  if (error && isApiErrorCode(error.code)) {
    return {
      code: error.code,
      message: typeof error.message === "string" ? error.message : "",
      correlationId: typeof error.correlation_id === "string" ? error.correlation_id : null,
    };
  }
  return { code: "server", message: "The request could not be completed.", correlationId: null };
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  token?: string | null;
  tenantId?: string | null;
}

function newCorrelationId(): string {
  return crypto.randomUUID().replace(/-/g, "");
}

/** Core request helper. Cold service -> the SPA must surface `waking_up`, not
 * a blank page (SPEC.md F1, DESIGN.md §4 WakingUp). */
export async function apiFetch(path: string, options: RequestOptions = {}): Promise<Response> {
  const base = import.meta.env.VITE_API_URL ?? "";
  const headers = new Headers(options.headers);
  headers.set("X-Request-ID", newCorrelationId());
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);

  const response = await fetch(`${base}${path}`, { ...options, headers });
  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      /* non-JSON failure body: handled by parseErrorEnvelope */
    }
    const parsed = parseErrorEnvelope(body);
    throw new ApiError(parsed.code, parsed.message, response.status, parsed.correlationId);
  }
  return response;
}

export async function apiJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  const response = await apiFetch(path, { ...options, headers });
  return (await response.json()) as T;
}
