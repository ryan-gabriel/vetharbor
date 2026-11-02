import type { ApiErrorCode } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * Error copy per DESIGN.md §5: what happened, what the user can do, and the
 * correlation id. Never marketing copy, never red about a person.
 */
const COPY: Record<ApiErrorCode, { title: string; action: string }> = {
  waking_up: {
    title: "Waking up",
    action: "The free-tier service is cold-starting; it should answer in about a minute.",
  },
  unauthenticated: { title: "Signed out", action: "Sign in again to continue." },
  forbidden: {
    title: "Not allowed",
    action: "Your role or tenant does not permit this action.",
  },
  not_found: {
    title: "Not found",
    action: "Nothing exists for this id inside your tenant.",
  },
  rate_limited: { title: "Slow down", action: "Too many requests; try again shortly." },
  read_only: {
    title: "Read-only demo",
    action: "This demo tenant is seeded. Upload is demonstrated by `make dev` and the recording.",
  },
  server: { title: "System error", action: "Something broke on our side, not yours." },
};

export interface ErrorNoticeProps {
  code: ApiErrorCode;
  message?: string;
  correlationId?: string | null;
  className?: string;
}

export function ErrorNotice({ code, message, correlationId, className }: ErrorNoticeProps) {
  const copy = COPY[code];
  return (
    <div
      role="alert"
      className={cn(
        "rounded-md border border-hairline bg-sunken p-4 text-ink-secondary",
        className,
      )}
    >
      <h3 className="font-display text-h3 font-semibold text-ink">{copy.title}</h3>
      <p className="mt-1 text-body">{message ?? copy.action}</p>
      {correlationId ? (
        <p className="mt-2 font-mono text-meta text-ink-muted">ref: {correlationId}</p>
      ) : null}
    </div>
  );
}
