import type { EntityOut } from '@/features/documents/api';

interface EvidenceRailProps {
  entities: EntityOut[];
}

const LABEL_COLORS: Record<string, string> = {
  SKILL: 'text-brand',
  ROLE: 'text-ink',
  ORG: 'text-ink-secondary',
  EDU: 'text-ink-secondary',
  DATE: 'text-ink-muted',
  YEARS: 'text-ink-muted',
  CONTACT: 'text-caution',
};

export function EvidenceRail({ entities }: EvidenceRailProps) {
  if (entities.length === 0) {
    return (
      <aside aria-label="Evidence rail" className="rounded-md border border-hairline bg-sheet p-6">
        <h2 className="font-display text-h2 text-ink">Entities</h2>
        <p className="mt-2 text-small text-ink-muted">
          No entities extracted yet.
        </p>
      </aside>
    );
  }

  // Group by label.
  const grouped = new Map<string, EntityOut[]>();
  for (const e of entities) {
    const list = grouped.get(e.label) ?? [];
    list.push(e);
    grouped.set(e.label, list);
  }

  return (
    <aside aria-label="Evidence rail" className="rounded-md border border-hairline bg-sheet p-6">
      <h2 className="font-display text-h2 text-ink">Entities</h2>
      <p className="mt-1 text-small text-ink-muted">
        {entities.length} entities extracted. Click to highlight in text.
      </p>

      <div className="mt-4 space-y-4">
        {Array.from(grouped.entries()).map(([label, items]) => (
          <div key={label}>
            <h3 className="font-mono text-meta font-medium uppercase tracking-wide text-ink-muted">
              {label} ({String(items.length)})
            </h3>
            <ul className="mt-2 space-y-1">
              {items.map((e, i) => (
                <li
                  key={`${label}-${String(i)}`}
                  className="flex items-start gap-2 text-small"
                >
                  <span className={`font-medium ${LABEL_COLORS[label] ?? 'text-ink'}`}>
                    {e.text}
                  </span>
                  {e.normalised && e.normalised !== e.text.toLowerCase() && (
                    <span className="font-mono text-meta text-ink-muted">
                      → {e.normalised}
                    </span>
                  )}
                  {e.is_pii && (
                    <span className="rounded-sm bg-caution-soft px-1 text-meta text-caution">
                      PII
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </aside>
  );
}