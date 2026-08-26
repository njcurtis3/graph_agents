# CURRENT-STATE — graph_agents

> **Last verified: 2026-08-26**
>
> A point-in-time snapshot **verified against disk**, not a living spec. `GRAPH.md` and
> `CLAUDE.md` describe how the fleet is *supposed* to work; this file records what is
> *actually true right now*. **Stale entries here are worse than missing ones** — if you
> change the fleet, update this file in the same session, and bump the date above.
>
> **What the 2026-08-26 stamp covers.** Re-checked against disk this pass: every line count
> and every frontmatter model/tool grant in the roster below; the 6 registry app ids **and
> their `kind` values** against the directories on disk; run 3's `state.json` end to end;
> the four `App 1` commits it claims, including the merge commit, read out of that
> repo's `git log`; `builder.md:3` against the `GRAPH.md` §4 footnote that described it;
> and the staleness hook, by running 20 synthetic payloads through it (both `tool_input`
> and `tool_response` shapes, junction and canonical paths, closed and parked runs).
> **Not** re-checked this pass: `verify-state.py`'s four exit paths, the portfolio
> `entry_docs` sweep, and FleetView — all three were verified 2026-08-26 by the audit that
> produced this pass's fixes, and are recorded below as that audit found them.

---

## Status: three runs, two of them executed, first product code shipped

Built 2026-08-25 in a single session. Three runs so far:

- `2026-08-25-refuge-freshness` against `huntstack` — deliberately parked at the human gate.
- `2026-08-25-fleet-hardening` against the fleet itself — approved and **executed**, five
  slices, one commit each except `s4` and `s5`, which took two apiece after a REJECT.
  Every slice was reviewed by a fresh `reviewer`, `s5` included.
- `2026-08-25-transclusion-external-previews` against `App 1` — approved and
  **executed**, one slice, two attempts after a REJECT. **Merged to `main`.**

**The fleet has now written product code.** Run 3's builder wrote
`quartz/plugins/transformers/linkpreviews.ts` plus 12 tests in a real app repo, an
independent reviewer REJECTED attempt 1 on a genuine parser bug, and the fixed work landed
on `App 1` `main` as `9fa35d7` → `f74b13e` → `6c7cdc2`, merged as `79c3c32`. All
four verified in that repo's `git log` this pass.

This is the claim this file got most wrong: until 2026-08-26 it still said "**no agent in
this fleet has written a line of product code yet**", eleven hours after one had. See
§ How this file stays current for why the machinery could not catch that.

---

## What is live

| Thing | State | Path |
|---|---|---|
| Umbrella constitution | live | `graph_agents/CLAUDE.md` (78 ln) |
| Graph spec | live | `graph_agents/GRAPH.md` (219 ln) |
| Portfolio index | live, 6 nodes — 3 products/sites, 2 tools, 1 vendor drop — ids and `kind` verified | `graph_agents/portfolio/registry.json` (139 ln), **untracked on purpose** — see below |
| Run-state schema | live | `graph_agents/.graph/runs/_schema.json` (28 ln) |
| Root memory shim | live, `@`-imports the constitution | `repos/CLAUDE.md` |
| `.claude` junction | live, verified same-dir | `repos/.claude` → `graph_agents/.claude` |
| 6 agent nodes | live; 4 of 6 have executed as registered agents | `.claude/agents/` |
| 3 skills | `feature-graph` exercised 3× (220 ln); `new-app` still unused (72 ln); `fleetview` exercised (56 ln) | `.claude/skills/` |
| Staleness hook | live, **observed firing** 2026-08-25; rewritten 2026-08-26 (junction paths, run-close, `.py`) — 20 synthetic payloads pass | `.claude/settings.json`, `.claude/hooks/flag-stale-state.py` (114 ln) |
| State verifier | live, advisory only — a check, not a gate. All four exit paths re-proven 2026-08-26 | `graph_agents/.graph/verify-state.py` (129 ln) |
| Fleet git repo | live, root = `graph_agents/`, branch `master`, no remote | `graph_agents/.git` |
| FleetView | live, **exercised** 2026-08-26 (`/api/graph` → 200: 3 runs, 6 agents, 3 skills, portfolio). Not in this repo — standalone app, own git repo. Launched by `/fleetview` | `repos/fleetview/` |

**The registry is untracked, and a fresh clone is therefore broken until you rebuild it.**
`.gitignore` excludes `portfolio/registry.json` because its `path`/`entry_docs` fields name
real directories on disk, personal names among them. But `scout.md` step 1 and
`feature-graph` step 1 both make it the **mandatory first read**, so on a fresh clone
routing fails with no visible cause — the file is simply absent. Rebuild it before the
first run: it is a JSON array of 6 objects, each with `id`, `kind`
(`product` | `site` | `tool` | `vendor`), `path` (the sibling directory name), and
`entry_docs` (paths into that app, `CLAUDE.md` first). `.gitignore` used to point here for
this explanation and this explanation did not exist; both ends were fixed 2026-08-26.

