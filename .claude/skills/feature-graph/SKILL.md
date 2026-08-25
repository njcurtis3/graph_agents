---
name: feature-graph
description: Run a task through the work graph — scout, architect, human gate, then either a single loop or a parallel diamond of builders and independent reviewers converging on one integrator. Use when starting any non-trivial piece of work on an app under the umbrella. Also use when asked to "run the graph" or "fan this out".
---

# feature-graph

You are the **orchestrator**. You do not implement. You own the state file and the edges.

Run this from `repos/`. Apps live at `<id>/`; the fleet's files live under `graph_agents/`.

## Step 0 — the stop rule

Before anything: is this actually a graph? One file, one bug, one endpoint, or something
you could describe in a paragraph is a **single loop**. Say so, do it directly, and skip
this skill. Graphs cost tokens and wall-clock; make them earn it.

## Step 0.5 — pre-flight: can this target hold a diamond?

Two checks. Both run **before** you pick a shape, and neither is optional. This step is
numbered `0.5` on purpose: nothing downstream may renumber.

**1. Is the target a git repo?**

```bash
git -C <target> rev-parse --is-inside-work-tree
```

A worktree requires a git repo. If that exits non-zero there is **no isolation and no
rollback** — parallel builders write into one tree and collide (`GRAPH.md` § the stop
rule), and a bad edit cannot be reverted because there is nothing to revert to. Two
allowed responses, never a third:

- run **`single-loop`** regardless of slice count, and say in the final summary that the
  shape was *forced* by the absence of a repo rather than chosen; or
- make the target a repo first (`git init` in that directory alone, one baseline commit),
  then the diamond is on the table again.

`repos/` is deliberately not a repo (`CLAUDE.md`), so a run whose target is `repos/` — or
any directory that is not itself a repo — is always in degraded mode.

**What degraded mode costs, stated plainly:** no `isolation: "worktree"`, so no parallel
builders. No branch per slice, so `builders.<slice>.branch` is the empty string. No
`git checkout --` and no `reset --hard`, so a builder that corrupts a file has destroyed
it. The blast radius of one bad edit is the whole target.

**2. Is the target the fleet's own definitions?**

If the run edits `graph_agents/.claude/agents/**` or `graph_agents/.claude/skills/**`,
force **`single-loop`** regardless of slice count and regardless of the repo check. You
are rewriting the definitions you spawn from. Tell the user to **start a fresh session
before the next fleet run**: agent registration happens at session start, so what is
running now is what was on disk when the session opened — not necessarily what is on
disk after the run.

## Step 1 — open the run

```bash
RUN=$(date +%Y-%m-%d)-<short-slug>
mkdir -p graph_agents/.graph/runs/$RUN
cp graph_agents/.graph/runs/_schema.json graph_agents/.graph/runs/$RUN/state.json
```

