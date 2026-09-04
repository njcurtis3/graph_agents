# The agent graph

Two graphs. Keeping them separate is the whole design.

---

## 1. The portfolio graph (static, long-lived)

Nodes are **apps**. This graph is intentionally almost edgeless.

```
                  ┌──────────────────┐
                  │ repos/  UMBRELLA │  conventions + templates
                  └────────┬─────────┘
        ┌──────────────────┼──────────────────────────────┐
        ▼                  │                              │
 ┌──────────────┐          │        (product nodes)       │
 │ graph_agents │──────────┘                              │
 │  the fleet   │  operates ON apps; no app depends on it │
 └──────────────┘                                         │
        ┌─────────┬─────────┬─────────┬─────────┬─────────┘
        ▼         ▼         ▼         ▼         ▼         ▼
    ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
    │ App 1 │ │ App 2 │ │ App 3 │ │ App 4 │ │ App 5 │ │ App 6 │
    └───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

Some of those nodes are tools rather than products (`kind` in the registry). The graph does
not care: a tool node is still standalone, still owns its own repo, and still gets zero
edges to its siblings.

Edges umbrella→app are **template edges**: one-time copy, then the app owns it and is
allowed to drift. There are **no app↔app edges**. Ever. See `CLAUDE.md`.

The `graph_agents/portfolio/registry.json` file is the **index** over this graph. It is what lets an
agent answer "where does this work go?" without reading five repos.

---

## 2. The work graph (dynamic, per task)

Nodes are **subagents** in `graph_agents/.claude/agents/` (reached as `.claude/agents/` from `repos/`). A new work graph is generated for each
task. The canonical shape is the **diamond**:

```
   goal
     │
     ▼
 ┌────────┐      read-only recon; writes facts into state
 │ scout  │
 └───┬────┘
     ▼
 ┌──────────┐    turns goal + facts into a plan AND into this graph's shape
 │architect │    ← this node is the router
 └───┬──────┘
     │  ── HUMAN GATE ──  you approve the plan before any code is written
     │
     ├──── fan-out (only if slices are genuinely independent) ────┐
     ▼                    ▼                    ▼                  │
 ┌────────┐          ┌────────┐          ┌────────┐               │
 │builder │          │builder │          │builder │   isolated    │
 │ slice1 │          │ slice2 │          │ slice3 │   worktrees   │
 └───┬────┘          └───┬────┘          └───┬────┘               │
     ▼                   ▼                   ▼                    │
 ┌────────┐          ┌────────┐          ┌────────┐               │
 │reviewer│          │reviewer│          │reviewer│   FRESH context each
 └───┬────┘          └───┬────┘          └───┬────┘   (never the builder's)
     │                   │                   │                    │
     │  conditional edge: REJECT ────────────┼────────────────────┘
     │                   │                   │        (max 2 loops, then escalate)
     └───────── fan-in ──┴───────────────────┘
                         ▼
                   ┌───────────┐   the single owned merge point
                   │integrator │
                   └─────┬─────┘
                         │  ── HUMAN GATE ── before deploy / migration / spend
                         ▼
                     ┌──────┐
                     │  ops │
                     └──────┘
```

### The stop rule (read this before building any graph)

Do **not** build a graph for:
- one file, one bug, one endpoint
- anything you could describe in a single paragraph
- anything where the slices would touch the same files

For those, use a **single loop**: one agent, one context, done. The graph costs real
tokens and real wall-clock. It earns that back only when slices are genuinely parallel
and verification genuinely needs a context that never saw the code being written.

Rough line: **3+ independent slices, or a change you would not merge unreviewed.**

**No repo, no diamond.** Before choosing a diamond, check that the target is a git repo:

```bash
git -C <target> rev-parse --is-inside-work-tree
```

If that exits non-zero, `isolation: "worktree"` is unexecutable — a worktree requires a
git repo — so the fan-out above has **no isolation and no rollback**. Builders write into
one tree and collide, `builders.<slice>.branch` is the empty string because there is no
branch, and a corrupted file cannot be restored because there is nothing to restore from.
Force **`single-loop`**, or make the target its own repo first. `repos/` is deliberately
not a repo (`CLAUDE.md`), so anything targeting it is permanently in degraded mode. Full
pre-flight: `feature-graph` step 0.5.

One case forces `single-loop` even *with* a repo: a run that edits
`graph_agents/.claude/agents/**` or `.claude/skills/**` is rewriting the definitions it
spawns from. Registration happens at session start, so start a fresh session before the
next fleet run.

### Delete fake edges

An edge exists only if a real artifact moves along it. If node B doesn't consume
anything node A produced, B doesn't depend on A — run them in parallel. Sequential
chains that exist only because they "feel ordered" are the single most common way
these graphs get slow.

---

## 3. Shared state — how edges actually carry data

Claude Code subagents start with a **fresh context** and return **only their final
text**. They cannot see each other's work. So "shared state travelling along edges" is
not a metaphor here — it is a file:

```
graph_agents/.graph/runs/<run-id>/state.json      # relative to repos/
```

Contract for every node:
1. **On start:** read `state.json`. That is your only inherited context.
2. **On finish:** append your result to your own key, including `written_by` naming
   yourself. Never rewrite another node's key, and never stamp `written_by` on one that
   is not yours.
3. **Return a HEADLINE, not the handoff.** Three lines, no verbatim command output, no
   file lists, no findings bodies. Rule 2 already put those in your key, which is what
   the next node actually reads — nothing consumes your return text but the orchestrator's
   main tab, and a human is the only thing there. Repeating the key in the return prints
   the machine channel into the human one, and the run then reads as several thousand
   words of correct, necessary, unreadable detail. Each node's own file gives its exact
   shape. `architect` and `ops` are the two exceptions: their returns are **gate**
   material, not status, and a human cannot approve a summary of a plan or a deploy they
   have not been shown.

`written_by` (added 2026-08-26) is the only authorship this file has ever carried.
Without it rule 2 was unverifiable *by construction*: an orchestrator hand-writing all
six keys read exactly like six nodes doing their jobs. `--audit` now rejects
`builders.<slice>` stamped `orchestrator`, and `reviews.<slice>` stamped `builder`.

**Checking that a node actually wrote its key:** `graph_agents/.graph/verify-state.py`
takes a run id plus key names and exits 0 only if each key is present, non-empty, and not
still the `_schema.json` placeholder. It catches the one failure that matters most here —
a node that returned a summary without writing anything.

It does **not** check content, key shape, or staleness. The full list of what it misses
is in `feature-graph` § `verify-state.py`.

**The edges, however, are now machinery.** `verify-state.py --audit <run-id>` asks the
question a state file can answer without being told which node just ran: did the edges
hold? Builders written while `approved_by_human` is still false, a review with no build
behind it, a fan-in over a slice that never passed, a run closed `done` with a slice
unbuilt or not `PASS`, a key stamped with the wrong node's name, template text left
sitting inside an otherwise-written key. That
mode is fired automatically by `.claude/hooks/flag-state-gap.py` on every `Write`/`Edit`
of a `state.json` — including writes made by subagents, so the complaint lands on the
node that just wrote. It is silent on a merely half-filled run, because that is what work
in progress looks like.

So the split is: **ordering and authorship are enforced, content is not.** A node can
still write nonsense into its own key, on schedule, under its own name, and nothing will
notice.

### The heartbeat — what the nodes *did*

`state.json` records what each node **concluded**, and only when it finishes. Nothing in
it moves while a node is working, so a run in flight is invisible.

`.claude/hooks/record-activity.py` fills that in. On `SubagentStart`, `SubagentStop` and
every `PostToolUse` it appends one compact line to
`.graph/runs/<run-id>/activity.jsonl` — timestamp, event, `agent_type`, `agent_id`, tool
name. FleetView renders it as a live lane; it is also the evidence base for four things
this fleet has never been able to answer with data rather than assertion:

- **model tiering** — §"Model tiering" argues cost hard and has never measured it. Tool
  counts and durations per `agent_type` are the measurement.
- **reviewer independence** — a re-review's `SubagentStart` carries a *new* `agent_id`,
  which makes "a fresh reviewer" checkable rather than asserted.
- **real parallelism** — when a diamond finally runs, overlapping timestamps are what
  prove the builders ran concurrently rather than merely being spawned together.
- **stalls** — the same tool repeating with no progress is visible in the tail.

⚠️ **Two of those four read `start`/`stop` pairs, and the `stop` half is currently
polluted** — 471 of 503 recorded stops are phantoms that never had a matching start. Node
durations measured naively from this file are wrong. See `CURRENT-STATE.md` gap #20.

**Note what this is not: an overseer agent.** One was considered and rejected. A subagent
is spawned, runs, returns text and ends — there is no loop for it to observe from, no
channel to its siblings, and a node consuming nothing and producing nothing is exactly
the fake edge §2 says to delete. The hook layer already runs alongside every node and is
handed `agent_id`/`agent_type` on every tool event. Oversight belongs where it can
actually see.

### The board — the human channel, rendered

Rule 3 caps what each node *says*. It does not by itself make a run legible: eight
headlines scattered between tool calls is still something you have to reassemble in your
head. `.graph/brief.py` does the reassembling.

```bash
python graph_agents/.graph/brief.py            # the run .graph/CURRENT names
python graph_agents/.graph/brief.py <run-id>
```

It prints one board: the gate, the goal, a line per node, a row per slice showing build
and verdict together, and — from `activity.jsonl` — what is running right now and for how
long. Roughly ten lines for a run whose `state.json` is several hundred.

**Nothing in it is authored.** Every value is derived from `state.json` and
`activity.jsonl`, which the fleet already writes. That is the design, not a shortcut: a
board no node writes cannot drift from the run, cannot be forged, and costs no node a
token. The moment a node is asked to author the summary as well, it can be wrong about it
— the same argument `--audit` makes against trusting a node's own account of its work.
It reuses `verify-state.py`'s placeholder rules rather than restating them, so "written"
means on the board exactly what it means to the audit.

**It also prints itself, at dispatch.** `.claude/hooks/show-board.py` fires on `PostToolUse`
for the `Agent` tool — the spawn call — and hands the board back as `systemMessage`,
**observed reaching the main tab 2026-09-03**. Not `SubagentStop`, which looks like the
right event and is not: it is a *display* event, so both its stdout and its `systemMessage`
go to Claude's context "instead of being shown in the transcript", reaching the orchestrator
and never the human. `CURRENT-STATE.md` gap #19 carries the quotes and gap #20 the second
reason.

**The hook fires when a node starts, not when it finishes** — measured, not assumed: all 32
`Agent` events in the heartbeat land within 0.2s of a `SubagentStart`, never near a node's
own stop. A spawn call returns a handle and the node runs in the background. So that board
shows the run as the node *picks it up*, and no hook can print one when the node comes back:
the event that fires then is `SubagentStop`, which cannot address a human.

So there are two boards per node, from two actors. The hook prints the dispatch board for
free. The orchestrator prints the **return** board itself, and the boards at the transitions
no node marks at all — after the gate, after a merge, at the close (`feature-graph` § the
board). FleetView renders the same two files with more room.

Schema in `graph_agents/.graph/runs/_schema.json`. Because state is on disk, a run survives a
crashed session, a `/clear`, or you walking away — pick it back up by pointing a fresh
orchestrator at the run directory.

---

## 4. Node roster

| Node | Model | Context | Writes code? | Job |
|---|---|---|---|---|
| `scout` | haiku | read-only | no | Find the facts. What exists, where, what breaks. |
| `architect` | opus | read-only | no | Goal + facts → plan + graph shape. The router. |
| `builder` | opus | isolated worktree † | yes | Implement exactly one slice. |
| `reviewer` | opus | fresh, never the builder's | no | Adversarial. Has authority to REJECT. |
| `integrator` | opus | main tree | yes | The one owned merge point. Resolves conflicts. |
| `ops` | opus | main tree | yes | CI, env, deploy. Always behind a human gate. |

† **Only where the target is a git repo.** In degraded mode the builder runs in the main
tree with no isolation and no rollback, which is why that case is `single-loop` and one
builder. `builder.md`'s frontmatter says the same thing in the same words — that gap was
closed 2026-08-25 (`6630dc1`), and this row and that file are no longer two sources of
truth.

**Reviewer independence is non-negotiable.** A builder reviewing its own work is not a
verification edge, it's a fake edge. Always a separate agent invocation.


### Model tiering — why scout is cheap and the rest are not

The rule: **spend on judgment, not on retrieval.**

`scout` is the highest-token node in a typical run and the most mechanical one. It
globs, greps, reads, and reports `file:line`. That is pattern-matching, not reasoning —
haiku does it at roughly a fifth the cost of a mid-tier model, and it is usually the
single biggest lever on a run's total spend.

Everything else stays on opus, and two nodes especially must never be downgraded:

- **`reviewer`** — its entire value is catching what the builder missed. A verifier that
  misses the bug is *worse* than no verifier, because it launders a bad diff as reviewed.
  Cheapening this node doesn't save money, it removes the reason the graph exists.
- **`architect`** — it decides the shape, and shape errors are the expensive ones. In the
  2026-08-25 huntstack run it was the architect that caught `survey_type` having five live
  values with a wrong schema comment; a flat-threshold badge built from the ticket text
  would have shipped broken.

**The consequence of a cheap scout:** haiku is less able to self-scope, so its brief must
be tighter. Tell it exactly which questions to answer and which files to start from.
Don't hand it "go look at the app." A vague scout brief is where the savings evaporate —
it reads everything, returns mush, and the architect plans on sand.

**The mechanical half of that brief is now a script.** `graph_agents/.graph/scout-facts.py
<app-id>` computes what every scout was re-deriving by hand — git repo or not, branch,
HEAD, dirty state, per-repo commit identity, registry entry, which entry docs exist, stack
on disk vs. stack claimed — and `scout.md` step 0 runs it before anything else.

A per-app fact **cache** was designed first and rejected on evidence (2026-08-28). Past
scout keys were checked against reality: "graph_agents/ is NOT a git repository" had become
false, and "6 app directories" had become eight. The facts scouts repeat most are the ones
that rot fastest, and one of them — git-repo status — decides the graph's shape via § "No
repo, no diamond". A cache would have served a confident wrong answer to exactly the
question that must not be wrong. The script stores nothing, so it cannot go stale; the cost
of recomputing a `git rev-parse` is far below the cost of trusting a stale one.

**Before reaching for a cheaper provider:** model tier is the second-biggest lever, not
the first. The stop rule is the first. One `single-loop` instead of an unjustified
six-node diamond saves more than downgrading every node in the fleet would.

Reference cost per MTok (in/out): haiku 4.5 $1/$5 · sonnet 5 $3/$15 · opus 5 $5/$25.


---

## 5. Human gates

Place them exactly where a mistake gets expensive to undo:

- after `architect` — before any code exists (cheapest possible place to change your mind).
  **What you approve here is now binding**: `.claude/hooks/guard-builder-scope.py` denies
  a builder's `Write`/`Edit` outside `architect.plan[].files`, so the file set is a
  boundary rather than a description. Widening it after the fact is possible, deliberate
  and recorded — `scope_exceptions` plus the slice's `deviation_from_approved_plan` —
  never silent. Read the file list at the gate as if it were a permission grant, because
  it is one.
- before `ops` — deploys, DB migrations, anything that costs money or touches prod
- before creating a new app — a new repo is a long-term maintenance commitment

Everywhere else, let it run.
