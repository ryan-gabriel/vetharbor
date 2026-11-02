/**
 * Seeded read-only demo state (SPEC.md F1). The list query wiring lands in
 * M1; this page establishes the structure and the honest empty state.
 */
export function DocumentListPage() {
  return (
    <>
      <h1 className="font-display text-h1 text-ink">Documents</h1>
      <p className="mt-2 max-w-measure text-body text-ink-secondary">
        Two seeded synthetic tenants prove tenant isolation. Upload is demonstrated locally with{" "}
        <code className="font-mono text-small">make dev</code> and in the recorded walkthrough.
      </p>
      <div className="mt-8 rounded-md border border-hairline bg-sheet p-8 text-center">
        <p className="text-body text-ink-secondary">No documents in this view yet.</p>
        <p className="mt-1 text-small text-ink-muted">
          Seeded corpora arrive with the M1 demo deployment.
        </p>
      </div>
    </>
  );
}
