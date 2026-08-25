# CURRENT-STATE — graph_agents

> **Last verified: 2026-08-25**
>
> A point-in-time snapshot **verified against disk**, not a living spec. `GRAPH.md` and
> `CLAUDE.md` describe how the fleet is *supposed* to work; this file records what is
> *actually true right now*. **Stale entries here are worse than missing ones** — if you
> change the fleet, update this file in the same session, and bump the date above.
>
> **What the 2026-08-25 stamp covers.** Re-checked against disk this pass: every line count
> and every frontmatter model/tool grant in the roster below; the presence, root, branch
> and log of the fleet git repo; that `repos/` is still not a repo; the absence of
> `.gitattributes` and the value of `core.autocrlf`; the 5 registry app ids against the
> directories on disk; the absence of any import linter or CI config; the exact text at
> `builder.md:3`, `builder.md:31`, `_schema.json:20`, `_schema.json:23` and
> `verify-state.py:72`; and the staleness hook, by triggering it. **Not** re-checked this
> pass: the hook's `Write` path and its behaviour during slices `s1`–`s4`, and the six
> routing cases of the original pipe-test.

---

## Status: two runs, one of them executed, zero production use

Built 2026-08-25 in a single session. Two runs so far:

- `2026-08-25-refuge-freshness` against `huntstack` — deliberately parked at the human gate.
- `2026-08-25-fleet-hardening` against the fleet itself — approved and **executed**, five
  slices, one commit each except `s4` and `s5`, which took two apiece after a REJECT.
  Every slice was reviewed by a fresh `reviewer`, `s5` included.

**No agent in this fleet has written a line of product code yet.** Everything written so
far is fleet tooling operating on itself.

---

## What is live

| Thing | State | Path |
|---|---|---|
| Umbrella constitution | live | `graph_agents/CLAUDE.md` (74 ln) |
| Graph spec | live | `graph_agents/GRAPH.md` (215 ln) |
| Portfolio index | live, 5 apps, paths verified | `graph_agents/portfolio/registry.json` (120 ln) |
| Run-state schema | live | `graph_agents/.graph/runs/_schema.json` (28 ln) |
| Root memory shim | live, `@`-imports the constitution | `repos/CLAUDE.md` |
| `.claude` junction | live, verified same-dir | `repos/.claude` → `graph_agents/.claude` |
| 6 agent nodes | live; 4 of 6 have executed as registered agents | `.claude/agents/` |
| 2 skills | `feature-graph` exercised twice (198 ln); `new-app` still unused (65 ln) | `.claude/skills/` |
| Staleness hook | live, **observed firing** 2026-08-25 | `.claude/settings.json`, `.claude/hooks/flag-stale-state.py` |
| State verifier | live, advisory only — a check, not a gate | `graph_agents/.graph/verify-state.py` (125 ln) |
| Fleet git repo | live, root = `graph_agents/`, branch `master`, no remote | `graph_agents/.git` |

### Node roster (frontmatter verified)

| Node | Model | Tools | Lines | Has executed? |
|---|---|---|---|---|
| `scout` | haiku | Read, Glob, Grep, Bash, WebSearch, WebFetch | 39 | yes, 2 runs |
| `architect` | opus | Read, Glob, Grep, Bash | 70 | yes, 2 runs |
| `builder` | opus | Read, Write, Edit, Glob, Grep, Bash | 49 | yes, 5 slices |
| `reviewer` | opus | Read, Glob, Grep, Bash | 52 | yes, 7 reviews |
| `integrator` | opus | Read, Write, Edit, Glob, Grep, Bash | 40 | **no** |
| `ops` | opus | Read, Write, Edit, Glob, Grep, Bash | 43 | **no** |

Model tiers and tool grants were re-read from frontmatter this pass and are unchanged
since creation. Line counts grew where `2026-08-25-fleet-hardening` edited the file.
Execution counts are as of the end of run `2026-08-25-fleet-hardening`: 7 reviews over 5
slices, because `s4` and `s5` were each REJECTED once and re-reviewed by a second, fresh
`reviewer` — `s1`+`s2`+`s3` = 3, `s4` = 2, `s5` = 2. The run is closed, so unlike every
earlier count in this row, 7 is final rather than as-of-writing.

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

