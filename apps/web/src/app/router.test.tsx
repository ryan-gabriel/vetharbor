import { render, screen } from "@testing-library/react";
import axe from "axe-core";
import { describe, expect, it } from "vitest";
import { RouterProvider, createMemoryRouter } from "react-router";
import { AppProviders } from "@/app/providers";
import { routes } from "@/app/routes";

/**
 * a11y smoke for the shell (TESTING.md §8). jsdom cannot compute colour, so
 * the contrast rule is delegated to the DESIGN token audit; landmarks,
 * headings, names and ARIA run here for real.
 */
function renderRoute(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  return render(
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>,
  );
}

describe("app shell", () => {
  it("has no serious or critical axe violations", async () => {
    const { container } = renderRoute("/");
    const results = await axe.run(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    const blocking = results.violations.filter(
      (v) => v.impact === "serious" || v.impact === "critical",
    );
    expect(blocking.map((v) => v.id)).toEqual([]);
  });

  it("exposes semantic landmarks: header, primary nav, main", () => {
    renderRoute("/");
    expect(screen.getByRole("banner")).toBeDefined();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeDefined();
    expect(screen.getByRole("main")).toBeDefined();
  });

  it("renders exactly one h1 per view", () => {
    renderRoute("/");
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });
});
