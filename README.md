# graph_agents

**Turn a feature request into a scouted, planned, human-approved, built, and
independently reviewed change — without the orchestrator writing a line of code itself.**

```bash
/feature-graph
```

graph_agents is an agent fleet for [Claude Code](https://claude.com/claude-code). It is
**tooling, not a product**: it operates *on* a portfolio of standalone apps that live
beside it — each its own git repo, its own deploys, its own lifecycle — and ships inside
none of them.

## Why

Letting an LLM agent write code unsupervised means trusting a diff you didn't watch get
written; reviewing every change by hand doesn't scale past the first app. graph_agents
picks a third option: force every non-trivial change through the same structure every
time. Facts get established before anyone plans. A human approves the plan — shape,
slices, and the explicit "not doing" list — before any code exists. A reviewer that never
saw the code being written gets the authority to reject it, twice, before a human is
pulled back in. And nothing is called done on the strength of a claim; the close is
checked against git, not against a state file that only knows what it was told.

## Features

### The work graph

```
   scout  →  architect  →  ⛔ HUMAN GATE  →  builder(s)  →  reviewer(s)  →  integrator
  (facts)     (plan +                        (implement     (adversarial,   (fan-in,
              shape)                          one slice)     can REJECT)     if diamond)
```

- **`scout`** does read-only recon and returns verified `file:line` facts — never a plan,
  never an opinion.
- **`architect`** turns the goal plus scout's facts into a plan *and* decides the graph's
  shape: a `single-loop` when slices share files or there's no worktree isolation, a
  `diamond` when 3+ slices are genuinely disjoint and can run as parallel builders in
  linked git worktrees.
- **`builder`** implements exactly one slice — isolated in its own worktree on a
  diamond, sequential otherwise — and never reviews its own work.
- **`reviewer`** runs in a fresh context that never saw the code being written and
  re-derives every check itself rather than trusting the builder's report. Has authority
  to REJECT; capped at two attempts per slice before a run stops and escalates.
- **`integrator`** (diamond only) is the one owned merge point. It proves the *whole* is
  coherent, not just that each slice passed alone — the kind of cross-slice conflict no
  single-slice reviewer could ever see.

### The human gate

The shape, the slices, the file-level edges, and the explicit "not doing" list are shown
before any code is written. Nothing proceeds without approval, and a second gate — behind
`ops`, never invoked automatically — sits in front of anything that deploys.

### Shared state, not shared context

Every node reads and writes one shared `state.json` for its run — the only wire between
agents that otherwise share no context with each other. Each node owns one key and never
rewrites another's; `written_by` stamps make that checkable instead of assumed.
`verify-state.py --audit` checks that the edges actually held: a review with no build
behind it, an integrator running over a REJECTed slice, a run marked `done` with a slice
never built.

### Model tiering

`scout` runs cheap — it's the highest-token node in a typical run and the most
mechanical: glob, grep, read, report `file:line`. That's retrieval, not judgment.
`builder` implements a slice a human already approved, so the judgment call already
happened by the time it runs. `reviewer` and `architect` never get downgraded: a verifier
that misses the bug is worse than no verifier, and a shape error from the architect is the
expensive kind to unwind.

### Guardrails that actually block

Two `PreToolUse` hooks enforce what the rest of this fleet only asks nicely for, and both
fail **closed** — a broken hook denies loudly rather than silently letting the thing
through it exists to stop:

- **The scope guard** denies a builder's `Write`/`Edit`/`Bash` outside the file set the
  human approved at the gate. The Bash half classifies what a command is *about to write*
  before it runs, not after.
- **The commit-attribution guard** denies any `git commit` carrying a Claude co-author,
  a `Claude-Session:` trailer, a generated-with line, or a non-owner `--author` — on
  every agent type, orchestrator included. Commits in this fleet are the owner's alone.

### The board

A heartbeat (`SubagentStart`/`SubagentStop`/`PostToolUse`) logs one line per node event to
`activity.jsonl`, and a third hook renders it live: the moment a node is dispatched, its
board appears in the main tab — goal, per-node status, a row per slice pairing build with
verdict — derived, never authored, so it can't drift from what `state.json` says and costs
no tokens to produce.

### Routers — six skills, each one thing

| Router | What it does |
|---|---|
| `feature-graph` | The main one. Turns a goal into a scout → architect → gate → single-loop-or-diamond run. |
| `new-app` | Scaffolds a new standalone app under the umbrella — own repo, own `CLAUDE.md`, registered in the portfolio index. |
| `fleetview` | Launches the read-only viewer for run state, pointed at this fleet. |
| `close-run` | Checks whether a run may be marked done — audit clean, gate passed, every slice built and reviewed `PASS`, and the work actually merged in **git**, not just claimed in `state.json`. |
| `audit-fleet` | Re-verifies `CURRENT-STATE.md` against disk and reports only drift, instead of trusting whoever last hand-edited it. |
| `postmortem` | Reviews a finished run's activity log for what its shape actually cost and caught — tool counts, diamond concurrency, slice round-trips, whether risk tags earned their keep. |

Every one of them is thin: the logic lives in a testable `.graph/` script, and the
`SKILL.md` just routes to it.

### Verified, not asserted

`close-run`, `audit-fleet`, and `postmortem` are all read-only checkers that print a
report and let a human act on it — none of them write `state.json`, and none of them can
close a run, fix a drift, or draw a conclusion on your behalf. The fleet's own claims
about itself are treated the same way its code is: checked against disk, not trusted
because they were written down once.

## Using it

Launch Claude Code from the parent directory that holds this fleet and your apps — not
from inside `graph_agents/` itself, since every path here is relative to that parent.
Then:

```bash
/feature-graph      # run a task through the graph
/new-app             # bootstrap a new standalone app under the portfolio
/fleetview           # open the run viewer
/close-run           # check whether the open run may be marked done
/audit-fleet         # re-verify CURRENT-STATE.md against disk
/postmortem          # review a finished run's shape and cost
```

## Seeing a run

Run state is JSON on disk, and you can read it as JSON. To look at it instead:

```bash
python fleetview/serve.py        # from the umbrella root
```

**FleetView** is a separate standalone app (`fleetview/`, its own repo) that renders each
run's work graph, the portfolio graph, and the node roster read live from agent
frontmatter — all from files this fleet already writes. It is a *viewer*: read-only, and
it never writes to a run. It is not part of this repo and this repo does not depend on
it — FleetView reads the run-state format as a convention, not an import, and takes the
fleet location as runtime config, so it works against any fleet and this fleet works
without it.

## The one invariant

> **No app may import, build against, or read files from another app.**

If two apps need the same thing, the pattern is copy, don't couple. A shared package turns
N standalone products into one distributed monolith you cannot sell, kill, or hand off
separately. The only things allowed to cross app boundaries are conventions, one-time-copy
templates, and this fleet.

## Layout

```
graph_agents/
  CLAUDE.md               the constitution — the invariant, restated
  GRAPH.md                 the graph spec — nodes, edges, shared state, human gates
  CURRENT-STATE.md         a disk-verified snapshot: what's live, what's still a gap
  portfolio/registry.json  the index over the app portfolio (see below — not tracked)
  .claude/
    agents/                the six node definitions
    skills/                 the six routers listed above
    hooks/                  the guardrails: scope, commit-attribution, staleness, heartbeat, board
  .graph/
    runs/<run-id>/          one state.json per unit of work — a run's whole history
    verify-state.py         checks a node actually wrote its result
    close-run.py            checks whether a run may be closed
    audit-fleet.py          checks CURRENT-STATE.md against disk
    postmortem.py           reviews a finished run's shape and cost
```

## `portfolio/registry.json` is intentionally not in this repo

The index that routes a task to an app lists real, local directory paths — including a
personal one. It's `.gitignore`d on purpose: the fleet still reads it locally, a clone of
this repo just won't come with it. If you're standing this fleet up for your own
portfolio, write your own `portfolio/registry.json` — see the `$comment` in
`.graph/runs/_schema.json` and the shape used throughout `CLAUDE.md` for the expected
fields (`id`, `path`, `kind`, `status`, `one_liner`, `stack`, `entry_docs`, `owns`).

See `CLAUDE.md` for the constitution, `GRAPH.md` for the full protocol, and
`CURRENT-STATE.md` for what's actually been exercised versus what's still a documented
gap — that file is a point-in-time snapshot verified against disk, not aspirational
documentation.
