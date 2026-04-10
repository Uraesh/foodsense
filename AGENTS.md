# FoodSense Design System Rules

These rules define how Codex should implement frontend and Figma-derived UI for this repository. They are tailored to the current `frontend/` codebase and must be followed for every design-facing change.

## Project Scope

- Frontend framework: Next.js App Router with React and TypeScript
- Frontend root: `frontend/`
- App routes live in `frontend/src/app/`
- Reusable UI components live in `frontend/src/components/`
- API helpers live in `frontend/src/lib/`
- Path alias: `@/* -> frontend/src/*`

## Visual Direction

- FoodSense is not a generic admin dashboard.
- The product should feel editorial, warm, and search-centric, with a food-and-discovery identity.
- Prefer a premium culinary/research mood over a cold enterprise look.
- Avoid bland white screens and avoid generic purple gradients.
- Favor layered backgrounds, soft glass or paper surfaces, warm neutrals, and a focused accent color.

## Typography Rules

- IMPORTANT: Do not keep the default `Segoe UI` stack for final UI work.
- Use `next/font` for the production typography setup.
- Prefer a two-font system:
  - headings: expressive serif or display serif
  - body/UI text: clean modern sans-serif
- Good defaults for this project:
  - heading: `Fraunces` or `Bricolage Grotesque`
  - body: `Manrope` or `Plus Jakarta Sans`
- Limit typography to a clear scale with named tokens. Do not hardcode ad hoc font sizes repeatedly.

## Styling Architecture

- IMPORTANT: Global design tokens must live in `frontend/src/app/globals.css`.
- IMPORTANT: New visual values must be introduced as CSS variables before they are reused.
- Use CSS variables for:
  - colors
  - spacing
  - border radius
  - shadows
  - typography scale
  - motion durations
- Prefer component-level styling via CSS Modules or structured class names.
- Inline styles are allowed only for truly dynamic values that depend on runtime computation.
- Do not keep expanding the current inline-style approach for production screens.

## Token Rules

- Define semantic tokens, not only raw tokens.
- Required token families:
  - `--color-bg-*`
  - `--color-surface-*`
  - `--color-text-*`
  - `--color-accent-*`
  - `--space-*`
  - `--radius-*`
  - `--shadow-*`
  - `--font-size-*`
  - `--line-height-*`
  - `--motion-*`
- Never hardcode hex colors inside components once tokens exist.
- Never hardcode repeated spacing values like `18px`, `22px`, `37px` across multiple components.

## Component Organization

- Place reusable primitives in `frontend/src/components/`
- Search-specific components belong in `frontend/src/components/` until a larger feature split is justified.
- Use PascalCase component names and one component per file.
- Export components as named exports unless a route file requires a default export.
- All presentational components should accept typed props and remain easy to reuse.

## Required UI Primitives For This Project

- Before building many screens, establish and reuse these primitives:
  - `SearchField`
  - `Button`
  - `SurfaceCard`
  - `StatusBadge`
  - `SectionHeading`
  - `EmptyState`
  - `LoadingState`
  - `MetricPill`
- Do not build each page with bespoke one-off styles if a primitive can absorb the pattern.

## Search Experience Rules

- The search page is the core experience and must feel intentional.
- The hierarchy should clearly separate:
  - query input
  - active status or strategy
  - ranked results
  - summary or evidence panel
- Results must communicate:
  - title or inferred product label
  - product ID
  - semantic relevance score
  - rating
  - review count
- If the backend returns `lexical_fallback`, the UI must be able to present that state honestly.

## Data And API Rules

- IMPORTANT: Use `frontend/src/lib/api.ts` for backend calls.
- Do not scatter raw fetch calls across presentational components.
- Keep data-fetching logic at the page level or in dedicated client helpers/hooks when needed.
- Components such as result cards and panels should remain mostly presentational.

## Accessibility Rules

- All interactive elements must have visible focus states.
- Search inputs and buttons must have accessible labels.
- Use semantic landmarks and heading order correctly.
- Contrast should remain comfortably readable on warm backgrounds.
- Do not rely on color alone to convey ranking state or fallback state.

## Motion Rules

- Motion should support comprehension, not decorate randomly.
- Use a small set of transitions:
  - page reveal
  - result card stagger
  - loading state pulse or shimmer
- Keep motion subtle and performant.
- Add reduced-motion fallbacks when animations become non-trivial.

## Asset Rules

- Store local static assets in `frontend/public/`
- If Figma MCP returns localhost asset URLs, use them directly or download them into `frontend/public/assets/`
- IMPORTANT: Do not add a new icon package by default.
- Reuse local SVG assets or Figma-provided assets first.

## Figma MCP Integration Rules

These rules apply whenever Figma is connected and designs are implemented from Figma.

### Required Flow

1. Run `get_design_context` first for the exact node
2. If needed, run `get_metadata` to narrow the target
3. Run `get_screenshot` for visual validation
4. Only then implement the UI in this repo
5. Translate the Figma output into this project's conventions instead of copying raw generated markup blindly

### Figma Translation Rules

- Treat Figma output as design intent, not final code style
- Replace hardcoded visual values with project tokens
- Replace repeated one-off wrappers with reusable primitives
- Keep fidelity high, but adapt structure to Next.js App Router and this repo's component layout
- Validate the final UI against the screenshot before considering the work complete

## Frontend Code Quality Rules

- Use strict TypeScript types for props and API payloads
- Prefer small, composable components over large page-local blocks
- Keep route files focused on composition
- Do not mix styling, data fetching, and result ranking logic in the same component without need
- If a component needs many repeated inline styles, extract a CSS Module instead

## Performance Rules

- Avoid unnecessary client components when server rendering is sufficient
- Keep heavy logic out of leaf UI components
- Memoization should not be added by reflex; only use it when profiling or repeated rerenders justify it
- Prefer lean UI trees and reusable surfaces over deeply nested wrappers

## Implementation Priorities For The Next Frontend Pass

- First, replace the bootstrap inline-style page with a token-driven layout
- Then wire the real `/search` backend response into the UI
- Then add honest strategy/fallback presentation
- Then refine typography, spacing, and motion

## Anti-Patterns To Avoid

- Do not keep building production UI with only inline style objects
- Do not hardcode colors or shadows repeatedly across files
- Do not introduce a design system library just for the sake of it
- Do not make the interface look like a default AI chat clone
- Do not hide backend fallback states from the user during the demo