### Node roster (frontmatter verified)

| Node | Model | Tools | Lines | Has executed? |
|---|---|---|---|---|
| `scout` | haiku | Read, Glob, Grep, Bash, WebSearch, WebFetch | 39 | yes, 2 runs |
| `architect` | opus | Read, Glob, Grep, Bash | 70 | yes, 2 runs |
| `builder` | opus | Read, Write, Edit, Glob, Grep, Bash | 50 | yes, 6 slices |
| `reviewer` | opus | Read, Glob, Grep, Bash | 52 | yes, 9 reviews |
| `integrator` | opus | Read, Write, Edit, Glob, Grep, Bash | 40 | **no** |
| `ops` | opus | Read, Write, Edit, Glob, Grep, Bash | 43 | **no** |

Model tiers and tool grants were re-read from frontmatter this pass and are unchanged
since creation. Line counts were re-counted with `wc -l` on 2026-08-26 — three had drifted
(`GRAPH.md` 215→219, `verify-state.py` 125→129, `builder.md` 49→50) because the direct fix
that closed gaps #8–#12 edited those files without re-counting. `scout` and `architect` are
now 3 runs each.

Execution counts run through the end of run `2026-08-25-transclusion-external-previews`:
**6 builder slices** (5 in fleet-hardening + 1 in run 3) and **9 reviews** — fleet-hardening
contributed 7 over 5 slices (`s4` and `s5` each REJECTED once and re-reviewed by a second,
fresh `reviewer`), run 3 contributed 2 over 1 slice (REJECTED once, re-reviewed fresh).
Both runs are closed, so these are final rather than as-of-writing.

Tiering rationale: `GRAPH.md` § Model tiering. Short version — spend on judgment, not
retrieval. `reviewer` and `architect` are never-downgrade.

---

## How this file stays current

A `PostToolUse` hook on `Write|Edit` runs `.claude/hooks/flag-stale-state.py`. When a
fleet **definition** file changes (`.md`/`.json` under `graph_agents/`) it injects context
telling Claude this snapshot is stale and must be re-verified before the turn ends.

It fires for: agent files, skills, `GRAPH.md`, `CLAUDE.md`, `registry.json`, `_schema.json`,
and the fleet's `.py` files. It stays silent for: this file itself (no self-trigger), and
everything outside `graph_agents/`.

**It now flags two kinds of drift, because this file went false in the second kind and
nobody noticed for eleven hours.** Rewritten 2026-08-26:

| Drift | Trigger | Why |
|---|---|---|
| **definition** | a fleet `.md`/`.json`/`.py` changed | the graph is now *described* wrongly |
| **history** | a run's `state.json` reaches `status: "done"` | the graph *did something* the Status line, Runs table and Changelog do not know about |

The old hook skipped `.graph/runs/**` wholesale, on the reasoning that "run state churns and
is not an architecture change". That reasoning is right about mid-run writes and wrong about
the last one: a **closed run** is precisely the event that falsified "no agent in this fleet
has written a line of product code yet". It covered definition drift and nothing covered
history drift. The fix keeps the churn suppression — mid-run writes are still silent, only
`status: "done"` fires — so the noise argument still holds.

**A junction blind spot was closed in the same pass.** `repos/.claude` is a directory
junction, so every fleet definition file has two valid absolute paths, and the old guard
(`"/graph_agents/" not in norm`) saw the segment in only one of them:

```
...\repos\graph_agents\.claude\agents\builder.md   -> fired
...\repos\.claude\agents\builder.md                -> SILENT
```

