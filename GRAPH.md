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
        ┌───────────┬───────────┬───────────┬─────────────┘
        ▼           ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ ┌───────────┐
   │huntstack│ │app-2 │ │podcraft │ │ thrml  │ │whoop-med  │
   └─────────┘ └─────────┘ └─────────┘ └────────┘ └───────────┘
```

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
2. **On finish:** append your result to your own key. Never rewrite another node's key.
3. Return a short summary as your final text (that is what the orchestrator sees).

**Checking that a node actually wrote its key:** `graph_agents/.graph/verify-state.py`
takes a run id plus key names and exits 0 only if each key is present, non-empty, and not
still the `_schema.json` placeholder. It catches the one failure that matters most here —
a node that returned a summary without writing anything.

It does **not** enforce the contract above. It cannot see *who* wrote a key, because
`state.json` records no authorship, so rule 2's "never rewrite another node's key" is
invisible to it and an orchestrator hand-writing every key passes cleanly. It also does
not check content, key shape, staleness, or partially-filled placeholders, and nothing
fires it automatically — it is a check the orchestrator chooses to run, not a gate. The
full list of what it misses is in `feature-graph` § `verify-state.py`.

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
builder. `builder.md`'s own frontmatter still claims it runs "in isolation" and "in
parallel with sibling builders" unconditionally; that is a known open gap, recorded in
`CURRENT-STATE.md`, not a second source of truth.

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

**Before reaching for a cheaper provider:** model tier is the second-biggest lever, not
the first. The stop rule is the first. One `single-loop` instead of an unjustified
six-node diamond saves more than downgrading every node in the fleet would.

Reference cost per MTok (in/out): haiku 4.5 $1/$5 · sonnet 5 $3/$15 · opus 5 $5/$25.


---

## 5. Human gates

Place them exactly where a mistake gets expensive to undo:

- after `architect` — before any code exists (cheapest possible place to change your mind)
- before `ops` — deploys, DB migrations, anything that costs money or touches prod
- before creating a new app — a new repo is a long-term maintenance commitment

Everywhere else, let it run.
