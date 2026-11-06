import { useParams, Link } from "react-router";
import { useDocument } from "./hooks";
import { ErrorNotice } from "@/components/ErrorNotice";
import { EvidenceRail } from "@/components/EvidenceRail";
import { WakingUp } from "@/components/WakingUp";
import { ApiError } from "@/lib/api";

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, error } = useDocument(id ?? "");

  if (isLoading) {
    return (
      <section role="status" aria-label="Loading document" className="space-y-4">
        <h1 className="font-display text-h1 text-ink">Loading…</h1>
      </section>
    );
  }

  if (isError) {
    const code = error instanceof ApiError ? error.code : "server";
    if (code === "waking_up") return <WakingUp />;
    return (
      <div className="space-y-4">
        <h1 className="font-display text-h1 text-ink">Document not found</h1>
        <ErrorNotice
          code={code}
          correlationId={error instanceof ApiError ? error.correlationId : null}
        />
        <Link to="/" className="text-brand underline">
          Back to documents
        </Link>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <>
      <nav aria-label="Breadcrumb" className="mb-4">
        <Link to="/" className="text-small text-brand underline">
          Documents
        </Link>
        <span className="text-small text-ink-muted"> / {data.filename}</span>
      </nav>

      <h1 className="font-display text-h1 text-ink">{data.filename}</h1>
      <p className="mt-1 text-small text-ink-muted">
        {data.kind} · {data.status} · {data.char_count} chars · {data.word_count} words
      </p>

      {data.warning_flags.length > 0 && (
        <div className="mt-4 rounded-md border border-caution bg-caution-soft p-3 text-small text-caution">
          Warnings: {data.warning_flags.join(", ")}
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_360px]">
        <section
          aria-label="Document text"
          className="rounded-md border border-hairline bg-sheet p-6"
        >
          <h2 className="font-display text-h2 text-ink">Extracted text</h2>
          <pre className="mt-4 whitespace-pre-wrap font-sans text-body text-ink">
            {data.extracted_text}
          </pre>
        </section>

        <EvidenceRail entities={data.entities} />
      </div>
    </>
  );
}
