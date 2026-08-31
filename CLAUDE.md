# Umbrella — holding company constitution

**Telos Research Group** is the working name for the LLC this umbrella will eventually
become. Not yet a formed legal entity — recorded here so it isn't re-decided later.

**You launch from `repos/`.** That is the holding company, and it is deliberately *not* a
git repository. This file lives in `repos/graph_agents/` — the agent fleet, which is
tooling, not an app. **All paths in the fleet are relative to `repos/`.**
Each app beside `graph_agents/` is its own independent repo with its own history, deps,
deploy, and lifecycle.

## The one invariant

> **No app may import, build against, or read files from another app.**

If two apps need the same thing, the pattern is **copy, don't couple**. Duplication
across apps is cheaper than a shared package, because a shared package turns N
standalone products into one distributed monolith you cannot sell, kill, or hand off
separately.

The only things that legitimately cross app boundaries:
- **Conventions** (how we name things, how we structure a repo)
- **Templates** (a starting point, copied once, then owned locally and allowed to drift)
- **The agent fleet** in `graph_agents/` (tooling that operates *on* apps, never *inside* the product)
- **Prose cross-references** — an app's `CLAUDE.md` may *name* a path here for a reader.
  The test is mechanical: if removing `graph_agents/` from disk breaks the app's build,
  test or deploy, it was an edge. If it only breaks a reader's convenience, it was a
  reference, and references are allowed.

An arrow from app A to app B is a **fake edge**. Delete it.

## Layout

```
repos/                            <- launch Claude Code HERE
  .claude/  ──junction──┐         <- resolves into graph_agents/.claude
  graph_agents/         │         <- the fleet. tooling, never product code
    CLAUDE.md           │         <- this file: the constitution
    GRAPH.md            │         <- the agent graph: nodes, edges, state
    portfolio/registry.json       <- the index: one line of truth per app
    .claude/  ◄─────────┘         <- agents + skills actually live here
      agents/                     <- the nodes
      skills/                     <- the routers (task -> graph)
    .graph/runs/<run-id>/         <- shared state for one unit of work
  huntstack/                      <- each its own git repo
  podcraft-ai/
  ...
```

`repos/.claude` is a **directory junction** into `graph_agents/.claude`. They are the same
directory, not a copy — edit either path, there is nothing to keep in sync. It exists so
the fleet is discovered from the root while the source of truth stays in `graph_agents/`.

`graph_agents/` is itself a node in the portfolio graph — but a **tooling** node. It
operates *on* apps. No app depends on it, and it never ships inside a product.

### Launch rule

Always launch from `repos/`. Every path the fleet uses assumes that cwd:

| Thing | Path |
|---|---|
| the index | `graph_agents/portfolio/registry.json` |
| run state | `graph_agents/.graph/runs/<run-id>/state.json` |
| an app | `<id>/` |

If you launch from inside `graph_agents/` instead, these paths break. Don't.

## Read order for any task

1. `graph_agents/portfolio/registry.json` — decide which app(s) this touches
2. That app's own `CLAUDE.md` (`<id>/CLAUDE.md`) — the app is the authority on itself
3. Only then open source files

Do not scan the whole umbrella to answer a question about one app. The registry exists
so you can load 2-3 files instead of five repos.

## Conventions

`graph_agents/conventions/` is the home for cross-app prose conventions — the "how we do
this" documents that are read and copied, never imported.

| Convention | Covers |
|---|---|
| `conventions/mobile-first.md` | Building a UI-bearing app mobile-first while still serving desktop well: width tiers, touch targets, viewport, and a reviewer checklist. |

Whether it applies to a given app is a lookup, not a debate: the `ui` field in
`portfolio/registry.json`.

## Scope rule

Every task belongs to exactly one app, or to the umbrella. If a task claims to belong to
two apps, it is two tasks. Split it before starting.
