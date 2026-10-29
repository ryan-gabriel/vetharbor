# DESIGN — Vetharbor

| | |
| --- | --- |
| **Purpose** | Enforces visual consistency and UI component rules. The contract a front-end change must satisfy. |
| **Primary reader** | AI agent. |
| **Status** | v1.0 — approved for build. Stack decided: React + Vite + TypeScript + Tailwind + shadcn/ui. |
| **Owner** | ryan_gabriel_s |
| **Last updated** | 29 Oct 2026 |
| **Authority** | Visual tokens and component rules live **here**. Folder boundaries live in `ARCHITECTURE.md` §11. Flows live in `SPEC.md` §6. |

Tiers: `[T1]` must ship · `[T2]` should ship · `[T3]` documented only.

---

## 1. Design idea

Vetharbor is a **harbor for untrusted documents**. The interface should feel like a careful editorial desk: paper, evidence, annotation, and a calm verdict — not a scoring machine. The document is the subject; the score is a marginal note beside it.

Three commitments drive every rule below:

1. **Evidence before number.** No score or answer appears without its source snippet visible or one click away.
2. **Advisory, never verdict.** The vocabulary is *strong / moderate / weak / insufficient evidence*, never *reject / fail / disqualified*. This is a legal and ethical position expressed as typography.
3. **Honest about its limits.** Cold starts, refusals, missing data and model uncertainty get first-class states with real copy, not spinners or error toasts.

The audience is a senior reviewer. Nothing decorative should cost them reading time.

## 2. Aesthetic: editorial security, light with one accent

Light warm-paper surfaces, near-black typography, one saturated harbour-blue accent, one amber for caution. Hairline rules instead of shadows. Low radii. Generous whitespace, asymmetric alignment on document-centric views. Serif for headings and document quotations, grotesque sans for interface, mono for ids, offsets, scores and logs.

This is deliberately not a dashboard look. No gradient meshes, no glass, no glowing cards, no three-accent hero, no illustration people.

## 3. Tokens

All tokens are CSS custom properties in `apps/web/src/styles/tokens.css`, mapped into the Tailwind theme. **No raw hex or px values in component code** — if a value is not a token, it does not go in a PR.

### 3.1 Colour

| Token | Value | Use |
| --- | --- | --- |
| `--surface-canvas` | `#F7F4EE` | Page background — warm paper |
| `--surface-sheet` | `#FFFFFF` | Document panel, tables |
| `--surface-sunken` | `#EFEAE1` | Wells, code/evidence blocks |
| `--surface-raised` | `#FFFDF9` | Overlays, dialogs |
| `--ink-primary` | `#14110E` | Body and heading text |
| `--ink-secondary` | `#4A443C` | Supporting text, labels |
| `--ink-muted` | `#7C7468` | Meta, timestamps, disabled |
| `--ink-inverse` | `#FAF7F2` | Text on accent |
| `--rule-hairline` | `#DCD5C8` | Default borders, dividers |
| `--rule-strong` | `#B8AE9C` | Table headers, focus-adjacent rules |
| `--accent` | `#1C4ED8` | Primary action, active state, links |
| `--accent-hover` | `#173FA8` | Hover/pressed |
| `--accent-soft` | `#E6EDFC` | Selected row tint, focus ring outer |
| `--caution` | `#B4690E` | Warnings, hidden-text flags, waking up |
| `--caution-soft` | `#FBF1E2` | Caution surface |
| `--danger` | `#A32F2F` | DLQ, failed processing, denied access |
| `--danger-soft` | `#FBEAEA` | Danger surface |
| `--success` | `#2E6B4F` | Ready state, green CI badge only |
| `--focus` | `#1C4ED8` | Focus ring (2px outline + 2px offset) |

Rules:

- `--danger` is **never** applied to a candidate, a document, or a score band. It marks system failures and denied operations only. A reviewer should be able to grep the component library and find no path where red means "this person is a bad fit".
- Status is never conveyed by colour alone: every badge pairs colour with a word and an icon.
- Contrast minimum 4.5:1 for body text, 3:1 for large text and UI parts, measured on the tokens above (`--ink-muted` on `--surface-canvas` is the tightest pairing and must be tested as an explicit case in CI).
- Semantic tokens only in components. `bg-accent`, not `bg-[#1C4ED8]`.

### 3.2 Typography

Self-hosted via `@fontsource` packages. **No CDN fonts** — Render and Vercel cold starts must not add a third-party round trip, and offline `make dev` must look identical to the deployment.

