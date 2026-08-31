# Convention — mobile-first, desktop-complete

A UI that only works on the machine it was built on is not finished. This file is the bar:
build the small screen first, then earn the large one. It is prose and checklists, nothing
more — see § This is a convention, not a dependency at the bottom before you wire anything
to this path.

## Does this apply?

**It applies when a human reaches the app's UI from a device they choose.** That is the
whole test. Public sites, hosted products, anything with a login screen or a URL you send
to someone — those are in.

It does **not** apply to CLIs, libraries, data pipelines, vendor drops, or a local-only
dev/inspection UI bound to `127.0.0.1` that only the operator ever opens. Those get to be
whatever width the operator's monitor is.

The registry answers this per app, so you do not have to re-argue it every run:
`graph_agents/portfolio/registry.json` carries a `ui` field on every entry —
`responsive-web` (this file applies), `desktop-only` (local viewer, does not apply), or
`none` (no UI at all). `kind` is the wrong axis and does not decide this; a `tool` can ship
a public UI and a `product` can ship a viewer nobody but you will ever load.

## Width tiers

Widths, never device names. Device names rot; a number is checkable in a diff.

| Tier | Width | What it means |
|---|---|---|
| **Floor** | **360px portrait** | The design floor. Nothing may break or overflow horizontally at 360. |
| Tablet | `>= 768px` | Layout may add a second column or reflow navigation. |
| Desktop | `>= 1024px` | Full desktop layout. |
| Content cap | `>= 1280px` | Text content gets a max-width; the page stops stretching. |

A scaffolder's own tier names (Tailwind `sm`/`md`/`lg`, MUI breakpoints, whatever) may map
onto these as long as **the floor is 360**. Do not fight the framework's names; do check its
smallest tier actually reaches 360.

## The authoring rule

**Base CSS is the small screen. Larger screens are additive, via `min-width` media queries
only.**

```css
/* base — this IS the 360px layout, no media query */
.card { display: block; padding: 1rem; }

/* larger screens add to it */
@media (min-width: 768px) { .card { display: grid; grid-template-columns: 1fr 1fr; } }
```

No `max-width`-only cascades. No `desktop.css` + `mobile.css` split. Both invert the
cascade so the mobile layout becomes a pile of overrides, and every future change has to be
made twice.

## Prohibitions — each one visible in a diff

- **No fixed px widths on layout containers.** `width: 1200px` on a wrapper is the bug.
  Use `max-width` plus a fluid width.
- **No horizontal overflow at 360px.** Long unbroken strings, wide tables and oversized
  images are the usual causes.
- **No `100vh` on a full-height mobile container.** Mobile browser chrome makes `vh` lie.
  Use `dvh` or `svh`.
- **No hover-only affordance.** If hover is the only way to reveal a control, a touch device
  cannot reach it. Every hover-revealed action needs a tap or focus path.
- **No `user-scalable=no`, no `maximum-scale=1`.** Never. Blocking pinch-zoom breaks the app
  for anyone who needs to magnify it.

## Required presence

A responsive viewport meta in the document head, or the framework's equivalent:

```html
<meta name="viewport" content="width=device-width, initial-scale=1" />
```

Without it a mobile browser renders at a fake ~980px width and scales down. Every other rule
in this file is inert until this tag exists.

## Touch targets

- Interactive elements: **>= 44x44 CSS px effective hit area**, padding included. A 16px icon
  with 14px of padding qualifies; a bare 16px icon does not.
- **>= 8px spacing** between adjacent targets, so a thumb cannot hit two at once.

## Typography and input

- **Body/base font >= 16px.** Under 16px, iOS Safari zooms the page when a form field takes
  focus and does not zoom back out.
- Correct `type` and `inputmode` on every input (`email`, `tel`, `numeric`, `decimal`,
  `search`) so the right keyboard appears.
- Forms usable one-handed: primary actions reachable in the lower half of the screen, not
  stranded in a top corner.

## Desktop is not an afterthought

Mobile-first is an authoring order, not a ceiling. Shipping a stretched phone layout on a
27" monitor fails this convention just as hard as horizontal overflow at 360.

- **Content max-width.** Prose lines cap around 60-75 characters. A full-bleed paragraph on a
  1600px window is unreadable.
- **Keyboard order and a visible focus ring.** Tab order follows visual order; focus is
  always visible. Do not remove the outline without replacing it.
- **Hover as enhancement only.** Hover may make something nicer. It may never make something
  reachable — see the prohibition above.
- **Use the extra width for real.** A second column, a persistent sidebar, a table that stops
  being a card list. If desktop is byte-identical to mobile with wider margins, the extra
  width was wasted.

## Images and media

- Every image and video carries intrinsic `width`/`height` attributes or an `aspect-ratio`,
  so the layout does not shift when it loads.
- Responsive sources (`srcset`/`sizes`, or the framework's image component) wherever the
  scaffolder supports them — a 2400px hero downloaded onto a 360px screen is a real cost.
- Media is fluid: `max-width: 100%`, never a fixed pixel width.

## Reviewer checklist

Yes/no, answerable by reading a diff. `reviewer.md` points here by name.

1. Does every new/changed layout container avoid a fixed px width?
2. Is every new media query `min-width`, with the base styles being the small-screen layout?
3. Does a new document head carry `width=device-width, initial-scale=1`, with no
   `user-scalable=no` and no `maximum-scale=1`?
4. Does every new interactive element have a >= 44x44px effective hit area?
5. Is every hover-revealed action also reachable by tap or focus?
6. Is every full-height container using `dvh`/`svh` rather than `100vh`?
7. Are form inputs and body text >= 16px?
8. Do new inputs set the right `type`/`inputmode`?
9. Do new images/videos declare `width`/`height` or `aspect-ratio`?
10. Does the desktop layer do something real with the extra width, and cap content width?

Anything you cannot answer from the diff is a **note**, not a rejection. This checklist is
deliberately limited to what is readable in code — no device lab, no screenshots, no
running browser.

## This is a convention, not a dependency

This file is **read and copied as guidance**. No app may import it, build against it, or
resolve this path at build, test or deploy time. An app's `CLAUDE.md` may *name* this path
for a human reader — that is a prose cross-reference and it is allowed. The mechanical test:
delete `graph_agents/` from disk, and every app must still clone, install, test and deploy.

When a new app is born with `ui: responsive-web`, the width tiers and the viewport /
touch-target bar get **copied into that app's own `CLAUDE.md`** under `## UI targets`, then
owned locally and allowed to drift. Copy, don't couple.

See `graph_agents/CLAUDE.md` § The one invariant.
