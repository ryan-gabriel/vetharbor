/**
 * Document API functions. All HTTP goes through lib/api (AGENTS.md §9).
 */

import { apiJson } from '@/lib/api';

export interface DocumentSummary {
  id: string;
  org_id: string;
  kind: string;
  filename: string;
  status: string;
  sha256: string;
  size_bytes: number;
  page_count: number | null;
  char_count: number;
  word_count: number;
  warning_flags: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface DocumentDetail extends DocumentSummary {
  extracted_text: string;
  entities: EntityOut[];
}

export interface DocumentListResponse {
  items: DocumentDetail[];
  total: number;
  page: number;
  page_size: number;
}

export interface EntityOut {
  id: string | null;
  label: string;
  text: string;
  normalised: string | null;
  taxonomy: string | null;
  confidence: number | null;
  char_start: number;
  char_end: number;
  rule_id: string | null;
  source: string;
  is_pii: boolean;
}

export async function listDocuments(
  page = 1,
  pageSize = 20,
): Promise<DocumentListResponse> {
  return apiJson<DocumentListResponse>(
    `/documents?page=${String(page)}&page_size=${String(pageSize)}`,
  );
}

export async function getDocument(id: string): Promise<DocumentDetail> {
  return apiJson<DocumentDetail>(`/documents/${id}`);
}

import { apiFetch } from '@/lib/api';

export async function uploadDocument(
  file: File,
  kind?: string,
): Promise<DocumentSummary> {
  const form = new FormData();
  form.append('file', file);
  if (kind) form.append('kind', kind);
  const response = await apiFetch('/documents', {
    method: 'POST',
    body: form,
  } as unknown as Parameters<typeof apiFetch>[1]);
  return (await response.json()) as DocumentSummary;
}