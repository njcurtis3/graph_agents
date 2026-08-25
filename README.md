# graph_agents

An agent fleet for [Claude Code](https://claude.com/claude-code) that turns a feature
request into a scouted, planned, human-approved, built, and independently reviewed
change — without the orchestrator ever writing code itself.

It is **tooling, not a product.** It operates *on* a portfolio of standalone apps that
live beside it (each its own git repo, its own deploys, its own lifecycle) and ships
inside none of them.

## The one invariant

> **No app may import, build against, or read files from another app.**

If two apps need the same thing, the pattern is copy, don't couple. A shared package
turns N standalone products into one distributed monolith you cannot sell, kill, or hand
off separately. The only things allowed to cross app boundaries are conventions,
one-time-copy templates, and this fleet.

## How it works

```
   scout  →  architect  →  ⛔ HUMAN GATE  →  builder(s)  →  reviewer(s)  →  integrator
  (facts)     (plan +                        (implement     (adversarial,   (fan-in,
              shape)                          one slice)     can REJECT)     if diamond)
```

1. **`scout`** (haiku) does read-only recon and returns verified `file:line` facts —
   never a plan, never an opinion.
2. **`architect`** (opus) turns the goal plus scout's facts into a plan and decides the
   graph's shape: a `single-loop` (sequential, when slices share files or there's no
   isolation) or a `diamond` (parallel builders in isolated git worktrees, when 3+ slices
   are genuinely disjoint).
3. **A human gate.** The shape, the slices, the edges, and the explicit "not doing" list
   are shown before any code is written. Nothing proceeds without approval.
4. **`builder`** (opus) implements exactly one slice, in isolation when the target is a
   git repo, sequentially otherwise. Never reviews its own work.
5. **`reviewer`** (opus) runs in a fresh context that never saw the code being written,
   re-derives every check itself rather than trusting the builder's report, and has
   authority to REJECT. Max two attempts per slice before a run stops and escalates to a
   human.
6. **`integrator`** (diamond only) is the one owned merge point — it proves the *whole*
   is coherent, not just that each slice passed alone.

Every node reads and writes a single shared `state.json` for its run — that file is the
only wire between agents that otherwise share no context. `.graph/verify-state.py`
checks that a node actually wrote its key rather than returning a summary and nothing
else.

## Model tiering

`scout` runs on haiku — it's the highest-token node in a typical run and the most
mechanical: glob, grep, read, report `file:line`. That's retrieval, not judgment.
Everything else stays on a frontier tier, and two nodes never get downgraded:
`reviewer`, because a verifier that misses the bug is worse than no verifier, and
`architect`, because shape errors are the expensive ones.

## Layout

```
graph_agents/
  CLAUDE.md              the constitution — the invariant, restated
  GRAPH.md                the graph spec — nodes, edges, shared state, human gates
  CURRENT-STATE.md        a disk-verified snapshot: what's live, what's still a gap
  portfolio/registry.json the index over the app portfolio (see below — not tracked)
  .claude/
    agents/               the six node definitions
    skills/                feature-graph (run the graph), new-app (bootstrap an app)
  .graph/
    runs/<run-id>/         one state.json per unit of work — a run's whole history
    verify-state.py        checks a node actually wrote its result
```

## `portfolio/registry.json` is intentionally not in this repo

The index that routes a task to an app lists real, local directory paths — including a
personal one. It's `.gitignore`d on purpose: the fleet still reads it locally, a clone of
this repo just won't come with it. If you're standing this fleet up for your own
portfolio, write your own `portfolio/registry.json` — see the `$comment` in
`.graph/runs/_schema.json` and the shape used throughout `CLAUDE.md` for the expected
fields (`id`, `path`, `kind`, `status`, `one_liner`, `stack`, `entry_docs`, `owns`).

## Using it

Launch Claude Code from the parent directory that holds this fleet and your apps (not
from inside `graph_agents/` itself — every path here is relative to that parent). Then:

- `/feature-graph` — run a task through the graph: scout, architect, human gate, then
  either a single loop or a parallel diamond converging on one integrator.
- `/new-app` — bootstrap a new standalone app under the portfolio: its own repo, its own
  `CLAUDE.md`, registered in the index, zero coupling to its siblings.

See `CLAUDE.md` for the constitution, `GRAPH.md` for the full protocol, and
`CURRENT-STATE.md` for what's actually been exercised versus what's still a documented
gap — that file is a point-in-time snapshot verified against disk, not aspirational
documentation.