1. ~~The named agents have never run as registered entities.~~ **CLOSED 2026-08-25.**
   All six agent files are registered and spawnable, and `2026-08-25-fleet-hardening`
   executed `scout`, `architect`, `builder` (5 slices) and `reviewer` (5 reviews) as
   registered nodes launched from `repos/`. No frontmatter or discovery debugging was
   needed. What is still unvalidated is narrower and is gaps #2 and #3 below: two of the
   six nodes have still never run, and no diamond has ever been built.
2. **`integrator` and `ops` have never executed.** `builder` and `reviewer` now have —
   that half of this gap closed on 2026-08-25 — but the fan-**in** end of the diamond is
   untested, and so is `ops`. Both keys in this run's `state.json` are still unwritten,
   which is why `verify-state.py` exits 1 on them.
3. **No diamond has ever run.** Both runs resolved to `single-loop`, both correctly.
   Worktree isolation has therefore still never been exercised, and see the note under
   gap #8: on a target with no git repo it *cannot* be.
4. **`new-app` has never been used.** All 5 registry entries were back-filled from
   directories that already existed; all five directories are on disk beside
   `graph_agents/`. Re-checked this pass, unchanged.
5. **Nothing enforces the umbrella invariant.** "No cross-app imports" is prose in
   `CLAUDE.md`. No lint rule, no CI check, no test. Re-checked this pass: the only two
   Python files in the fleet are `flag-stale-state.py` and `verify-state.py`, and neither
   inspects imports; there is no CI config anywhere under `graph_agents/`. Deliberately
   left open by `2026-08-25-fleet-hardening` — it is about apps, not about the graph, and
   it needs its own run.
6. ~~The staleness hook has never actually fired.~~ **CLOSED — observed firing
   2026-08-25.** During slice `s5` of `2026-08-25-fleet-hardening`, every `Edit` to
   `GRAPH.md` and to `feature-graph/SKILL.md` returned the hook's `additionalContext`
   verbatim ("You just changed ... `CURRENT-STATE.md` is now STALE"). Edits to this file
   itself produced no hook output, which is the documented no-self-trigger branch. Two
   things are still *not* established: whether the hook fired during slices `s1`–`s4`
   (those builders ran in their own contexts and none of them recorded it either way),
   and whether it fires for `Write` as well as `Edit` — only the `Edit` path was
   exercised. The original six-case routing pipe-test that this gap used to rest on was
   not re-run this pass; it is superseded by the live observation, not confirmed by it.
7. **State-file writes are convention, not machinery — now partially checkable.**
   `graph_agents/.graph/verify-state.py` (added 2026-08-25) exits 0 only if a named key
   is present, non-empty, and not still the `_schema.json` placeholder, and
   `feature-graph` steps 2, 3, 5 and 6 call it. That is a real narrowing: a node that
   returns a summary without writing its key is now detectable. It is **not** closure.
   Seven things it does not check, verified against the code by `s4`'s second reviewer:
   (1) content correctness — `{"status": "done"}` alone passes; (2) key shape — a missing
   `branch` or `verdict` passes, since `_schema.json` is consulted for placeholder
   identity only, never structure; (3) *who* wrote a key — `state.json` records no
   authorship, so the never-rewrite-another-node's-key contract is invisible to it;
   (4) staleness — no timestamps, so a key left from a previous attempt passes;
   (5) numbers and booleans are non-empty by design, so a hand-written `{"gated": false}`
   passes; (6) partial placeholders — a key whose `status` is filled while `branch` is
   still template text passes; (7) it is advisory, not enforcing — nothing fires it
   automatically. The orchestrator still hand-writes every state update.
8. ~~`builder.md:3` promises isolation the fleet cannot always deliver.~~ **Closed**
   2026-08-25, direct edit (no graph run — five one-line fixes below the stop-rule
   threshold). Frontmatter now reads: "Isolated by a git worktree and run in parallel with
   sibling builders when the target is a git repo; otherwise sequential, single-loop
   only."
