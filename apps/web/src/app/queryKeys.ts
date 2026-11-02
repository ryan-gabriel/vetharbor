/**
 * Query keys are tenant-scoped so switching orgs can never show the previous
 * org's cache (AGENTS.md §9).
 */

export type TenantQueryKey = readonly [
  scope: "tenant",
  orgId: string,
  ...segments: (string | number)[],
];

export function makeTenantQueryKey(
  orgId: string,
  ...segments: (string | number)[]
): TenantQueryKey {
  if (!orgId) {
    throw new Error("orgId is required for tenant-scoped queries");
  }
  return ["tenant", orgId, ...segments];
}
