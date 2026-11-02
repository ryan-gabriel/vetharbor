# apps/web — React + Vite + TypeScript SPA [T1]

Vite + React + TypeScript shell for the Vetharbor document desk. Tailwind v4
tokens come from `src/styles/tokens.css`, mapped from `docs/DESIGN.md` §3;
shadcn/ui primitives live in `src/components/ui`, composites in
`src/components`. Feature folders follow `docs/ARCHITECTURE.md` §11.
Conventions: `AGENTS.md` §9. Deployed to Vercel (Hobby) at M1.

## Run (local)

```bash
npm ci
npm run dev          # Vite, http://localhost:5173
npm test             # Vitest + Testing Library + axe
npm run typecheck    # tsc -b
npm run lint         # ESLint (type-aware)
npm run format       # Prettier check
```

Set `VITE_API_URL` (see `.env.example`) to point the SPA at the API. The
offline default is `http://localhost:8000`.

## Status (M0 task 2)

- [x] app shell, primary nav, advisory footer, one `h1` per view
- [x] typed API client with the error envelope from `ARCHITECTURE.md` §11
- [x] tenant-scoped TanStack Query keys (`AGENTS.md` §9)
- [x] `WakingUp` and `ErrorNotice` states with honest copy (`DESIGN.md` §4–5)
- [x] design tokens mapped from `DESIGN.md` §3, including the text scale
- [x] a11y smoke test for landmarks, headings and axe violations
- [ ] document list/detail data wiring: M1
- [ ] upload dropzone and processing states: M1
- [ ] ScoreGauge / EvidenceRail / CitationList: M1–M4