9. ~~`builder.md:31` contradicts how the fleet actually commits.~~ **Closed** 2026-08-25,
   same pass. Now: "Do not push or open a PR. In diamond mode commit only on your own
   worktree branch; in single-loop mode (no repo, or no isolation) commit directly."
10. ~~`_schema.json` under-describes what nodes actually write.~~ **Closed** 2026-08-25,
    same pass. `reviews.<slice>` gained `summary`; `builders.<slice>` gained
    `gate_results` and `deviation_from_approved_plan`, both marked optional.
11. ~~`verify-state.py:72` has one silent failure path.~~ **Closed** 2026-08-25, same
    pass. A non-dict `_schema.json` now prints a WARNING to stderr before degrading to
    the empty-check, matching the existing `OSError`/`ValueError` branch. Re-verified:
    `["a","b"]` as the template now produces the warning and still exits correctly.
12. ~~No `.gitattributes`, and `core.autocrlf` is `true` globally.~~ **Closed** 2026-08-25,
    same pass. `graph_agents/.gitattributes` added: `* text=auto eol=lf`.

---

## Runs

| Run | App | Shape | Status | Outcome |
|---|---|---|---|---|
| `2026-08-25-refuge-freshness` | huntstack | single-loop | **parked** at human gate | Plan complete, unapproved, no code written |
| `2026-08-25-fleet-hardening` | umbrella (the fleet itself) | single-loop, 5 slices | **executed**, approved at the gate | Fleet got a git repo, a state contract in all 6 nodes, an owner for `branch`, `verify-state.py`, and this snapshot corrected |

Parked run detail: `graph_agents/.graph/runs/2026-08-25-refuge-freshness/state.json`
Executed run detail: `graph_agents/.graph/runs/2026-08-25-fleet-hardening/state.json`

### `2026-08-25-fleet-hardening` — what happened

Goal: improve the agent graph architecture and the subagents in it. The `scout` found the
blocker that shaped the whole run — `feature-graph` required `isolation: "worktree"` for
parallel builders, and neither `repos/` nor `graph_agents/` was a git repo, so the diamond
was unexecutable against the fleet. The `architect` refused to fan out on two independent
grounds (file overlap and no isolation/no rollback) and answered the isolation problem
with `git init` inside `graph_agents/` only, plus honest degraded-mode docs. A
snapshot-copy substitute for worktrees was considered and rejected. The human gate held.

Five sequential slices, each built then reviewed by a fresh `reviewer` — `s4` and `s5`
were each REJECTED once and re-reviewed: `s1` git repo and rollback · `s2` the state
contract in every node · `s3` an owner for the `branch` field · `s4` `verify-state.py` ·
`s5` this file, `GRAPH.md` and `feature-graph`.

**`s4` was REJECTED on its first attempt and is the run's most useful result.** The
reviewer reproduced `feature-graph` step 1 exactly — `cp _schema.json` into a new run
directory — and found all four newly wired verification call sites exited 0 on a run where
no node had been spawned, because every placeholder in the template is a non-empty
descriptive string. The new check was green in precisely the situation it existed to
catch. Attempt 2 added placeholder-identity detection and passed. A check that lies is
worse than no check; an independent reviewer caught it and the builder did not.

**Deviation from the approved plan, recorded not absorbed.** `s2`'s approved file set was
three files (`architect.md`, `reviewer.md`, `ops.md`). The orchestrator extended it
mid-slice to five, adding `scout.md` and `integrator.md`, because the approved gate —
`grep -l state.json .claude/agents/*.md | wc -l` == 6 — was unsatisfiable from the
approved set. The ruling was to make the files honest rather than weaken the gate. The
extension was strictly wording: no node's behaviour, responsibilities, model tier or
`Return` block changed. Full detail in `builders.s2.deviation_from_approved_plan`.

**One recorded fact in `2026-08-25-fleet-hardening`'s own `state.json` is wrong, and is
corrected here rather than copied forward.** The scout's fact 6 credited `scout.md:15`
and `integrator.md:21` with mentioning `state.json`; they carried the contract in words
but not the literal token.
Before `s2`, exactly **one** agent file contained the string `state.json` — `builder.md`.
That error is what made `s2`'s gate unsatisfiable as approved.

