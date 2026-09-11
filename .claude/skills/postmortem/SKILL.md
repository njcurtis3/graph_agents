---
name: postmortem
description: Review a finished run's activity.jsonl and state.json for what the shape actually cost and caught — tool counts, diamond concurrency, slice round-trips, whether risk tags earned their cost. Use when asked to "review this run", "postmortem this run", or "was this diamond/risk-tag worth it".
---

# postmortem

You are the **orchestrator**. This is not a gate and it blocks nothing — it is the
2026-08-28 `archive-adapters` review (the one that produced risk tagging) done again,
data-backed instead of from memory.

## Step 1 — run it

```bash
python graph_agents/.graph/postmortem.py            # the run .graph/CURRENT names
python graph_agents/.graph/postmortem.py <run-id>
```

Works on a closed run or an open one. Always exits 0 — it reports, it does not fail.

## What it tells you, and why each part is trustworthy

| Section | Reads | Why it survives gap #20 |
|---|---|---|
| Tool activity | `tool` events per agent lane | never touches a `stop` timestamp |
| Concurrency (diamond only) | first/last `start`/`tool` timestamp per builder lane | windows are tool-bounded, not stop-bounded |
| Slice round-trips | `reviews.<slice>` attempts, via `verify-state.py`'s own resolver | pure `state.json`, no activity involved |
| Risk-tag fit | round-trips grouped by `architect.plan[].risk` | same — `state.json` only |

**Gap #20 is still open** (`CURRENT-STATE.md`): `activity.jsonl` carries `stop` events with
no matching `start`, stamped `orchestrator`, interleaved with real work. This script never
reads one. That is also why it prints **no duration, no wall-clock, no "this run took
Nh"** — nothing here is a `start`/`stop` pair. If gap #20 closes, duration belongs added
here once, not reinvented per-caller.

## Reading the concurrency line

- `shape is single-loop` → N/A, correctly. Concurrency was never claimed.
- `diamond`, fewer than 2 builder lanes recorded → the heartbeat didn't distinguish
  concurrent builders (this has happened — `archive-adapters`' own log shows one
  `builder` agent_id for three worktree builders). That is a finding about the
  heartbeat, worth booking as a gap, not a bug in this script.
- `N/M pairs overlap` → the real signal. Zero overlap on a diamond means the builders
  were spawned together but never proven to run at the same time — say so plainly rather
  than assuming the shape earned its cost.

## Reading the risk-tag fit

It flags the two outcomes worth acting on:

- **high-risk slices are where the loops are** — the tag is doing its job, leave it alone.
- **low-risk looped MORE than high-risk** — the architect's risk call missed on this run.
  Worth a note in `CURRENT-STATE.md`'s Decisions log if it is not a one-off.

A single run is one data point. Don't rewrite `architect.md`'s risk-tagging rule off one
postmortem — look for the pattern across a few before touching the node that owns it.

## What this skill is not

- **Not `/close-run`.** That one gates whether a run may be marked done. This one runs on
  a run at any status and has no opinion on whether it should close.
- **Not a duration report.** See gap #20 above. If you need wall-clock, that is a separate,
  currently-blocked piece of work — don't approximate it from this script's numbers.
- **Not a verdict on the reviewer.** Round-trip counts say how many times a slice looped,
  not whether the loop was deserved.
