import { NavLink, Outlet } from "react-router";

/**
 * Application shell: header, primary nav, content region, advisory footer
 * (DESIGN.md §3.4, §7). One `h1` belongs to the page, never the shell.
 */
export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <header className="flex h-14 items-center justify-between border-b border-hairline bg-sheet px-6">
        <span className="font-display text-h3 font-semibold text-ink">Vetharbor</span>
        <nav aria-label="Primary">
          <NavLink
            to="/"
            className={({ isActive }) =>
              [
                "text-small underline-offset-4",
                isActive ? "font-medium text-brand underline" : "text-ink-secondary",
              ].join(" ")
            }
          >
            Documents
          </NavLink>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-page grow px-6 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-hairline px-6 py-4 text-meta text-ink-muted">
        Advisory screening on synthetic data. Every score is evidence-linked; humans decide.
      </footer>
    </div>
  );
}