**`s5` was verified by a human reading it, not by a command.** The architect said so
explicitly instead of inventing a check, and the user agreed to be that check. The
machine-checkable parts of `s5` are greps for presence; the accuracy of the gap list above
is not machine-checkable and never was.

**`s5` was itself REJECTED on its first attempt, and the reason is worth keeping.** Its
first attempt added the `2026-08-25-fleet-hardening` heading above but left the
refuge-freshness narrative below it untouched, so that heading captured the other run's
paragraphs: this file briefly claimed that *this* run refused to fan out a 2-slice
sequence, held its gate with `git status` clean on huntstack, found two failed huntstack
scraper runs, and was watching a huntstack roadmap "late Aug" re-scrape window — all four
claims false of this run, one of them contradicting the run's own "not touching anything
outside `graph_agents/`". No grep could catch it, because every sentence was individually
well-formed and had been accurate about a different run.
A heading inserted above existing prose changes what that prose refers to. Both runs now
have their own heading and the passages name their run instead of saying "that run".

### `2026-08-25-refuge-freshness` — what happened

What `2026-08-25-refuge-freshness` proved: routing through the index worked; `scout`
returned `file:line` facts; `architect` correctly refused to fan out a 2-slice sequence;
the human gate held with `git status` clean on huntstack. Every claim in this subsection
is about `2026-08-25-refuge-freshness` and about huntstack — not about the fleet.

What `2026-08-25-refuge-freshness` found in huntstack, independent of the feature —
**both still open**:
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
| 2026-08-25 | No repo, no diamond — check `git -C <target> rev-parse --is-inside-work-tree` before choosing a shape | A worktree requires a repo. Without one there is no isolation and no rollback, so a fan-out is builders overwriting each other with no way back. Degraded mode is documented, not papered over |
| 2026-08-25 | Runs that edit `.claude/agents/**` or `.claude/skills/**` are always `single-loop`, and the next fleet run needs a fresh session | You are rewriting the definitions you spawn from, and registration happens at session start |
| 2026-08-25 | The **builder** writes its own `builders.<slice>` key, including `branch` — empty string when the target has no repo | The field existed in the schema with no owner. Whoever does the work knows the branch |
| 2026-08-25 | `verify-state.py` is advisory — a check the orchestrator runs, not a gate that fires itself | Making it blocking would need a hook, and its seven blind spots mean a green result must not be read as "the state is correct" |

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
| 2026-08-25 | Run `fleet-hardening` s1: `git init` in `graph_agents/` + `.gitignore`; branch `master`, no remote. Rollback exists for the first time |
| 2026-08-25 | s2: state contract added to `architect`, `reviewer`, `ops` — then extended by ruling to `scout` and `integrator`. All 6 nodes now share one idiom |
| 2026-08-25 | s3: `branch` field given an owner (the builder); `_schema.json` `$comment` and `builders.s1.branch` say so; `builder.md` step 4 matches |
| 2026-08-25 | s4: added `.graph/verify-state.py` and wired it into `feature-graph` steps 2/3/5/6. REJECTED on attempt 1 for passing on an untouched template; fixed with placeholder-identity detection |
| 2026-08-25 | s5: degraded-mode rule (`no repo, no diamond`) written into `feature-graph` step 0.5 + step 5 and into `GRAPH.md`; `verify-state.py` documented with all seven blind spots; this file's gap list re-verified against disk — gaps #1 and #6 closed, #7 narrowed, #8–#12 newly booked |
| 2026-08-25 | s5 REJECTED on attempt 1: its new run heading captured the refuge-freshness narrative below it, making four huntstack claims read as claims about this run. Re-anchored under a per-run heading on attempt 2 |
| 2026-08-25 | Run close: reviewer count corrected to 7 (`s5`'s own second reviewer included) and scoped to the closed run; the four captured huntstack claims now all named |
| 2026-08-25 | Direct fix (no graph run — below the stop-rule threshold): closed gaps #8–#12. `builder.md` frontmatter and step 31 made honest about degraded mode; `_schema.json` gained `summary`, `gate_results`, `deviation_from_approved_plan`; `verify-state.py:72` now warns on a non-dict template instead of failing silently; added `.gitattributes` |
