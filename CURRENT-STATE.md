# CURRENT-STATE — graph_agents

> **Last verified: 2026-08-25**
>
> A point-in-time snapshot **verified against disk**, not a living spec. `GRAPH.md` and
> `CLAUDE.md` describe how the fleet is *supposed* to work; this file records what is
> *actually true right now*. **Stale entries here are worse than missing ones** — if you
> change the fleet, update this file in the same session, and bump the date above.

---

## Status: scaffolded, one shakedown run, zero production use

Built 2026-08-25 in a single session. One end-to-end test run against `huntstack`,
deliberately stopped at the human gate. **No agent in this fleet has written a line of
product code yet.**

---

## What is live

| Thing | State | Path |
|---|---|---|
| Umbrella constitution | live | `graph_agents/CLAUDE.md` (74 ln) |
| Graph spec | live | `graph_agents/GRAPH.md` (178 ln) |
| Portfolio index | live, 5 apps, paths verified | `graph_agents/portfolio/registry.json` (120 ln) |
| Run-state schema | live | `graph_agents/.graph/runs/_schema.json` (28 ln) |
| Root memory shim | live, `@`-imports the constitution | `repos/CLAUDE.md` |
| `.claude` junction | live, verified same-dir | `repos/.claude` → `graph_agents/.claude` |
| 6 agent nodes | written, **not yet exercised as registered agents** | `.claude/agents/` |
| 2 skills | written, **not yet exercised** | `.claude/skills/` |
| Staleness hook | written + pipe-tested (6/6 cases), **never fired** | `.claude/settings.json`, `.claude/hooks/flag-stale-state.py` |

### Node roster (frontmatter verified)

| Node | Model | Tools | Lines |
|---|---|---|---|
| `scout` | haiku | Read, Glob, Grep, Bash, WebSearch, WebFetch | 38 |
| `architect` | opus | Read, Glob, Grep, Bash | 61 |
| `builder` | opus | Read, Write, Edit, Glob, Grep, Bash | 46 |
| `reviewer` | opus | Read, Glob, Grep, Bash | 50 |
| `integrator` | opus | Read, Write, Edit, Glob, Grep, Bash | 40 |
| `ops` | opus | Read, Write, Edit, Glob, Grep, Bash | 40 |

Tiering rationale: `GRAPH.md` § Model tiering. Short version — spend on judgment, not
retrieval. `reviewer` and `architect` are never-downgrade.

---

## How this file stays current

A `PostToolUse` hook on `Write|Edit` runs `.claude/hooks/flag-stale-state.py`. When a
fleet **definition** file changes (`.md`/`.json` under `graph_agents/`) it injects context
telling Claude this snapshot is stale and must be re-verified before the turn ends.

It fires for: agent files, skills, `GRAPH.md`, `CLAUDE.md`, `registry.json`.
It stays silent for: this file itself (no self-trigger), `.graph/runs/**` (run state
churns and is not an architecture change), and everything outside `graph_agents/`.

**It deliberately does not auto-stamp the date.** A bot bumping `Last verified:` without
re-checking anything would make this doc confidently wrong — the exact failure the header
warns about. The hook creates the obligation; a real verification pass discharges it.

---

## Known gaps — things that are NOT true yet

1. **The named agents and skills have never actually run as registered Claude Code
   entities.** They were created mid-session, and registration happens at session start.
   The 2026-08-25 run used built-in agent types (`Explore`, `Plan`) with the node
   instructions injected by hand. **First launch from `repos/` is still an unvalidated
   path** — expect to debug frontmatter or discovery on first real use.
2. **`builder`, `reviewer`, `integrator`, and `ops` have never executed.** Only `scout`
   and `architect` have round-tripped. The fan-out → review → fan-in half of the diamond
   is entirely untested, including worktree isolation.
3. **No diamond has ever run.** The one test resolved to `single-loop`, correctly.
4. **`new-app` has never been used.** All 5 registry entries were back-filled from
   directories that already existed.
5. **Nothing enforces the umbrella invariant.** "No cross-app imports" is prose in
   `CLAUDE.md`. No lint rule, no CI check, no test. It holds only while agents read and
   obey it.
6. **The staleness hook has never actually fired.** All six routing cases pass a direct
   pipe-test, but `.claude/settings.json` did not exist when this session started, so the
   settings watcher is not watching it. Unproven until a fresh session.
7. **State-file writes are convention, not machinery.** Nodes are *told* to append to
   `state.json`; nothing verifies they did. In the 2026-08-25 run the orchestrator wrote
   every state update by hand.

---

## Runs

| Run | App | Shape | Status | Outcome |
|---|---|---|---|---|
| `2026-08-25-refuge-freshness` | huntstack | single-loop | **parked** at human gate | Plan complete, unapproved, no code written |

Parked run detail: `graph_agents/.graph/runs/2026-08-25-refuge-freshness/state.json`

What that run proved: routing through the index worked; `scout` returned `file:line`
facts; `architect` correctly refused to fan out a 2-slice sequence; the human gate held
with `git status` clean on huntstack.

What it found, independent of the feature — **both still open**:
- Two consecutive huntstack scraper runs failed (`scripts/logs/refuge-counts-2026-08-10.log:27`,
  `-2026-08-18.log:27`). Nothing surfaces this in the product.
- huntstack roadmap's "late Aug" OK/AR + LDWF re-scrape window opened 2026-08-25.

---

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-08-25 | Holding company, not monorepo — each app its own git repo | Shared packages turn N sellable products into one distributed monolith |
| 2026-08-25 | Fleet lives in `graph_agents/`, launch from `repos/` | Source of truth stays in one folder; junction makes it discoverable from root |
| 2026-08-25 | `repos/CLAUDE.md` `@`-imports the constitution | Launching from root loads root memory only — the invariant would otherwise never be in context |
| 2026-08-25 | Shared state is a file, not a metaphor | Subagents get fresh context and return only text; a file is the only wire between them |
| 2026-08-25 | `scout` → haiku, everything else opus | Scout is the highest-token, most mechanical node. Verifiers never get cheapened |
| 2026-08-25 | Staleness hook flags, never auto-stamps — **user-confirmed, do not revisit** | An auto-bumped "Last verified" would assert a check that never happened |
| 2026-08-25 | Rejected OpenRouter free models | Routing is session-wide not per-agent; 50 req/day and 20 req/min break fan-out — one scout used 17 tool calls |
| 2026-08-25 | `graph_agents/` is its own git repo — `repos/` still is not | The prohibition in `CLAUDE.md` is on `repos/`, and its stated reason is avoiding a monorepo. `graph_agents/` is a node holding zero app code, so a repo of its own is the same rule every app node already follows — and it is the only rollback path for fleet self-edits |

---

## Changelog

| Date | Change |
|---|---|
| 2026-08-25 | Fleet created: constitution, graph spec, registry, 6 nodes, 2 skills, state schema |
| 2026-08-25 | Moved everything under `graph_agents/`; repathed all cross-references |
| 2026-08-25 | Junction `repos/.claude` → `graph_agents/.claude`; repathed to repos-relative; added root `CLAUDE.md` shim |
| 2026-08-25 | First shakedown run (`refuge-freshness`), parked at gate |
| 2026-08-25 | `scout` sonnet → haiku; added § Model tiering to `GRAPH.md`; tightened scout-brief guidance in `feature-graph` |
| 2026-08-25 | This file created |
| 2026-08-25 | Added `PostToolUse` staleness hook + `.claude/settings.json` (first settings file in the fleet) |
