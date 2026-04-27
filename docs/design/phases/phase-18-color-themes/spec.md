# Phase 18 — Color Themes

> Add named color themes to the app, selectable independently from light/dark mode.

## Problem

The app had a single color scheme (blue accents, gray surfaces) with a light/dark toggle. There was no way to personalize the visual identity beyond brightness.

## Changes

**Three themes** — Ocean (blue, default), Forest (emerald), Sunset (amber) — named in the VS Code tradition. Each theme defines a full palette: accent colors, page background, card surfaces, input fields, and header.

**CSS custom properties** — all theme colors are expressed as CSS variables (`--a3`–`--a7` for accent shades, `--bg`, `--surface`, `--hover`, `--input` for chrome). Variables are declared per `data-theme` attribute on the `<html>` element, with separate overrides for dark mode (`html.dark[data-theme="X"]`).

**Tailwind integration** — the `accent` color family is added to `tailwind.config` referencing the CSS variables, enabling standard Tailwind classes (`bg-accent-600`, `ring-accent-500`, etc.) across all templates.

**Colored header** — the header background uses `--a7` (darkest accent shade), giving each theme an immediately recognizable identity similar to VS Code's title bar. Header text uses `text-white`.

**Theme cycle button** — a small colored dot in the header (right of the 🌙 toggle) cycles Ocean → Forest → Sunset → Ocean on click. The dot color reflects the current accent. Choice is persisted in `localStorage` under `color-theme`.

**No flash on load** — the theme init script runs inline before Tailwind renders, applying `data-theme` from `localStorage` before any paint.

**Secondary buttons unchanged** — neutral gray buttons (Cancel, Copy, Ping bot) are intentionally left gray, consistent with VS Code's approach of keeping secondary chrome theme-neutral.