| Role | Family | Weights | Notes |
| --- | --- | --- | --- |
| Display / headings | `Fraunces` (variable, optical size) | 400, 600 | Serif. Section titles, document names, score headline number |
| Interface | `Inter` | 400, 500, 600 | Body, labels, tables, buttons |
| Mono | `IBM Plex Mono` | 400, 500 | Ids, char offsets, scores, log lines, JSON, rule ids |

Scale (fluid, `clamp()`, 1.25 ratio): `--text-display` 32→44px; `--text-h1` 26→32; `--text-h2` 21→24; `--text-h3` 17→19; `--text-body` 16px fixed; `--text-small` 14px; `--text-meta` 13px; `--text-mono` 13px / `tabular-nums`.

- Body line-height 1.6; headings 1.15–1.25.
- Measure: **max 68ch** for prose, 78ch for tables. Document text panels are the exception: they render at `--text-body` with `whitespace: pre-wrap` inside a sheet.
- One weight step per element. Never three.
- Numerals always `tabular-nums` in scores, counts and durations, so a polling number does not jitter.
- `Fraunces` optical sizing on for display, off in headings under 20px.
- Never set body copy in a serif, and never set a heading in mono.

### 3.3 Space, radius, elevation, layers

- Base unit 4px. Scale: `2, 4, 8, 12, 16, 24, 32, 48, 64, 96`.
- Component padding: compact 8/12, default 12/16, generous 24/32.
- Section rhythm: 64px desktop, 40px mobile. Page top padding 32px.
- Radii: `--radius-sm 2px`, `--radius 4px`, `--radius-lg 6px` (dialogs only). Nothing pill-shaped except badges, which use 999px by exception.
- Elevation: **hairlines first**. `--shadow-none` default; `--shadow-sheet 0 1px 2px rgb(20 17 14 / .06)` for overlays; `--shadow-dialog 0 12px 32px rgb(20 17 14 / .14)`. Cards are not raised by default — a card that needs a shadow needs a reason.
- Layers: sticky header 10, dropdown 20, dialog 30, toast 40, waking-up overlay 50.

### 3.4 Layout

- 12-column grid, 24px gutter, max content width **1240px**.
- Application shell: 56px header, 240px sidebar (collapses to a drawer under 1024px), main region.
- **Document detail is a two-pane editorial spread**: text sheet left (min 480px), evidence and score rail right (360px). This is the signature layout and it must not degrade into stacked cards on desktop.
- One primary action per screen. A screen with two equal-weight buttons is a design error, not a preference question.

## 4. Component system

Built on shadcn/ui primitives, restyled through tokens. Copy a primitive into `components/ui`, do not fork its behaviour. Project composites live in `components/`.

