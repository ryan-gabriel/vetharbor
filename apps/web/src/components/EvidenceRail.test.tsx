import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { EvidenceRail } from '@/components/EvidenceRail';
import type { EntityOut } from '@/features/documents/api';

const sampleEntities: EntityOut[] = [
  {
    id: '1',
    label: 'SKILL',
    text: 'Python',
    normalised: 'python',
    taxonomy: 'local',
    confidence: 0.9,
    char_start: 0,
    char_end: 6,
    rule_id: 'gazetteer:1.0.0',
    source: 'gazetteer',
    is_pii: false,
  },
  {
    id: '2',
    label: 'CONTACT',
    text: 'test@example.com',
    normalised: 'email',
    taxonomy: null,
    confidence: 1.0,
    char_start: 20,
    char_end: 36,
    rule_id: 'email_regex',
    source: 'regex',
    is_pii: true,
  },
];

describe('EvidenceRail', () => {
  it('renders empty state when no entities', () => {
    render(<EvidenceRail entities={[]} />);
    expect(screen.getByText(/no entities extracted yet/i)).toBeDefined();
  });

  it('renders entity groups with labels', () => {
    render(<EvidenceRail entities={sampleEntities} />);
    expect(screen.getByText('SKILL (1)')).toBeDefined();
    expect(screen.getByText('CONTACT (1)')).toBeDefined();
  });

  it('shows PII badge for contact entities', () => {
    render(<EvidenceRail entities={sampleEntities} />);
    expect(screen.getByText('PII')).toBeDefined();
  });

  it('has accessible aside landmark', () => {
    render(<EvidenceRail entities={sampleEntities} />);
    expect(screen.getByRole('complementary', { name: /evidence rail/i })).toBeDefined();
  });

  it('shows entity count', () => {
    render(<EvidenceRail entities={sampleEntities} />);
    expect(screen.getByText(/2 entities extracted/i)).toBeDefined();
  });
});