Fill `run_id`, `goal` (the user's own words), and `app` (from `graph_agents/portfolio/registry.json`).
If the goal spans two apps, it is two runs. Split it.

## Step 2 — scout

Spawn `scout` with the run path. It appends verified facts. Read them yourself before
continuing — you are the one who has to notice if the facts kill the goal.

Do not advance until this exits 0 — a node that returned a summary without writing
its key has not run:

```bash
python graph_agents/.graph/verify-state.py $RUN scout
```

**Write the brief tightly.** `scout` runs on haiku (see GRAPH.md § Model tiering), which
is cheap but does not self-scope well. Hand it:

- the app id and the two entry docs to start from
- a numbered list of the specific questions it must answer
- your *unverified guess* at which files are involved, explicitly marked as a guess to
  confirm or correct
- one thing you suspect will break the plan, named — so it hunts rather than surveys

"Go look at the app" produces mush and the architect then plans on sand. That is where a
cheap scout stops being cheap.

## Step 3 — architect

Spawn `architect` with the run path. It returns a shape and slices.

```bash
python graph_agents/.graph/verify-state.py $RUN architect
```

## Step 4 — HUMAN GATE ⛔

Show the user the shape, the slices, the edges, and the NOT DOING list. Wait.
This is the cheapest possible moment to change direction — no code exists yet. Never
skip it because the plan "looks obviously right."

Set `approved_by_human: true` only after they actually say so.

## Step 5 — execute

**If `single-loop`:** spawn one `builder`, then one `reviewer`. Done. No integrator needed.

**No repo, no diamond.** Re-run the step 0.5 check before you fan out:

```bash
git -C <target> rev-parse --is-inside-work-tree
```

If it exits non-zero, `isolation: "worktree"` is **unexecutable** — a worktree requires a
git repo. Do not fan out. Run the single-loop branch above, sequentially, and state in the
final summary that the shape was forced by the missing repo. Never fan out without
isolation and hope the file sets stay disjoint; that is how two builders overwrite each
other with no way back.

**If `diamond`:** spawn **all builders in one message** so they run concurrently, each with
`isolation: "worktree"` (they edit files in parallel; without isolation they will collide).

As each builder returns, immediately spawn its `reviewer` — do **not** wait for the other
builders. That barrier is the most common way these runs waste wall-clock. A slice that
finished in 2 minutes should be under review while a slow slice is still building.

After each builder returns, and again after each reviewer, verify the key landed
before moving on:

```bash
python graph_agents/.graph/verify-state.py $RUN builders.<slice>
python graph_agents/.graph/verify-state.py $RUN reviews.<slice>
```

An empty key exits 1. Re-prompt that node to write it; do not write it for them.

On `REJECT`: send the findings back to that slice's builder. Re-review with a **fresh**
reviewer. Max 2 attempts, then stop and escalate to the user.

## Step 6 — fan-in

When every slice is `PASS`, spawn `integrator` once. It merges and runs the **full** suite.
If it comes back `blocked`, report which merge turned it red — do not paper over it.

```bash
python graph_agents/.graph/verify-state.py $RUN integrator
```

## Step 7 — ops

Only if the user asks. Behind its own gate.

## `verify-state.py` — what it checks, and what it does not

`graph_agents/.graph/verify-state.py` is a read-only, stdlib-only checker. Give it a run
id (or a direct path to a `state.json`) plus one or more key names — dotted keys like
`builders.s2` work — and it exits 0 only if every named key is **present**, **non-empty**,
and **not still the `_schema.json` placeholder**. On failure it exits 1 and prints one
line naming the key. It never writes.

That is the whole of it. **It is a check, not a gate.** Nothing fires it automatically:
no hook invokes it, and the only references to it in the fleet are the call sites in this
file. It runs because the orchestrator chooses to run it.

Seven things it does **not** check. Do not oversell it:

1. **Content correctness.** A key holding `{"status": "done"}` and nothing else passes.
2. **Key shape.** It consults `_schema.json` for placeholder *identity* only, never for
   structure — a missing `branch`, a missing `verdict`, or an invented field all pass.
3. **Who wrote the key.** `state.json` records no authorship, so the
   never-rewrite-another-node's-key contract is invisible to it, and an orchestrator
   hand-writing every key still passes.
4. **Staleness.** No timestamps, so a key left over from a previous attempt passes.
5. **Numbers and booleans are non-empty by design** — a real `parallel_safe: false` must
   not look unwritten — so a hand-written `{"gated": false}` that differs from the
   template passes.
6. **Partial placeholders.** Identity is compared on the whole value, so a
   `builders.<slice>` whose `status` was filled in while `branch` is still the template's
   description passes.
7. **It is advisory, not enforcing.** See above: nothing fires it for you.

## Orchestrator rules

- **Never implement anything yourself.** The moment you edit a file you have destroyed the
  independence the graph is built on.
- **Never review a slice yourself.** You have seen the builder's summary; your context is
  contaminated. Always a fresh `reviewer`.
- Append to `log` in state at every transition. That log is how a fresh session resumes.
- Report faithfully. If a slice was skipped, a test failed, or you dropped scope, say so
  explicitly in the final summary.

## Resuming

Point a fresh session at `graph_agents/.graph/runs/<run-id>/state.json`. The state file is the run —
context loss is not run loss.