| Component | Rules |
| --- | --- |
| `Button` | Variants `primary` (accent, one per screen), `secondary` (hairline on sheet), `ghost`, `danger` (system-destructive only). Min height 40px, hit area 44px. Text only — no icon-only buttons without an accessible name and a tooltip. |
| `Badge` | `statusDocument` (pending, processing, ready, failed, rejected), `scoreBand` (strong, moderate, weak, insufficient), `warningFlag`, `role`. Word + icon + colour. Never a bare dot. |
| `Card` / `Panel` | Hairline border, no shadow, `--surface-sheet`. Max one nesting level: a card inside a card is a redesign, not a tweak. |
| `Table` | Tabular numerals, 44px rows, `--ink-secondary` headers with `--rule-strong` underline, sortable headers expose `aria-sort`, zebra forbidden — use hairlines. |
| `DocumentSheet` | Renders `extracted_text` with entity highlights. Highlight style: 2px underline in `--accent`, not a filled chip, so text stays readable. Clicking an entity scrolls the rail into view and vice versa. Hidden-text warnings surface as inline amber markers with a tooltip. |
| `EvidenceRail` | The score and the entities that justify it. Every item is `(entity, char_start, char_end, why)` from `scores.evidence`. Recipient of `DocumentSheet` clicks. |
| `ScoreGauge` | Headline number in `Fraunces`, 44px, `tabular-nums`. Below it: band word, then a thin horizontal bar with the calibration band as a bracket, then the three feature contributions as labelled rows with numbers. Never colour-only, never a circular dial, never a percentage without the model version beside it. Shows `model_version` and a link to its model card. |
| `CitationList` | Numbered, each item scrolls the source into view and highlights the span. Hovering a citation in the answer text highlights the list row. |
| `RedactedText` | Renders `[redacted:email]` chips in mono on `--surface-sunken`. The chip names the category so the reader knows something was removed on purpose rather than lost. |
| `AnswerPanel` | Answer text max 68ch, refusal states are normal outcomes: `refused_no_evidence` → "I could not find this in your documents." + suggested rewording; `blocked_injection` → "This document was flagged as containing instructions. It was not sent to the model." + the rule that fired. |
| `UploadDropzone` | Drag-drop plus a plain file input. States: idle, hovering, validating, too-large, wrong-type, accepted. Always lists the exact limits (5 MB, 60 pages, PDF/DOCX/TXT). Carries the anonymisation notice (`SPEC.md` §11). Disabled with server-side reason when `demo_state.is_readonly_mode` is true — never hidden, because a hidden control teaches nothing. |
| `StatusPoller` | `aria-live="polite"` region, 2 s interval with jitter, stops at a terminal state, 60 s cap then "still processing, we will notify by polling slower". No full-page spinner. |
| `WakingUp` | Full-bleed `--surface-sunken` overlay, one line of Fraunces: "This demo is asleep.", a mono countdown estimate, an auto-retry, and a link to the recording. Shown when the API returns `waking_up` or the first request exceeds 1.5 s. Never a skeleton screen, because a skeleton implies progress that is not happening. |
| `EmptyState` | One sentence plus the single next action. No illustration, no mascot. |
| `TenantSwitcher` | Header select listing `org_memberships` rows. Switching writes an `auth.tenant_switch` audit row and flashes the org name so it is unmistakable which tenant is active. |
| `Toast` (`sonner`) | Bottom-right, 4 s default, 8 s with an action. Max one at a time for the same category. Never the sole channel for a form error — inline validation is required alongside. |
| `Skeleton` | Allowed only for same-size content on a warm service. Shimmer is a 150 ms opacity pulse; static grey is acceptable and cheaper. |
| `Tabs` | 44px targets, `role="tablist"`, active tab underline in `--accent` plus weight, arrow-key navigation. |
| `Dialog` | Focus trap, `Esc` closes, return focus to the trigger, max width 560px, `--surface-raised` plus `--shadow-dialog`. |
| `CodeLine` / `LogView` | Mono on `--surface-sunken`, 13px, horizontal scroll with a visible fade, never wrapped mid-id. |

Composite rule: a screen is assembled from `DocumentSheet` + `EvidenceRail` + `ScoreGauge` or from `AnswerPanel` + `CitationList`. Those two pairs are the product's visual identity; if a screen contains neither, question whether it belongs in v1.

## 5. States and copy

Every async surface implements all applicable states explicitly; a missing state is a bug, not polish.

`loading · waking_up · empty · ready · partial · processing · failed · denied · rate_limited · read_only`

Voice: plain, declarative, second person, no marketing. Present tense, sentence case, no exclamation marks in system messages. Numbers and technical ids in mono.

| Banned | Use instead |
| --- | --- |
| "Rejected candidate" | "Below current threshold — manual review required" |
| "AI-ranked top applicants" | "Strongest evidence of match to this role" |
| "Disqualified" | (does not exist in this product) |
| "Something went wrong" | What happened, what the user can do, the correlation id |
| "Loading…" (over 1.5 s) | `WakingUp` or `StatusPoller` with real status |
| "Our AI ensures fairness" | "Fairness audit results and limitations" linking to the notebook |

The last row matters: the README and the UI make no fairness claim the fairness notebook does not support.

## 6. Data visualisation

- Chart types permitted: horizontal bar for feature contributions, small line for score distribution over model versions, scatter for calibration (predicted bin versus observed rate, with the diagonal), histogram for PSI drift. Everything else is a table.
- Colour-blind safe: the accent/amber/danger trio is distinguishable under deuteranopia and protanopia; each series also differs in marker shape and direct labelling.
- Every mark has a numeric label. A chart without numbers is decoration.
- No axis truncation. Zero included on any quantitative axis.
- Confidence intervals drawn as whiskers when present in the Quarto/`scores` data; never implied by shading.
- Library: `visx` primitives with the tokens above — not a themed charting framework, because a theme that re-skin your tokens is a second design system you did not approve.
- Every chart has a text alternative summarising the finding in one sentence.

## 7. Accessibility (hard requirement)

WCAG 2.1 AA, enforced as CI failures, not aspirations (see `TESTING.md` §8).

