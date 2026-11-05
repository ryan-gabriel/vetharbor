/**
 * TanStack Query hooks for documents. Keys are tenant-scoped (AGENTS.md §9).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { makeTenantQueryKey } from '@/app/queryKeys';
import {
  getDocument,
  listDocuments,
  uploadDocument,
  type DocumentDetail,
  type DocumentListResponse,
  type DocumentSummary,
} from './api';

const ORG_ID = 'org-harbor'; // TODO: resolve from auth context in M3

export function useDocuments(page = 1, pageSize = 20) {
  return useQuery<DocumentListResponse>({
    queryKey: makeTenantQueryKey(ORG_ID, 'documents', 'list', page, pageSize),
    queryFn: () => listDocuments(page, pageSize),
  });
}

export function useDocument(id: string) {
  return useQuery<DocumentDetail>({
    queryKey: makeTenantQueryKey(ORG_ID, 'documents', 'detail', id),
    queryFn: () => getDocument(id),
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation<DocumentSummary, Error, { file: File; kind?: string }>({
    mutationFn: ({ file, kind }) => uploadDocument(file, kind),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: makeTenantQueryKey(ORG_ID, 'documents'),
      });
    },
  });
}