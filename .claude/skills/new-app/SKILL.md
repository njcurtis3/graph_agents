---
name: new-app
description: Bootstrap a new standalone application under the holding-company umbrella — its own git repo, its own CLAUDE.md, registered in the portfolio index, with zero coupling to sibling apps. Use when starting a new app, product, or site under the umbrella.
---

# new-app

A new app is a long-term maintenance commitment, not a folder. Treat it that way.

## Step 1 — HUMAN GATE ⛔

Before creating anything, get explicit answers and confirm them back:

1. **id** — kebab-case, becomes the directory and repo name
2. **one_liner** — what it does, one sentence. If this is hard to write, the app is not ready to exist.
3. **kind** — `product` | `site` | `tool` | `vendor`
4. **stack** — language and framework
5. **Why is this not a feature of an existing app?** If there is no clean answer, it probably is one. Say so.
6. **ui** — `responsive-web` | `desktop-only` | `none`. One-line test: does a human reach
   this on a device they choose? If yes it is `responsive-web`. Local-only dev/inspection
   UIs (a viewer bound to `127.0.0.1`) are `desktop-only`; CLIs, libraries and pipelines
   are `none`.

Do not create anything until they confirm.

## Step 2 — create it standalone

```bash
# from repos/ — apps are siblings of graph_agents/
mkdir -p <id> && cd <id> && git init
```

It gets its **own** repo. It does **not** get added to a root workspace, a root lockfile,
or a shared tsconfig/pyproject — none of those exist here, and creating one would collapse
the holding company into a monorepo.

Scaffold with the ecosystem's own tool (`npm create`, `uv init`, `cargo new`, …). Do not
hand-roll what a scaffolder does correctly.

**If `ui` is `responsive-web`, then apply `graph_agents/conventions/mobile-first.md` to what
the scaffolder just generated:**

- set the viewport meta (`width=device-width, initial-scale=1`)
- establish the 360px base layer — base styles are the small-screen layout, larger screens
  added via `min-width` only
- delete any desktop-fixed-width default the scaffolder emitted (a `width: 1200px` wrapper,
  a `min-width` on `body`, a demo page that overflows at 360)

This step is not optional. Ecosystem scaffolders do not default to mobile-first; they emit
a desktop demo page. If nobody post-processes it, the app is desktop-shaped from commit one
and retrofitting it later rewrites the layout layer.

## Step 3 — the app's own CLAUDE.md

Every app is the authority on itself. Write `<id>/CLAUDE.md` covering:

- what it is, in one paragraph
- how to run it, test it, and deploy it — as actual commands
- its architecture in a few lines: entry point, data flow, where state lives
- its constraints — anything an agent would otherwise get wrong
- this line, verbatim:
  `Standalone app under the repos/ umbrella. Never import from a sibling app; see ../graph_agents/CLAUDE.md.`

  That line names a path outside the app, which looks like the dependency the constitution
  forbids. It is not one: it is a **prose cross-reference for a human or an agent reading
  the file**, and nothing the app builds, imports, runs or ships resolves it. The app must
  still clone, install, test and deploy with `graph_agents/` absent from the disk. If you
  ever find yourself making code read that path, you have turned a convention into an
  edge — delete it. See `CLAUDE.md` § The one invariant.

When `ui` is `responsive-web`, the app's CLAUDE.md must also carry its **own copy** of the
width tiers and the viewport / touch-target bar under a `## UI targets` heading — copied out
of `graph_agents/conventions/mobile-first.md`, then owned locally and allowed to drift, like
any other copy. The app stays the authority on itself. It may *name*
`graph_agents/conventions/mobile-first.md` alongside the copy; that is the same kind of
prose cross-reference as the line above, subject to the same test.

## Step 4 — register it

Add an entry to `graph_agents/portfolio/registry.json`, with `path` and `entry_docs` relative to `repos/`. The entry must include `ui` — the fleet routes on it. Unregistered apps are invisible to the fleet —
the registry is the index every agent routes through.

## Step 5 — first commit

```bash
git add -A && git commit -m "Initial scaffold"
```

Do not create a remote or push unless the user asks.

## Copying from a sibling app

Encouraged — copy the file, then **own it locally**. Strip anything specific to the source
app. Never symlink, never reference across the boundary, never extract it into a shared
package. Divergence between the copies later is expected and fine; that is the price of
standalone, and it is cheaper than coupling.