1. Semantic landmarks: `header`, `nav`, `main`, `aside` for the evidence rail, `footer`. Exactly one `h1` per view; no level skips.
2. Keyboard: every interactive element reachable in a sensible order; visible `:focus-visible` ring using `--focus`, 2px outline with 2px offset; dialogs trapped; tables sortable from the keyboard.
3. Hit targets ≥ 44×44 CSS px.
4. Forms: a real `<label>` per control, `aria-describedby` for errors, errors named inline and summarised at the top, no placeholder-as-label.
5. Live regions: `StatusPoller` polite, toasts polite, and no more than one live region per region of the screen.
6. Images: this product has essentially none. Document previews are text. Avatars are absent by design (photos are an excluded feature — `SPEC.md` §7 FR-602), so no decorative portrait ever appears.
7. Motion: `prefers-reduced-motion: reduce` kills all transitions and the skeleton pulse.
8. Text: 16px body minimum, zoom to 200 % without loss, no fixed-height text containers.
9. Colour: never sole carrier; contrast as in §3.1.
10. Tables: `<caption>` or an `aria-label`, `<th scope>`, and the score table announces the model version in a caption so the number is never unattributed.

## 8. Interaction and motion

- Durations: 120 ms hover, 150 ms state change, 200 ms dialog open, 250 ms drawer. Nothing longer is a design smell.
- Easing: `cubic-bezier(0.2, 0, 0, 1)` for entrances, `cubic-bezier(0.4, 0, 1, 1)` for exits.
- Allowed: underline reveal on nav hover, evidence-row tint on focus, entity-to-rail scroll, badge fade on state change, bar-grow on first paint of `ScoreGauge`.
- Forbidden: parallax, scroll-jacking, pinned sections, auto-carousels, animated counters, logo animations, hover-lift on cards, page transitions.
- Optimistic UI only for the tenant switcher and reading states. Scores and answers are never optimistic — a wrong number on a candidate is precisely the harm this product is designed to avoid.

## 9. Responsive

Breakpoints: 480 / 768 / 1024 / 1280 / 1440.

- Under 1024: sidebar becomes a drawer; the two-pane spread stacks with the sheet first and the rail below, and `EvidenceRail` gains a sticky mini-header so the score does not scroll away from its text.
- Under 768: one column, 16px page padding, tables become card lists for `documents` and stay tables for `audit_log` with horizontal scroll, `ScoreGauge` number drops to 34px.
- Under 480: header collapses to logo plus tenant chip; the upload dropzone becomes a plain button plus a limits list.
- `demo_reader` is desktop-first. Small-screen layouts are correct and readable but not the demo path; say so in the runbook rather than pretending.

## 10. Front-end conventions agents must follow

- TypeScript `strict`, `noUncheckedIndexedAccess`. No `any` without a `// rationale:` comment.
- Server state in TanStack Query, keyed by `['tenant', orgId, ...]` so a tenant switch cannot show cached rows from the previous org — this is an RLS bug that would otherwise look like a data leak.
- No `fetch` in components; everything through `lib/api` with the typed error union from `ARCHITECTURE.md` §11.
- Component files: one exported component per file, colocated `*.test.tsx`, no index barrel re-exports of everything.
- Styling: token utilities only. Arbitrary values (`bg-[#...]`, `p-[13px]`) fail review.
- Icons: `lucide-react`, 16/20px, stroke 1.5, always paired with a text label in primary actions.
- Every interactive component ships with its a11y test in the same PR; a component without a `*.test.tsx` covering its keyboard path is not done.

## 11. Do / don't quick reference

**Do:** paper-white document sheets, hairline rules, one accent used sparingly, serif for headings and quotations, tabular numerals, explicit empty and refusal states, evidence beside every number, the model version beside every score.

**Don't:** gradient headlines, glassmorphism, dark glowing dashboards, emoji in UI, icon-only buttons without labels, cards inside cards, colour-only status, circular score dials, auto-playing anything, fake avatars, the word "rejected" about a person, marketing copy in error messages, raw hex in components, three equal-weight buttons on a screen.

## 12. `[T3]` appendix

- **Dark mode.** Deferred, and deliberately so: the editorial-paper concept loses its meaning in near-black, and a second palette doubles the contrast test matrix. If built: a separate token file, a `data-theme` attribute, no per-component colour logic, and both palettes pass AA in CI. Amber becomes the accent, hairlines lighten, sheet surfaces invert to `#14110E`, and the evidence highlight switches from underline to a soft tint because a 2px blue line is harsh on black.
- **Printing.** `@media print` for the document-detail sheet: single column, ink-only, evidence appended as footnotes, score with its model version in the footer. Useful for interviews and cheap to keep.
- **Theming per tenant.** Not planned. One product identity; tenants differ in data, not in colour.
- **Design tokens to Figma.** Only if a reviewer asks; the token file is already the source of truth, and a two-way sync is a maintenance liability at this scale.