`GRAPH.md` §2 tells agents the nodes are "reached as `.claude/agents/` from `repos/`" — the
documented path was the one that bypassed the hook. It now calls `os.path.realpath()` before
routing, which resolves the junction, and both paths fire. Verified with 20 synthetic
payloads across both `tool_input` and `tool_response` shapes (the latter is what `Write`
returns, which also closes the open half of gap #6).

**It still deliberately does not auto-stamp the date.** A bot bumping `Last verified:`
without re-checking anything would make this doc confidently wrong — the exact failure the
header warns about. The hook creates the obligation; a real verification pass discharges it.

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
   untested, and so is `ops`. Both keys are still the untouched template in **every** run
   on disk, run 3 included, which is why `verify-state.py` exits 1 on them. Correctly so:
   all three runs were `single-loop`, and under the 2026-08-26 merge ruling a single-loop
   run reaches `integrator` only when its merge conflicts. Run 3's did not. Closing this
   gap now needs either a real diamond or a conflicting merge — it will not close by
   accident.
3. **No diamond has ever run.** All three runs resolved to `single-loop`, all three
   correctly — run 3's architect refused to fan out because its three candidate slices were
   producer/consumer, not independent: `s2` consumed the exact `data-*` contract `s1` emitted
   and `s3`'s `done_when` needed both. Disjoint file sets are not sufficient for a diamond;
   independently checkable `done_when` is the real test, and that is now on the record twice.
   Worktree isolation has therefore still never been exercised, and see the note under
   gap #8: on a target with no git repo it *cannot* be.
4. **`new-app` has never been used.** All 6 registry entries were back-filled from
   directories that already existed; all six directories are on disk beside `graph_agents/`,
   and all six are git repos while `repos/` correctly is not. Re-checked this pass,
   unchanged. (Earlier passes of this file said "5" — the count was stale, not the check.)
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
   **Update 2026-08-26:** the `Write` half is now closed *in code* — the rewritten hook was
   driven with `tool_response.filePath` payloads, the shape `Write` returns, and routes them
   identically to `tool_input.file_path` on all 10 path cases. That is a synthetic payload,
   not a live `Write` from Claude Code, so it proves the branch works and not that the
   harness sends that shape. Whether the hook fired during `s1`–`s4` remains unknowable.
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
| `2026-08-25-transclusion-external-previews` | App 1 | single-loop, 1 slice | **executed**, approved at the gate | First product code by this fleet. External-link popovers no longer surface browser frame-block errors. Merged to `main` as `79c3c32` |

Run state lives at `graph_agents/.graph/runs/<run-id>/state.json` for each of the three.

### `2026-08-25-transclusion-external-previews` — what happened

Goal: stop external-link transclusion popovers from showing browser X-Frame-Options/CSP
block errors, and improve transclusions generally. App: `App 1`. Approved at the
gate, one slice, **two attempts**.

**The architect's central finding was that the obvious fix cannot work.** A cross-origin
iframe blocked by `X-Frame-Options` or CSP `frame-ancestors` still fires `load`, and its
`contentDocument`/`contentWindow.location` are unreadable cross-origin — so there is *no*
client-side signal distinguishing "blocked" from "loaded". No runtime timeout detects
blocking; a timeout only catches slow frames. The fix had to move to build time: a probe
records per-origin frameability, and the runtime **defaults to a metadata card**, attempting
an iframe only where the probe affirmatively proved framing is permitted. Missing, stale or
uncrawled data means card. Fail-safe, not fail-open.

It also ruled on an apparent contradiction in the app's own `CLAUDE.md`: line 34 calls
`quartz/plugins/` "stable and should not be changed", while lines 107–112 give step-by-step
instructions for adding a transformer there. The ruling was that line 34 targets pre-existing
upstream Quartz files, and the plan added a **new** file rather than editing `linkfavicons.ts`
— a mechanism valid under either reading, so the ambiguity never had to be resolved.

**Attempt 1 was REJECTED, and the finding was real.** The reviewer caught that
`parseFrameAncestors` split the CSP header on `;` before `,`, so a multi-policy value like
`default-src 'self', frame-ancestors 'none'` parsed to `null` — **fail-open**, marking a
site frameable that had explicitly forbidden framing. That is the exact bug class the whole
design was built to avoid, in the function the design rests on. Attempt 2 split on `,` into
policies first and intersects the source lists, matching browser semantics.

**The reviewer did not trust the builder's tests.** It wrote its own throwaway Jest suite
against the real module (9/9), and then live re-probed all 94 frameable origins through the
fixed `isFrameable` — finding 0 consistent false positives and 2 transient anti-bot flags
that cleared on re-probe. It also caught that the committed cache had been computed by the
*old* parser and would be served until the 30-day TTL elapsed; that gap was closed by hand
in `6c7cdc2`, which is why the run has three commits and not two.

**Nothing in `feature-graph` said who merged it.** The orchestrator did — step 5 ended at
"one builder, then one reviewer. Done" and step 6's fan-in was diamond-only, so the merge
was work no step assigned, in a skill whose rules open with "never implement anything
yourself." Ruled 2026-08-26 and written into the skill: see the Decisions log.

`integrator` and `ops` were **not** exercised — both keys in this run's `state.json` are
still the untouched template, which is correct for a single-loop run and is why gap #2
stays open.

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
A heading inserted above existing prose changes what that prose refers to. Every run has
its own heading and the passages name their run instead of saying "that run". Run 3's
heading was added 2026-08-26 directly above the `fleet-hardening` heading — adjacent to
another heading, capturing no prose — for the same reason.

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
| 2026-08-25 | FleetView is a standalone app in `repos/fleetview/`, not a directory in the fleet | A viewer is a product with its own lifecycle, not tooling that operates on apps. Keeping it here would have made the fleet ship a UI |
| 2026-08-25 | FleetView depends on the run-state **format**, never on a path into `graph_agents/` — fleet location is runtime config (`--fleet`, `$FLEETVIEW_FLEET`, then auto-detect) | `CLAUDE.md` says no app depends on the fleet. A hardcoded `../graph_agents` would be exactly that dependency. A convention may cross the boundary; an import may not — and the app must still run with no fleet present, which it does |
| 2026-08-26 | **In `single-loop`, the orchestrator merges the one reviewed branch itself; on conflict it stops and spawns `integrator`** — user ruling | The merge was previously unassigned work that the orchestrator did anyway, in a skill that says "never implement anything yourself." Merging already-reviewed work writes no code and makes no choice, so it is bookkeeping and belongs to the orchestrator. Resolving a conflict *is* a judgment call about code, so it stays with the node that owns merges. Cheaper than spawning `integrator` on every single-loop run |
| 2026-08-26 | The staleness hook flags **history** drift as well as definition drift, but only at `status: "done"` | A closed run is what falsified this file's headline claim. Firing on every mid-run write would restore the noise the original `.graph/runs/**` skip existed to prevent; firing once at close costs nothing and catches the only run event that changes what is true |
| 2026-08-26 | The hook resolves paths with `os.path.realpath()` before routing | `repos/.claude` is a junction, so fleet files have two absolute paths — and `GRAPH.md` §2 documents the one that did *not* contain `/graph_agents/`. A textual guard was silent on the documented path |
| 2026-08-26 | A prose cross-reference from an app to `graph_agents/` is **not** a forbidden edge; the test is whether deleting `graph_agents/` breaks the app's build, test or deploy | `new-app` mandates apps carry `see ../graph_agents/CLAUDE.md` verbatim, which read as a violation of "no app depends on the fleet". The distinction was real but unwritten, so the constitution now states it mechanically instead of leaving it to be re-litigated |

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
| 2026-08-25 | FleetView built (stdlib-Python read-only viewer for run graphs, roster, portfolio), first under `graph_agents/viz/`, then moved out to `repos/fleetview/` as a standalone app before any commit. Fleet keeps only the `/fleetview` skill that launches it |
| 2026-08-25 | Run close: reviewer count corrected to 7 (`s5`'s own second reviewer included) and scoped to the closed run; the four captured huntstack claims now all named |
| 2026-08-25 | Direct fix (no graph run — below the stop-rule threshold): closed gaps #8–#12. `builder.md` frontmatter and step 31 made honest about degraded mode; `_schema.json` gained `summary`, `gate_results`, `deviation_from_approved_plan`; `verify-state.py:72` now warns on a non-dict template instead of failing silently; added `.gitattributes` |
| 2026-08-25 | Run `transclusion-external-previews` against `App 1`: build-time frameability probe + metadata card replaces the always-iframe external popover. REJECTED on attempt 1 for a fail-open multi-policy CSP parse. **First product code written by this fleet**; merged `79c3c32` |
| 2026-08-26 | Fleet audit (no graph run — documentation and one hook, below the stop-rule threshold). Found this file materially false: it still claimed two runs and zero product code after run 3 had merged |
| 2026-08-26 | Staleness hook rewritten: `realpath()` closes the junction blind spot, run-close now flags **history** drift, `_schema.json` and `.py` files now flag definition drift. 20 synthetic payloads pass across both `tool_input` and `tool_response` shapes |
| 2026-08-26 | `feature-graph` step 5 gained the single-loop merge ruling; step 6 marked diamond-only; orchestrator rules now distinguish merging (yours) from conflict resolution (`integrator`'s) |
| 2026-08-26 | `GRAPH.md` §4 footnote corrected — it was the last copy of gap #8, closed in `6630dc1`, still describing `builder.md` as dishonest |
| 2026-08-26 | `.gitignore` now explains the untracked-registry consequence and points at a section that exists; `.claude/scheduled_tasks.lock` ignored. This file gained the rebuild note |
| 2026-08-26 | Constitution and root `CLAUDE.md`: prose cross-references named as allowed with a mechanical test; "standalone product" → "standalone node", since `fleetview` is a tool and `thrml` a vendor drop |
| 2026-08-26 | Roster line counts re-measured — `GRAPH.md` 215→219, `verify-state.py` 125→129, `builder.md` 49→50 had drifted; registry count corrected 5→6 |
