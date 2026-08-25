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

## Step 3 — the app's own CLAUDE.md

Every app is the authority on itself. Write `<id>/CLAUDE.md` covering:

- what it is, in one paragraph
- how to run it, test it, and deploy it — as actual commands
- its architecture in a few lines: entry point, data flow, where state lives
- its constraints — anything an agent would otherwise get wrong
- this line, verbatim:
  `Standalone app under the repos/ umbrella. Never import from a sibling app; see ../graph_agents/CLAUDE.md.`

## Step 4 — register it

Add an entry to `graph_agents/portfolio/registry.json`, with `path` and `entry_docs` relative to `repos/`. Unregistered apps are invisible to the fleet —
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
