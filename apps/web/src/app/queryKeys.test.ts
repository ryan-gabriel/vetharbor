import { describe, expect, it } from "vitest";
import { makeTenantQueryKey } from "@/app/queryKeys";

describe("makeTenantQueryKey", () => {
  it("scopes keys by tenant so org switches cannot show stale caches", () => {
    const harbor = makeTenantQueryKey("org-harbor", "documents", "list");
    const northwind = makeTenantQueryKey("org-northwind", "documents", "list");
    expect(JSON.stringify(harbor)).not.toBe(JSON.stringify(northwind));
    expect(harbor[0]).toBe("tenant");
    expect(harbor[1]).toBe("org-harbor");
  });

  it("refuses an empty org id rather than leaking an unscoped cache", () => {
    expect(() => makeTenantQueryKey("")).toThrow(/orgId is required/);
  });
});
