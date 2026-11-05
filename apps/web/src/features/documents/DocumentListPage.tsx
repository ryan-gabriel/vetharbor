import { useDocuments } from './hooks';
import { ErrorNotice } from '@/components/ErrorNotice';
import { WakingUp } from '@/components/WakingUp';
import { ApiError } from '@/lib/api';
import { Link } from 'react-router';

export function DocumentListPage() {
  const { data, isLoading, isError, error } = useDocuments();

  if (isLoading) {
    return (
      <section role="status" aria-label="Loading documents" className="space-y-4">
        <h1 className="font-display text-h1 text-ink">Documents</h1>
        <p className="text-body text-ink-secondary">Loading…</p>
      </section>
    );
  }

  if (isError) {
    const code =
      error instanceof ApiError ? error.code : 'server';
    if (code === 'waking_up') {
      return <WakingUp />;
    }
    return (
      <div className="space-y-4">
        <h1 className="font-display text-h1 text-ink">Documents</h1>
        <ErrorNotice code={code} correlationId={error instanceof ApiError ? error.correlationId : null} />
      </div>
    );
  }

  const items = data?.items ?? [];

  return (
    <>
      <h1 className="font-display text-h1 text-ink">Documents</h1>
      <p className="mt-2 max-w-measure text-body text-ink-secondary">
        Two seeded synthetic tenants prove tenant isolation. Upload is demonstrated locally with{' '}
        <code className="font-mono text-small">make dev</code> and in the recorded walkthrough.
      </p>

      {items.length === 0 ? (
        <div className="mt-8 rounded-md border border-hairline bg-sheet p-8 text-center">
          <p className="text-body text-ink-secondary">No documents in this view yet.</p>
          <p className="mt-1 text-small text-ink-muted">
            Seeded corpora arrive with the M1 demo deployment.
          </p>
        </div>
      ) : (
        <ul className="mt-8 divide-y divide-hairline rounded-md border border-hairline bg-sheet">
          {items.map((doc) => (
            <li key={doc.id} className="px-4 py-3">
              <Link
                to={`/documents/${doc.id}`}
                className="flex items-center justify-between gap-4 hover:text-brand"
              >
                <span className="font-display text-h3 text-ink">{doc.filename}</span>
                <span className="font-mono text-meta text-ink-muted">{doc.status}</span>
              </Link>
              <p className="mt-1 text-small text-ink-secondary">
                {doc.char_count} chars · {doc.word_count} words
                {doc.warning_flags.length > 0 && (
                  <span className="ml-2 text-caution">
                    ⚠ {doc.warning_flags.join(', ')}
                  </span>
                )}
              </p>
            </li>
          ))}
        </ul>
      )}

      {data && data.total > data.page_size && (
        <p className="mt-4 text-small text-ink-muted">
          Showing {items.length} of {data.total} documents.
        </p>
      )}
    </>
  );
}