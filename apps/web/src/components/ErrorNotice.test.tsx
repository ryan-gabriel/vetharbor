import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ErrorNotice } from "@/components/ErrorNotice";

describe("ErrorNotice", () => {
  it("announces itself as an alert (DESIGN.md §5)", () => {
    render(<ErrorNotice code="forbidden" />);
    expect(screen.getByRole("alert")).toBeDefined();
  });

  it("shows the mapped copy for read_only with the make dev pointer", () => {
    render(<ErrorNotice code="read_only" />);
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("Read-only demo");
    expect(alert.textContent).toContain("make dev");
  });

  it("renders the correlation id in mono when present", () => {
    render(<ErrorNotice code="server" correlationId="corr-42" />);
    expect(screen.getByRole("alert").textContent).toContain("ref: corr-42");
  });

  it("never uses adverse-decision vocabulary (AGENTS.md §3.3)", () => {
    render(<ErrorNotice code="forbidden" />);
    expect(screen.getByRole("alert").textContent.toLowerCase()).not.toMatch(
      /rejected|disqualified/,
    );
  });
});
