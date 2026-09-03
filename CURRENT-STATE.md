# CURRENT-STATE — graph_agents

> **Last verified: 2026-09-03**
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
> **Second 2026-08-26 pass** (direct edit, no graph run — one hook plus one script mode is
> below the stop-rule threshold): `verify-state.py --audit` and `flag-state-gap.py`, both
> driven through 12 synthetic cases, plus every line count in the tables below re-measured
> with `wc -l`. That pass also read all four run `state.json` files through the new audit,
> which is how gap #7's `fleet-hardening` finding surfaced. A **third** 2026-08-26 pass
> added `written_by` authorship: 6 more fixtures (healthy, orchestrator-forged builder key,
> builder-stamped review, partly unstamped, legacy unstamped, template text left in), all
> 10 earlier fixtures re-run as regressions, both CLI modes re-proven against all four real
> runs, and every roster line count re-measured again. A **fourth** pass added
> `.graph/CURRENT` and the plan-scope guard, driven through 12 synthetic cases covering
> both what it blocks and the seven conditions under which it must stay silent, plus the
> `scope_exceptions` audit rule in three states. A **fifth** pass added the node heartbeat
> and FleetView's activity lane, verified end-to-end against a live server rather than by
> fixture alone, and corrected the "no remote" claim in the git-repo row below. A **sixth**
> pass ran `new-app` for `personal-archive` (gap #4) — the registry is now 7 apps, and
> `verify-invariant.py` was re-run clean across all 7. Verified directly for that pass: the
> new repo's `git log` and tracked file list, its 6 tests passing, its CLI's three
> subcommands run by hand, and the verbatim no-sibling-import line matched with `grep -Fxq`.
> A **seventh** pass ran `archive-adapters`, the first diamond. Verified directly for that pass:
> both fleet fixes driven through fixtures (14 payloads for the guard, 5 for the audit) with the
> must-still-fail cases tested BEFORE the must-now-pass case; all four prior runs re-audited and
> confirmed byte-identical; `personal-archive` `master` at `a5ebed4` with 32 tests green together;
> the roster line counts for the two changed files re-measured. Not re-checked: everything else in
> the roster, unchanged since the sixth pass.
>
> **What the 2026-09-03 stamp covers** (direct edit, no graph run). Verified directly:
> `brief.py` rendered against **all 8 runs on disk** — the diamond, the two runs carrying
> off-plan slices, the `parked` run whose builder keys are still untouched template, and the
> four runs with no `activity.jsonl` — plus a synthetic mid-flight fixture exercising the
> live lane, a `blocked` builder, a `REJECT`, and a slice not yet started; both glyph modes;
> and repo-relative path output from `repos/`. All six roster line counts re-measured with
> `wc -l` after the return-block rewrite, as were `GRAPH.md` and the `feature-graph` skill.
> Confirmed rather than assumed: `_schema.json` was left byte-identical on purpose, because
> `is_untouched()` compares string leaves and editing a template description would flip
> older runs' untouched keys to "written" — the 2026-08-26 regression, restated.
> A **second 2026-09-03 pass** added the board hook. Verified directly: the hooks
> reference read for what `SubagentStop` does with stdout and with `systemMessage` (quoted
> verbatim in gap #19, because this is the kind of ruling that gets re-proposed); all four
> `activity.jsonl` files re-counted for the stop-event anomaly behind gap #20 — 471 of 503
> stops unattributed, every one carrying an `agent_id` that never had a `SubagentStart`;
> `Agent` confirmed as the spawn tool name from the same logs, 31 occurrences, all in the
> main session. `show-board.py` driven through 24 cases as a subprocess, and
> `test_hooks_resolve.py` re-run over all **8** commands. **Not observed**: `systemMessage`
> actually rendering in the main tab — see gap #19.
> A **third 2026-09-03 pass** added `/close-run`. Verified directly: `close-run.py` run
> against **all 8 historical runs**, with `fleet-hardening`'s 8 blockers and
> `archive-adapters`' clean result both read out rather than assumed; `test_close_run.py`
> driven through 27 checks, each building a real `git init` repository with a real branch
> merged or not merged; the four line counts above re-measured with `wc -l`. **Not
> exercised**: no run has been closed through this skill — it has only been pointed at
> history.
> **Not** re-checked on any 2026-09-03 pass: the guard, the registry, the invariant checker
> and FleetView — untouched, and recorded below as their own passes found them.
>
> **Not** re-checked on 2026-08-26: `verify-state.py`'s four *named-key* exit paths, the portfolio
> `entry_docs` sweep, and FleetView — all three were verified 2026-08-26 by the audit that
> produced that pass's fixes, and are recorded below as that audit found them.

---

## Status: five runs, four of them executed; the first diamond has run

Built 2026-08-25 in a single session. Five runs so far:

- `2026-08-25-refuge-freshness` against `huntstack` — deliberately parked at the human gate.
- `2026-08-25-fleet-hardening` against the fleet itself — approved and **executed**, five
  slices, one commit each except `s4` and `s5`, which took two apiece after a REJECT.
  Every slice was reviewed by a fresh `reviewer`, `s5` included.
- `2026-08-25-transclusion-external-previews` against `App 1` — approved and
  **executed**, one slice, two attempts after a REJECT. **Merged to `main`.**
- `2026-08-26-invariant-check` against the fleet itself — approved and **executed**, one
  slice, PASS on attempt 1. Closed gap #5: the umbrella invariant is now checked, not just
  asserted in prose.
- `2026-08-26-archive-adapters` against `personal-archive` — approved and **executed**, and
  the **first diamond**: three concurrent builders in three linked worktrees, three
  independent reviewers, one integrator. `s2`/`s3` PASS on attempt 1; `s1` took three
  attempts and two REJECTs, both for real personal health data surviving redaction into a
  committed fixture. Merged to `master` (`a5ebed4`), 32 tests green together.

**The graph's fan-in earns its keep, and now there is evidence rather than a diagram.** The
diamond's integrator did not merely merge text: it settled a conflict that existed *only between
two independently-correct slices* — github swallowing a bad config while roam raised on one, each
blessed by its own reviewer, neither wrong alone. No single-loop run can manufacture that defect,
and no reviewer looking at one branch can see it.

**The review layer is load-bearing, and this run is the proof.** `s1-whoop` passed its own test
suite on every one of its three attempts — including the attempt that was committing a real heart
rate of the machine owner's into git. Both leaks were found by reviewers hand-walking every leaf
against the source, and both times the builder had already certified a "systematic" audit. A green
gate was never evidence for the property that mattered.

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
| Umbrella constitution | live | `graph_agents/CLAUDE.md` (95 ln) |
| Graph spec | live | `graph_agents/GRAPH.md` (328 ln) |
| Portfolio index | live, **5 nodes** — 2 products, 2 tools, 1 site — ids and `kind` verified 2026-08-31. **Narrowed from 8 to 4 on 2026-08-31**: `koenrane.xyz`, `personal-archive`, `thrml`, `whoop-med-tracker` removed at the owner's direction — those repos are personal, not part of the development umbrella going forward. Not deleted from disk, just deregistered; the fleet routes to none of them. **`telosrg-site` added same day** via `/new-app` — the org's public marketing site. Also gained `org`/`org_status`/`org_domain`/`org_domain_status`/`org_github`/`org_github_status` fields (2026-08-31): "Telos Research Group", working name not yet a formed legal entity; domain `telosrg.com` **purchased** 2026-08-31 (re-verified registered via RDAP against Verisign after the owner reported buying it); GitHub org **github.com/TelosRG registered** 2026-08-31 (re-verified via `api.github.com/orgs/TelosRG` after the owner reported creating it) | `graph_agents/portfolio/registry.json` (139 ln), **untracked on purpose** — see below |
| Run-state schema | live | `graph_agents/.graph/runs/_schema.json` (31 ln) |
| Root memory shim | live, `@`-imports the constitution | `repos/CLAUDE.md` |
| `.claude` junction | live, verified same-dir | `repos/.claude` → `graph_agents/.claude` |
| 6 agent nodes | live; **5 of 6** have executed as registered agents — `integrator` first ran 2026-08-26 (`archive-adapters`). **`ops` is the only node never executed** | `.claude/agents/` |
| 4 skills | `feature-graph` exercised 3× (347 ln); `new-app` **exercised three times** — `personal-archive` 2026-08-26, `roamex` 2026-08-28, `telosrg-site` 2026-08-31 (72 ln); `fleetview` exercised (56 ln); `close-run` **added 2026-09-03, not yet exercised by a real close** (84 ln) | `.claude/skills/` |
| Close checker | live, **added 2026-09-03**, exercised only against history. Answers whether a run may be closed: `--audit` clean, gate passed, every slice — off-plan included — built and `PASS`, and **the work proved present in git** rather than in `state.json`. That fourth check is the one nothing else in the fleet makes. Read-only like `verify-state.py`; on green it prints the close for the orchestrator to write. Re-run against all 8 historical runs: `archive-adapters` reports closeable under `--recheck`, `fleet-hardening` reports **8 blockers**, which is the correct answer about it. `--recheck` exists to audit an already-closed run | `graph_agents/.graph/close-run.py` (240 ln), `graph_agents/.graph/test_close_run.py` (204 ln), `.claude/skills/close-run/SKILL.md` |
| Scout fact collector | live, **added 2026-08-28**, not yet exercised by a real scout run. Verified by hand across all 8 apps: correct git/HEAD/dirty/identity, `--all` and `--json` modes, and the registry-vs-disk contradiction lines. Computes, never caches — a per-app fact *store* was designed and **rejected on evidence** the same day (see Decisions log) | `graph_agents/.graph/scout-facts.py` (250 ln), `scout.md` step 0 |
| Staleness hook | live, **observed firing** 2026-08-25; rewritten 2026-08-26 (junction paths, run-close, `.py`) — 20 synthetic payloads pass | `.claude/settings.json`, `.claude/hooks/flag-stale-state.py` (114 ln) |
| State verifier | live, **two modes**. Named-key mode: advisory, a check the orchestrator runs. `--audit` mode: fires from a hook, checks edge ordering. **Fixed 2026-08-26 (`4cbe78c`)** — it counted `_schema.json`'s example slice as real, so the fan-in check fired on *every* run reaching an integrator and no diamond could close green. 5 new fixtures + byte-identical output on all four prior runs | `graph_agents/.graph/verify-state.py` (420 ln) |
| Plan-scope guard | live. **Fixed 2026-08-26 (`46e0f25`) to be worktree-aware** — it resolved plan entries against `repos/`, so it denied *every* write by *every* builder in a diamond. **Fixed again 2026-09-02: it did not glob.** A plan entry of `<dir>/**` normalised with its literal `**` attached, and since no real file is equal to or prefixed by a path ending in `**`, it denied *every* write under an approved directory — it blocked 3 of 4 slices of `2026-09-01-huntstack-mobile`, whose file sets were exactly that. Trailing `**`/`*` segments are now reduced to the directory they stand for at parse time, residual wildcards fall through to `fnmatch`, and both match sites share one `_match()` so they cannot drift apart a third time. **Now has a real self-test** (14 cases, previously the 14 "synthetic cases" lived only in a builder's transcript). **Exercised for real** across 9 builder runs with zero false denials since. ⚠️ **Matcher is `Write\|Edit` only, so a Bash write bypasses it entirely** — see gap #13. **Now fails CLOSED (2026-09-02)**: `main()` wraps `decide()` and emits a deny naming the hook itself as broken, and `settings.json` no longer swallows errors — a crash blocks builders loudly instead of silently voiding the human gate (gap #17, closed). All seven hook commands are now cwd-independent via `${CLAUDE_PROJECT_DIR:-.}` and covered by `test_hooks_resolve.py` (gap #18, closed) | `.claude/settings.json`, `.claude/hooks/guard-builder-scope.py` (279 ln), `.claude/hooks/test_guard_builder_scope.py` (194 ln) |
| Run board | live, **added 2026-09-03**, not yet used by a real run. Renders one run's `state.json` + `activity.jsonl` as a ~10-line board: gate, goal, a line per node, a row per slice pairing build with verdict, and the in-flight lane. Authored by nothing — every value is derived, and the placeholder rules are imported from `verify-state.py` rather than restated, so "written" means the same to the board as to the audit. Verified against all 8 runs on disk (diamond, off-plan slices, an untouched template run, a `parked` run, runs with no heartbeat) plus a synthetic mid-flight fixture; ASCII fallback when the console encoding cannot take the glyphs | `graph_agents/.graph/brief.py` (392 ln), `feature-graph` § the board |
| Run board hook | live, **added 2026-09-03**, **not yet observed rendering**. A third `PostToolUse` entry, `matcher: "Agent"`, returning the board as `systemMessage` when a node returns. `Agent` is the orchestrator's spawn tool and completes exactly when a subagent finishes — confirmed from `activity.jsonl`, 31 occurrences, all main-session. Silent on every other tool, on `SubagentStop`, on a subagent caller, on a closed run and on no open run. Self-tested through 24 subprocess cases against a **copied** fleet in a temp dir rather than by borrowing the live `.graph/CURRENT`, which a concurrent session may be relying on. Whether `systemMessage` reaches the user is documented but **unobserved** — gap #19 | `.claude/settings.json`, `.claude/hooks/show-board.py` (107 ln), `.claude/hooks/test_show_board.py` (160 ln) |
| Node heartbeat | live — `SubagentStart`/`SubagentStop` + a `*`-matcher `PostToolUse` entry append one line per node event to `.graph/runs/<run>/activity.jsonl`. Verified: events recorded with agent/tool, main-session writes recorded as `orchestrator`, silent on a closed run and with no open run | `.claude/settings.json`, `.claude/hooks/record-activity.py` (101 ln) |
| Open-run pointer | live, untracked — written by `feature-graph` step 1, read by the scope guard. A pointer to a closed run is ignored | `graph_agents/.graph/CURRENT` |
| State-audit hook | live, third `PostToolUse` entry — fires `--audit` on every `Write`/`Edit` of a `state.json`, silent on `_schema.json`, on non-run files, and on a merely half-filled run. **Caught a real defect on first run** (see gap #7) | `.claude/settings.json`, `.claude/hooks/flag-state-gap.py` (125 ln) |
| Invariant checker | live, advisory only, **observed catching a violation** — clean across all 6 apps 2026-08-26, builder and reviewer each independently confirmed it flags synthetic cross-app imports and ignores `registry.json`/doc prose/`@huntstack/*` | `graph_agents/.graph/verify-invariant.py` |
| Cross-app-import hook | live, second `PostToolUse` entry alongside the staleness hook — fires on `Write`/`Edit` inside a registered app dir, reuses the checker's `check_file()` | `.claude/settings.json`, `.claude/hooks/flag-cross-app-import.py` |
| Fleet git repo | live, root = `graph_agents/`, branch `master`, **remote `origin` at `github.com/njcurtis3/graph_agents`** — added since the 2026-08-25 entry that said "no remote"; pushed 2026-08-26 | `graph_agents/.git` |
| FleetView | live, **exercised** 2026-08-26 (`/api/graph` → 200: 3 runs, 6 agents, 3 skills, portfolio). Gained an **activity lane** 2026-08-26 reading `activity.jsonl` — verified end-to-end against a live server on port 8791, including a deliberately torn line (counted and skipped) and the 4 runs with no heartbeat rendering no lane. `ed7b6c2`, 32 assertions, 0 failures. Not in this repo — standalone app, own git repo. Launched by `/fleetview` | `repos/fleetview/` |

**The registry is untracked, and a fresh clone is therefore broken until you rebuild it.**
`.gitignore` excludes `portfolio/registry.json` because its `path`/`entry_docs` fields name
real directories on disk, personal names among them. But `scout.md` step 1 and
`feature-graph` step 1 both make it the **mandatory first read**, so on a fresh clone
routing fails with no visible cause — the file is simply absent. `scout-facts.py` (step 0)
now fails first and more loudly, naming the file and the launch rule, but it is the same
missing file either way. Rebuild it before the
first run: it is a JSON array of 8 objects, each with `id`, `kind`
(`product` | `site` | `tool` | `vendor`), `path` (the sibling directory name), and
`entry_docs` (paths into that app, `CLAUDE.md` first). `.gitignore` used to point here for
this explanation and this explanation did not exist; both ends were fixed 2026-08-26.

### Node roster (frontmatter verified)

| Node | Model | Tools | Lines | Has executed? |
|---|---|---|---|---|
| `scout` | haiku | Read, Glob, Grep, Bash, WebSearch, WebFetch | 67 | yes, 2 runs |
| `architect` | opus | Read, Glob, Grep, Bash | 96 | yes, 2 runs |
| `builder` | opus | Read, Write, Edit, Glob, Grep, Bash | 75 | yes, 6 slices |
| `reviewer` | opus | Read, Glob, Grep, Bash | 79 | yes, 9 reviews |
| `integrator` | opus | Read, Write, Edit, Glob, Grep, Bash | 45 | **no** |
| `ops` | opus | Read, Write, Edit, Glob, Grep, Bash | 49 | **no** |

All six line counts moved on 2026-09-03 when every node's `## Return` block was
rewritten to the headline contract (`GRAPH.md` § 3, rule 3) — `scout` 41→67, `architect`
81→96, `builder` 55→67, `reviewer` 54→79, `integrator` 41→45, `ops` 43→49. The two that
grew least are the two gates: `architect` and `ops` kept their full blocks and gained only
the paragraph saying why they are exempt.

`builder` moved again the same day, 67→75: real runs (`2026-09-02-date-accuracy`) showed
builders writing multi-paragraph self-justification essays into `notes` — a field the
Return block already capped at one line — while `gate_results` stayed verbatim as
designed. Step 4 now spells out the `notes` cap inline next to where it's written, not
just in the Return block, and states explicitly that `gate_results` is the one field
allowed to be long.

Model tiers and tool grants were re-read from frontmatter this pass and are unchanged
since creation. Line counts were re-counted with `wc -l` on 2026-08-26 — three had drifted
(`GRAPH.md` 215→219, `verify-state.py` 125→129, `builder.md` 49→50) because the direct fix
that closed gaps #8–#12 edited those files without re-counting. `scout` and `architect` are
now 3 runs each. Re-counted again after the authorship pass, which added a `written_by`
line to all six node files: `scout` 39→41, `architect` 70→72, `builder` 50→51, `reviewer`
52→54, `integrator` 40→41, `ops` unchanged at 43.

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
2. **`ops` has never executed.** — *`integrator` half CLOSED 2026-08-26.* `integrator` ran for the
   first time in `2026-08-26-archive-adapters`, and it did real work rather than ceremonial work: it
   resolved a two-place merge conflict in `src/adapters/__init__.py` and then ruled a **semantic**
   cross-slice conflict that no reviewer could have seen — two slices had adopted opposite error
   policies for configured-but-wrong input, and each slice's own reviewer had ruled its slice
   correct. It also ran the one check no reviewer could: that no `REGISTRY` line was silently
   dropped in conflict resolution, since each reviewer only ever saw a branch carrying one line.
   **`ops` remains the single node this fleet has never run**, and by design: it sits behind its own
   human gate and is never invoked automatically at the end of a graph.
3. ~~No diamond has ever run.~~ **CLOSED 2026-08-26**, `2026-08-26-archive-adapters` against
   `personal-archive`: three slices, three builders concurrent in three linked worktrees, three
   independent reviewers, one integrator. **Worktree isolation is exercised at last** — zero
   collisions, zero guard denials, and the three branches merged with exactly the conflict the
   architect predicted in the one file every slice had to touch.
   The architect's fan-out test is now on the record as something that *passed* rather than
   something that refused: it did not rely on disjoint file sets, which run 3 correctly rejected as
   insufficient. It relied on each slice's test importing `src.adapters.<name>` **directly as a
   module**, never through `REGISTRY` — so every slice was green on its own branch against a tree
   where the other two adapters were absent files. It checked the one thing that could have
   falsified that (`test_contract.py:47` does not assert registry emptiness despite its name) rather
   than assuming it.
   **The decisive precondition was set a run earlier, not in this run**: `personal-archive`'s record
   contract was frozen at scaffold time, so the slices consumed a contract rather than each other.
   That is what made three producers genuinely independent, and it is the reusable lesson.
4. ~~`new-app` has never been used.~~ **CLOSED 2026-08-26.** Run directly, not through a
   graph run — the skill *is* the procedure, and it carries its own human gate at step 1, so
   wrapping it in `feature-graph` would have produced two gates for one decision. Created
   `personal-archive` (`tool`, python): own repo, own `CLAUDE.md` carrying the verbatim
   no-sibling-import line, registered in `registry.json`, initial commit `272dd54` on
   `master`, no remote. The gate was answered explicitly, including the question the skill
   exists to force — why this is not a feature of `whoop-med-tracker` — and one environment
   finding the skill does not anticipate: **`uv` is not installed**, so "scaffold with the
   ecosystem's own tool" had no tool to reach for. Resolved by the human choosing to match
   the sibling Python convention (`requirements.txt` + `src/` + `tests/` + `pytest.ini`)
   rather than introduce packaging the portfolio does not otherwise use. That decision is
   recorded here because the skill will hit it again on the next Python app.
   The previous 6 registry entries remain back-filled from directories that already existed;
   this is the first entry the skill itself produced. Scaffold is 14 files, 6 tests passing,
   CLI smoke-tested; **no service adapters yet** — that is deliberate, see gaps #2 and #3.
   (Earlier passes of this file said "5" apps — the count was stale, not the check.)
5. ~~Nothing enforces the umbrella invariant.~~ **CLOSED 2026-08-26**, run
   `2026-08-26-invariant-check`, single slice, PASS on attempt 1. `graph_agents/.graph/verify-invariant.py`
   walks every registered app's source and flags import syntax whose target is a relative
   path (`./`/`../`) that resolves into a different app or into `graph_agents/` itself —
   bare specifiers (like huntstack's `@huntstack/*` workspace imports) are names, not
   paths, so they cannot match by construction, and only import-shaped lines are read, so
   `registry.json`'s own `path` fields and doc prose naming apps are invisible to it.
   **Re-run 2026-08-26** after `personal-archive` was registered: clean across 7 targets.
   `graph_agents/.claude/hooks/flag-cross-app-import.py` runs the same check live on every
   `Write`/`Edit`, registered as a second `PostToolUse` entry in `settings.json` alongside
   the staleness hook. Clean across all 6 apps today (fleetview 2, huntstack 121,
   App 1 233, podcraft-ai 26, thrml 25, whoop-med-tracker 6 source files — reviewer
   confirmed none silently skipped); both builder and reviewer independently wrote and
   deleted synthetic cross-app-import fixtures and confirmed it catches them with correct
   `file:line`, including `graph_agents/` itself as a forbidden target, and stays silent on
   `registry.json`, doc prose, and real `@huntstack/*` imports. Advisory only, like
   `verify-state.py` — it is a check, not a gate, and nothing forces it to run outside this
   session's hook. Reviewer logged four low-severity, non-blocking scope notes: `SOURCE_EXT`
   doesn't cover `.mts`/`.cts`/`.pyi` (no such files exist in any app today); the Python
   `sys.path` rule only matches a literal `./`/`../` string, not a computed path; non-import
   edges (a `package.json` `file:` dependency, a `tsconfig` `paths` alias, a build script
   shelling out to a sibling app) are out of scope — grepped for and none exist today, but
   the checker proves less than the invariant's full wording ("import, build against, or
   **read files from**"); and `builders.s1.changed` under-lists one file (the run's own
   `state.json`, not app code). None reopen the gap; all are documented narrowness, not
   live misses.
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
7. **State-file writes were convention, not machinery — ordering and authorship are now
   enforced; content is not.**
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

   **Update 2026-08-26 — ordering is now machinery; content still is not.**
   `verify-state.py` gained a second mode, `--audit <run-id>`, and
   `graph_agents/.claude/hooks/flag-state-gap.py` fires it as a third `PostToolUse` entry
   on every `Write`/`Edit` of any `state.json`, subagent writes included. The named-key
   mode could never be hook-fired for a structural reason worth recording: it must be told
   *which* key to check, and a hook sees only a file path. `--audit` asks the question a
   lone state file can answer instead — **did the edges hold?** It reports builders written
   while `approved_by_human` is false, a review with no build behind it, an `integrator`
   over a slice that is `REJECT` or unreviewed, `ops.actions` with no approval, a run
   closed `done` with a slice unbuilt or not `PASS`, and template strings left inside an
   otherwise-written key. That last one closes blind spot (6) above; the hook closes (7).

   **Update 2026-08-26, same day, second pass — blind spot (3), authorship, is closed
   too.** `_schema.json` gained a `written_by` field on all six node keys, each node's
   `.md` now tells it to stamp its own, and `--audit` maps key → owning node
   (`builders.*` → `builder`, `reviews.*` → `reviewer`, and so on) and rejects any other
   name. The two forgeries that matter are now detected by name: `builders.s1` stamped
   `orchestrator`, and `reviews.s1` stamped `builder` — a builder reviewing itself, which
   `GRAPH.md` calls a fake edge and which nothing could previously see. This also
   constrains the orchestrator directly: filling a node's key in itself now fails the
   audit whether it stamps honestly (`orchestrator` is not the owner) or dishonestly
   (that is forgery). **Runs opened before this are not retro-fitted** — all four report
   exactly one line saying the run carries no authorship at all, which is true and is the
   point; back-dating stamps would manufacture evidence.

   **(1), (2), (4) and (5) remain open** — content correctness, key shape, staleness, and
   the numbers/booleans exemption. A node writing confident nonsense into its own key, on
   schedule, under its own name, still passes both modes.

   One regression was found and fixed during this pass, and it is the general hazard of
   placeholder-identity checking: adding `written_by` to `_schema.json` meant every older
   run's *untouched* `integrator` key stopped being byte-identical to the template, so
   both modes began treating it as written — `--audit` then complained about the template
   text inside it, and the named-key mode started **passing** `integrator` on all four
   runs, contradicting gap #2 above. Whole-value equality was replaced with
   `is_untouched()`, which looks for evidence of writing (a string leaf differing from
   the template, a key the template lacks, content in a list the template left empty)
   rather than exact identity. Re-verified after the fix: `integrator ops` exits 1 on all
   four runs, a fresh copy of the template fails all 6 keys, and run 4's four written
   keys still pass.

   Verified by 12 synthetic cases: 8 hook payloads (non-run file, `_schema.json`, clean
   run, violating run, `Write`-shape `tool_response.filePath`, gate-skip fixture,
   unparseable state file, missing path — the first three silent, the rest firing
   correctly) and 4 audit fixtures (leftover placeholder, fan-in over a `REJECT`, a
   `done` run with a planned slice never built, and a healthy `done` run that must stay
   clean). Deliberately silent mid-run: a half-filled state file is what work in progress
   looks like, and a hook that complained at every intermediate write would be disabled
   inside a day.

   **It caught a real defect on its first run, in this fleet's own history.**
   `2026-08-25-fleet-hardening` is `status: done` and its `log` says "5/5 slices PASS",
   but on disk `reviews.s4` and `reviews.s5` still record attempt 1's `REJECT`, and
   `builders.closing_fix` — a sixth slice, not in the architect's plan — has no reviewer
   key at all. The attempt-2 PASSes CURRENT-STATE.md has been reporting since 2026-08-25
   were never written into state by anyone. The historical run files are left **as they
   are**: they are a record, and rewriting another node's key to make an audit green is
   the precise failure the contract exists to prevent. `feature-graph`'s orchestrator
   rules now require `--audit` to exit 0 before `status: done` is written.
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
13. **The plan-scope guard covers `Write`/`Edit` only, so a Bash write bypasses it entirely.**
    `settings.json` registers the `PreToolUse` matcher as `Write|Edit`, and every `builder` has
    `Bash`. A builder writing through `sed`, a heredoc or `python -c` never reaches the hook: no
    denial, no record, no trace. The approved file set is presented to a human at the step-4 gate as
    a permission boundary; it is a boundary on **two write paths out of several**. **Raised by a
    builder itself, unprompted** — `s1-whoop` reported that it had deliberately kept using `Edit`
    *because* a Bash edit would have evaded the guard silently. That is simultaneously the best
    evidence the fleet's norms hold and the clearest statement that the machinery does not. Open;
    it is the most serious gap on this list.
14. **`--audit` parses the untouched `scope_exceptions` placeholder as a file path.**
    `approved_paths()` skips prose with a heuristic — a space and no separator — and the
    `_schema.json` placeholder contains `/` (in "Write/Edit"), so it slips through, becomes a bogus
    allowed path, and pollutes the `Approved:` list a denied builder is shown. Matches no real file,
    so it opens nothing. Worked around in `archive-adapters` by setting that run's
    `scope_exceptions` to `[]`; the general fix — a placeholder-aware filter — is **not** done.
15. **The staleness hook fires on app files edited inside a builder worktree.**
    Reported twice by `s1-whoop`: every fixture edit under `personal-archive`'s worktree returned
    "you changed the agent architecture's definition, `CURRENT-STATE.md` is now STALE". Nothing
    about the fleet changed. The worktrees live under `graph_agents/.graph/worktrees/` only because
    `repos/` is not a repo, and the hook matches on that prefix. Same path-matching class as the
    guard bug closed in `46e0f25`. Noise rather than damage — but it trains agents to ignore a hook
    that exists to be heeded, which is how a real staleness warning gets missed later.
16. **A green test suite is not evidence that `fixtures/whoop/` is redacted, and never was.**
    Carried forward verbatim from the third `s1-whoop` reviewer and re-stated by the integrator,
    because it is the single most load-bearing thing this run learned. `test_fixture_is_redacted`
    checks three rules; small integer leaves under `score` fall outside all three. **The suite was
    green through all three attempts, including the attempt that was committing a real heart rate.**
    Two builder self-certifications of a "systematic" audit were both wrong, and both were caught
    only by a reviewer hand-walking the tree. Any future edit under `fixtures/whoop/` needs a human
    leaf-walk, not a test run. This is a permanent property of that fixture, not a defect to close.

17. ~~**The plan-scope guard fails open, and a crash is indistinguishable from "no opinion."**~~
    **Closed 2026-09-02**, owner-directed, the same day it was found. `main()` now wraps `decide()`
    and emits a deny that names this file as broken; `settings.json` no longer wraps the call in
    `2>/dev/null || true`. The documented silences stay allows. One allow-on-failure remains by
    design: a malformed payload carries no `agent_type`, so the deny could not be scoped to builders
    and would block every agent in the session. Fail-closed is safe here precisely because the guard
    already fires for builders only -- the orchestrator and every other node are exempt, so a broken
    guard costs one loud, self-identifying denial rather than a silently voided human gate.
    Covered by 5 of the self-test's 19 cases, including a real fault injected into a real copy of
    the hook.

18. ~~**The other six hook commands are cwd-relative and fail silently when cwd is not `repos/`.**~~
    **Closed 2026-09-02**, owner-directed, same day it was found. All seven commands are now rooted at
    `"${CLAUDE_PROJECT_DIR:-.}/graph_agents/..."`, and the six advisory ones dropped `2>/dev/null`
    while KEEPING `|| true` -- they are `PostToolUse` and must never block a write, but there is no
    reason for their failures to be invisible. All four were confirmed silent on stderr when healthy
    first, so the change adds no noise. Demonstrated rather than asserted: from inside `graph_agents/`,
    the old form `python graph_agents/.claude/hooks/flag-stale-state.py 2>/dev/null || true` **exits 0,
    reporting success, while the interpreter never found the file** -- that is how a hook stays dead
    indefinitely with nothing to show for it. **How long the six were silently dead remains unknown and
    unmeasurable**; nothing recorded it, and that history cannot be recovered.
    Now covered by `test_hooks_resolve.py`, which parses the real commands out of `settings.json`
    (so a hook added later is covered without anyone remembering) and runs each from a non-root cwd.

19. **The headline contract is prose, nothing enforces it, and the board's delivery is
    documented but unobserved.** Booked 2026-09-03, narrowed the same day.
    **Still open, and the core of it:** every node's `## Return` says "three lines, hard cap" and
    *nothing checks it*. A node that returns its old six-line block with the full `done_when`
    transcript is not denied, not flagged, and not visible anywhere — `activity.jsonl` records
    that a node stopped, never what it said. Same shape as every rule this fleet has had to
    promote later: `--audit` was convention until `flag-state-gap.py` fired it, the approved file
    set was description until `guard-builder-scope.py` denied on it. A long return costs tokens
    and readability rather than correctness, which is why it stays un-machined.
    **Closed off, so it is not re-proposed: `SubagentStop` cannot address the human.** The hooks
    reference, read 2026-09-03: *"On display events like `Stop` and `SubagentStop`, stdout is
    added to Claude's context as a system message instead of being shown in the transcript, even
    if it doesn't parse as JSON."* The field that works elsewhere is exempted on the same events —
    `systemMessage` is *"A system message shown to Claude. On display events like `Stop` and
    `SubagentStop`, the message is added to Claude's context instead of being shown in the
    transcript."* Both routes reach the orchestrator, which already knows, and never the person
    reading the main tab. Gap #20 is the second, independent reason.
    **What replaced it:** `show-board.py`, a `PostToolUse` hook on `matcher: "Agent"` — a
    non-display event, where the docs say *"To surface a message to the user on any platform,
    return `systemMessage` in JSON output."*
    **What remains unverified:** that sentence sits next to a field description reading "shown to
    Claude", and the two do not obviously agree. Nobody has watched this hook render. It cannot be
    watched in the session that wrote it, because hooks are snapshotted at session start. **The
    test is one fresh session and any subagent spawn**: if a board appears in the main tab, the
    row above and this paragraph both get to say "observed"; if it does not, the hook is inert and
    the orchestrator printing `brief.py` by hand (`feature-graph` § the board) remains the whole
    mechanism — which is why that rule was written to stand on its own.
    And the honest statement about all of it: **no run has yet executed under any of this.**

20. **`activity.jsonl` is polluted with `SubagentStop` events that are not node stops.**
    Booked 2026-09-03. Across the four runs carrying a heartbeat, **471 of 503 `stop` events
    arrive with no `agent_type`** and are recorded as `orchestrator` by `record-activity.py`'s
    documented fallback. They are not the main session stopping: each carries a **unique
    `agent_id` that never had a matching `SubagentStart`** (102/102, 3/3, 233/233, 133/133 across
    the four runs), and they interleave with a still-running node's own tool calls — one fires
    mid-scout, between two of its Greps. Whatever they are, they are not "a subagent finished".
    This matters because `activity.jsonl` was built to be the evidence base for four claims
    (`GRAPH.md` § the heartbeat), and two of them — node durations for model tiering, and
    reviewer independence proven by a fresh `agent_id` — read `start`/`stop` pairs. A 15:1 ratio
    of phantom stops to real ones does not corrupt `brief.py` (it counts lanes, and these lanes
    carry a single event and the `orchestrator` name) but it would mislead anyone measuring from
    the raw file. Not yet diagnosed: whether Claude Code is delivering a different event under
    this name, or the fleet is misreading the payload.

---

## Runs

| Run | App | Shape | Status | Outcome |
|---|---|---|---|---|
| `2026-08-25-refuge-freshness` | huntstack | single-loop | **parked** at human gate | Plan complete, unapproved, no code written |
| `2026-08-25-fleet-hardening` | umbrella (the fleet itself) | single-loop, 5 slices | **executed**, approved at the gate — but its **state file is an incomplete record**: see gap #7 | Fleet got a git repo, a state contract in all 6 nodes, an owner for `branch`, `verify-state.py`, and this snapshot corrected. `reviews.s4`/`s5` still hold attempt 1's `REJECT` and `builders.closing_fix` was never reviewed; found 2026-08-26 by the new state audit, left unedited on purpose |
| `2026-08-25-transclusion-external-previews` | App 1 | single-loop, 1 slice | **executed**, approved at the gate | First product code by this fleet. External-link popovers no longer surface browser frame-block errors. Merged to `main` as `79c3c32` |
| `2026-08-26-archive-adapters` | `personal-archive` | **diamond, 3 slices** | **executed**, approved at the gate. s2/s3 PASS on attempt 1; **s1 took 3 attempts, two REJECTs, both real data leaks** | The fleet's **first diamond**. Three concurrent worktree builders, three independent reviewers, one integrator that resolved both a textual and a **semantic** cross-slice conflict. Merged to `master` (`a5ebed4`), 32 tests green together. Closed gap #3 and the `integrator` half of #2; found gaps #13–#16 and fixed two fleet defects (`46e0f25`, `4cbe78c`) |
| `2026-08-26-invariant-check` | umbrella (the fleet itself) | single-loop, 1 slice | **executed**, approved at the gate, PASS on attempt 1 | Closed gap #5: `verify-invariant.py` + `flag-cross-app-import.py` make the umbrella invariant a live, automated check instead of prose. Committed directly to `graph_agents` `master` (`ae97640`) — no branch, nothing to merge |

Run state lives at `graph_agents/.graph/runs/<run-id>/state.json` for each of the four.

### `2026-08-26-archive-adapters` — what happened

Goal: three service adapters for `personal-archive` — whoop, github, roam — each
fixture-driven and independently testable. Shape: **diamond**, the fleet's first.

**What it proved.** Worktree isolation works: three builders wrote concurrently in three linked
worktrees with zero collisions and zero guard denials. The architect's independence test held —
each slice's test imports `src.adapters.<name>` directly rather than through `REGISTRY`, so every
slice was green on its own branch against a tree where the siblings were absent files.

**What only a diamond could produce.** The integrator's real work was not the merge text. Two
slices had adopted **opposite error policies** for configured-but-wrong input — github swallowed a
404 and archived nothing forever, roam raised — and *each slice's own reviewer had ruled its slice
correct*, because each saw exactly one branch. The incoherence existed only in the space between
two independently-correct slices. The integrator ruled (configured-but-wrong raises; absent config
stays skipped) on two arguments it could only make on the merged tree: whoop already used
`raise_for_status`, so github was the sole outlier and "swallow" would have meant inventing
behaviour at the seam; and under swallow, `cli._write` still writes an empty ndjson
indistinguishable from a genuinely quiet week.

**What the review layer caught.** `s1-whoop` was REJECTED twice, both times for real personal
health data surviving redaction into a committed fixture — first a real `max_heart_rate`, then two
sleep-need values whose zeros the builder had argued were "absence, not measurement" (they are
model outputs; zero is a value). Both were invisible to the test and found only by a reviewer
hand-walking every leaf against the source. The builder eventually diagnosed its own root cause
better than either reviewer had: its audit script contained a literal `isinstance(value, bool):
continue`, so its judgement was compiled into the tool it was certifying with. Attempt 3 required
it to **paste the enumeration rather than certify the audit**, and a third fresh reviewer
independently confirmed the numbers.

**Human decisions.** Readwise dropped (token-only) and replaced with Roam at the human's choice;
Roam scoped to a graph export file rather than its token-gated API; both fixtures redacted under an
explicit privacy ruling; the 2-attempt ceiling overridden once, explicitly, for `s1` attempt 3.

**Two fleet defects fixed mid-run, both blocking.** `46e0f25` made the plan-scope guard
worktree-aware — it had denied every builder write in a diamond, undetected since the day it was
written. `4cbe78c` stopped `--audit` counting `_schema.json`'s example slice as real, which had
made a green close impossible for *any* run reaching an integrator. Neither was fixed by weakening
a check: both were driven through fixtures where the cases that must still fail were tested first.

### `2026-08-26-invariant-check` — what happened

Goal: close gap #5 — nothing enforced "no app may import, build against, or read files
from another app," it was prose in `CLAUDE.md`. App: umbrella (the fleet itself). Approved
at the gate, one slice, **PASS on attempt 1**.

The `scout` surfaced the risk that shaped the design: a naive check would false-positive on
`registry.json`'s own `path`/`entry_docs` fields (which legitimately name every app), on doc
prose in `CLAUDE.md`/`GRAPH.md` naming apps in examples, and on huntstack's internal
`@huntstack/*` pnpm-workspace imports, which look like they cross a boundary but don't — all
three live inside huntstack's own repo. The `architect`'s answer: only parse actual
import/require *syntax*, and only match a target that is a **relative path** (`./` or
`../`). Bare specifiers like `@huntstack/db` are names, not paths, so they cannot match by
construction — no allowlist needed. Free text in JSON values or comments never reaches the
import-syntax parser at all.

Two files, one slice: `graph_agents/.graph/verify-invariant.py` (the checker, advisory,
mirrors `verify-state.py`'s style) and `graph_agents/.claude/hooks/flag-cross-app-import.py`
(a second `PostToolUse` entry alongside the staleness hook, so a violation surfaces at the
moment of the `Write`/`Edit`, not just when someone remembers to run the script). The hook
imports the checker's `check_file()` rather than duplicating the rule — one definition of a
violation, not two that can drift apart.

**Both builder and reviewer independently wrote synthetic cross-app-import fixtures, ran the
checker against them, and deleted them** — nothing was left behind or committed in any app
repo (`git -C whoop-med-tracker status --short` confirmed empty by both). The reviewer did
not reuse the builder's fixtures; it wrote its own nested TS/Python set (import-from,
export-from, `require()`, dynamic `import()`, side-effect import, a `repos/`-round-trip
path) and confirmed all of it caught with correct `file:line`, `graph_agents/` included as a
forbidden target, while `@huntstack/*` and same-app relative imports stayed silent. It also
instrumented the walk to confirm all 6 apps were actually scanned (not silently skipped) and
grepped all 6 apps for non-import edges (`package.json` `file:` deps, `tsconfig` `paths`
aliases) to confirm the clean verdict wasn't hiding a live violation the checker can't see.

**The reviewer logged four low-severity findings, none of which reopened the gap**:
`SOURCE_EXT` doesn't cover `.mts`/`.cts`/`.pyi` (no such files exist in any app today); the
Python `sys.path` rule matches only a literal `./`/`../` string, not a computed path built
from `os.path.join`; non-import edges are structurally out of scope, which means the checker
proves less than the invariant's full wording ("import, build against, or **read files
from**"); and `builders.s1.changed` under-listed the run's own `state.json` among the
commit's files. All four are documented narrowness, verified against the real trees to be
non-live today, not misses the checker was supposed to catch and didn't.

Single-loop, no branch — the builder committed directly to `graph_agents`' `master`
(`ae97640`), so step 5's merge was a no-op. `integrator` and `ops` were not exercised, same
as every prior run.

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
| 2026-09-03 | **The close is checked by a script, and written by the orchestrator — never both by one actor** | `close-run.py` follows `verify-state.py`'s contract exactly: it decides and prints, it does not write. A script that set `status: done` and appended the closing `log` entry itself would be doing to the orchestrator's keys what `written_by` was added to stop a node doing to another's. The check is mechanical; the close is an act with an author |
| 2026-09-03 | **A merge is proved against git, never against `state.json`** | The first three close checks read the state file, and a state file cannot know whether a merge happened — a run whose slices all say PASS and whose branch never landed passes every existing check and is not done. So each slice's branch, or its recorded commit for a branch since deleted, must be an ancestor of the target's HEAD. Degraded shapes (no repo, direct commit, no branch) are notes, not blockers, because `feature-graph` step 0.5 describes them as legitimate |
| 2026-09-03 | **The board is delivered from `PostToolUse`/`Agent`, never from `SubagentStop`** | `SubagentStop` is a *display event*: the docs put both its stdout and its `systemMessage` into Claude's context "instead of being shown in the transcript", so a board emitted there reaches the orchestrator — which already knows — and never the human. The fleet's own heartbeat gives the second reason: 471 of 503 stop events are phantoms (gap #20), so the event is not even a reliable "a node finished" signal here. `Agent` `PostToolUse` is both: non-display, so `systemMessage` surfaces, and exactly one per node return |
| 2026-09-03 | **The return text is the human channel; `state.json` is the machine channel. Nodes return headlines, and the board is derived, never authored** | `GRAPH.md` § 3 already said a subagent returns only its final text and that the orchestrator alone sees it — so the return had no machine consumer and never did. Writing it as if it were the handoff printed the machine channel into the main tab, and a run then read as several thousand words nothing downstream consumed. The board is derived from files the fleet already writes for exactly the reason `--audit` exists: a summary a node authors is a summary a node can be wrong about, and one no node authors cannot drift, cannot be forged, and costs no tokens |
| 2026-09-03 | **`architect` and `ops` are exempt from the headline cap** | Their returns are not status, they are the two human gates. A gate is a decision, and nobody can approve a plan or a deploy they have not been shown — compressing those two blocks would save a screen and cost the only two moments in the graph where a human's judgment is load-bearing |
| 2026-08-26 | The staleness hook flags **history** drift as well as definition drift, but only at `status: "done"` | A closed run is what falsified this file's headline claim. Firing on every mid-run write would restore the noise the original `.graph/runs/**` skip existed to prevent; firing once at close costs nothing and catches the only run event that changes what is true |
| 2026-08-26 | The hook resolves paths with `os.path.realpath()` before routing | `repos/.claude` is a junction, so fleet files have two absolute paths — and `GRAPH.md` §2 documents the one that did *not* contain `/graph_agents/`. A textual guard was silent on the documented path |
| 2026-08-26 | **The hook fires `--audit`, not the named-key check** — and it stays silent mid-run | The named-key mode is unhookable by construction: it must be told which key to inspect, and a `PostToolUse` hook knows only a file path, never which node just returned. So the hook asks the question a lone `state.json` *can* answer — did the edges hold? Reporting merely-unwritten keys mid-run was rejected outright: that is what a run in progress looks like, and a hook that fires on every intermediate write gets disabled, after which it enforces nothing. This supersedes the 2026-08-25 "advisory, not a gate" decision for **ordering only**; content correctness is still unchecked and deliberately so |
| 2026-08-26 | **An overseer *agent* was considered and rejected; the overseer *function* is hooks** | An agent cannot watch other agents here: subagents are spawned, run, return text and end — there is no loop for one to observe from, no channel between siblings, and a node consuming nothing and producing nothing is precisely the fake edge `GRAPH.md` says to delete. The hook layer already runs concurrently with every node and, per the current Claude Code hook reference, receives `agent_id`/`agent_type` on every tool event plus `SubagentStart`/`SubagentStop`. So oversight is built where it can actually see: `PreToolUse` for enforcement, `PostToolUse`/`Subagent*` for live status |
| 2026-08-26 | **The scope guard blocks on the UNION of all slices' files, not the acting slice's** | A hook is handed `agent_id`, never a slice id, and nothing maps one to the other. In `single-loop` — every run this fleet has executed — the union *is* the one slice, so the guard is exact; in a diamond, worktrees already isolate builders from each other, so what the union still buys is the plan boundary. Blocking on a guess at the slice would deny correct work |
| 2026-08-26 | **The guard denies rather than warns, but stays silent on seven conditions** | A warning after the write is a record of the violation, not a guard against it, and `PreToolUse` is the only place in this fleet a rule can stop something. It is silent for non-builders, with no open run, on a closed run, on an unapproved run (that is `--audit`'s finding; denying there would deadlock a run whose approval merely was not recorded), when the plan lists no files, when `files` still reads as prose, and for the run's own `state.json` — which every node is required to write |
| 2026-08-26 | **Authorship is stamped by the node itself, and pre-2026-08-26 runs are not retro-fitted** — they report one line saying they carry no stamps | `written_by` is self-reported, so it stops an honest orchestrator taking a shortcut, not a determined liar; that is still the whole gap, because the failure mode here is convenience, not malice. Back-filling stamps onto the four existing runs would manufacture evidence about who wrote keys nobody recorded — and one of those runs (`fleet-hardening`) is already known to misreport itself. One line per legacy run, not one per key, so the runs that have *specific* violations stay readable |
| 2026-08-26 | `fleet-hardening`'s stale `reviews.s4`/`s5` keys are **left as they are** | The audit found a closed run whose state contradicts its own log. Editing those keys to make the audit green would be the orchestrator writing a reviewer's key — the exact contract violation the state file exists to prevent — and would destroy the evidence that the fleet ran for a day with an unverified close. The record stands; the gap list carries the finding |
| 2026-08-28 | **Scout memory is a collector, not a cache — a per-app fact store was designed and rejected** | Past scout keys were checked against reality before building: `"graph_agents/ is NOT a git repository"` (2026-08-25) had become false, and `"6 app directories"` (2026-08-26) had become eight. Scouts do repeat work, but the facts they repeat most are the ones that rot fastest — and one of them, git-repo status, decides graph shape via § "No repo, no diamond". A cache would have served a confident wrong answer to the one question that must not be wrong; a stale `false` forces an unnecessary single-loop, a stale `true` fans builders out with no isolation. The facts are also one `git rev-parse` cheap, so caching them saves nothing worth the risk. `scout-facts.py` stores nothing and therefore cannot go stale |
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
| 2026-08-26 | `GRAPH.md` §4 footnote corrected — it was the last copy of gap #8, closed in `c4f075c`, still describing `builder.md` as dishonest |
| 2026-08-26 | `.gitignore` now explains the untracked-registry consequence and points at a section that exists; `.claude/scheduled_tasks.lock` ignored. This file gained the rebuild note |
| 2026-08-26 | Constitution and root `CLAUDE.md`: prose cross-references named as allowed with a mechanical test; "standalone product" → "standalone node", since `fleetview` is a tool and `thrml` a vendor drop |
| 2026-08-26 | Roster line counts re-measured — `GRAPH.md` 215→219, `verify-state.py` 125→129, `builder.md` 49→50 had drifted; registry count corrected 5→6 |
| 2026-08-26 | Run `invariant-check` against the fleet itself: `verify-invariant.py` + `flag-cross-app-import.py` close gap #5. PASS on attempt 1, committed directly to `graph_agents` `master` as `ae97640` |
| 2026-08-26 | Direct fix (below the stop-rule threshold): `verify-state.py --audit` + `flag-state-gap.py` make the graph's **edge ordering** enforced instead of advisory. Gap #7 blind spots (6) and (7) closed, (1)–(5) explicitly still open. The audit's first run found `fleet-hardening`'s state file contradicting its own log |
| 2026-08-26 | Node heartbeat: `record-activity.py` logs `SubagentStart`/`SubagentStop`/`PostToolUse` to `activity.jsonl`, and FleetView (`ed7b6c2`, separate repo) renders it as a live lane. This is the **overseer** idea, built where it can actually see — an overseer *agent* was rejected as unimplementable and as a fake edge |
| 2026-08-26 | `.graph/CURRENT` (untracked pointer to the open run) + `guard-builder-scope.py`: the fleet's **first blocking hook**. A `builder`'s `Write`/`Edit` outside `architect.plan[].files` is now DENIED, making the human gate's file set a permission grant. Escape hatch is `scope_exceptions`, which `--audit` flags when unexplained |
| 2026-08-26 | **History rewritten in both repos to remove Claude commit attribution**, per a standing user rule this session had been violating. `graph_agents`: 13 commits stripped of `Co-Authored-By`/`Claude-Session` trailers, force-pushed. `personal-archive`: 6 commits stripped, and 4 commits re-authored — one was authored by `Claude <noreply@anthropic.com>` and three by `builder <nathanjcurtis3@gmail.com>`, none of which is the owner. **All commits in both repos are now authored solely by the owner.** Every commit hash in this file was remapped and re-verified reachable |
| 2026-08-26 | **First diamond.** Run `archive-adapters` against `personal-archive`: 3 concurrent worktree builders, 3 independent reviewers, 1 integrator. Merged `a5ebed4`, 32 tests green together. Closes gap #3 and the `integrator` half of #2 — `ops` is now the only node never executed |
| 2026-08-26 | `46e0f25` — plan-scope guard made worktree-aware. It resolved plan entries against `repos/`, so it denied EVERY builder write in a diamond; undetected since written because the guard had never fired and worktrees had never run. 14 synthetic payloads |
| 2026-08-26 | `4cbe78c` — `--audit` stopped counting `_schema.json`'s example slice as real. The fan-in check fired on every run reaching an integrator, so no diamond could close green. 5 fixtures; all four prior runs byte-identical |
| 2026-08-26 | Gaps #13–#16 booked from the diamond: the guard's `Write\|Edit`-only matcher (a Bash write bypasses it — **raised by a builder that declined to use it**), the `scope_exceptions` placeholder parsed as a path, the staleness hook firing on app files in worktrees, and the standing rule that a green suite never evidences whoop fixture redaction |
| 2026-08-26 | `/new-app` exercised for the first time (gap #4): `personal-archive`, own repo, initial commit `272dd54`, registered as the 7th app. Gate surfaced an unanticipated environment case — no `uv` — resolved by matching the sibling Python convention. Scaffolded deliberately as a **diamond vehicle**: contract frozen up front, `src/adapters/__init__.py` the single expected merge point. Gaps #2 and #3 stay open until a run uses it |
| 2026-08-26 | Authorship: `written_by` on all six node keys in `_schema.json`, stamped by each node, checked by `--audit` against an owner map. Gap #7 blind spot (3) closed — a `builders.*` key stamped `orchestrator`, or a `reviews.*` key stamped `builder`, now fails. Placeholder detection rewritten as `is_untouched()` after the new field broke whole-value template identity on older runs |
| 2026-08-28 | `/new-app` exercised a second time: `roamex` (Roam export → provenance-tracked knowledge graph), own repo, 2 commits, pushed to `github.com/njcurtis3/roamex`, registered as the 8th node |
| 2026-08-28 | `scout-facts.py` added and wired into `scout.md` step 0, `feature-graph` step 0.5 and `GRAPH.md` § model tiering. Computes git/HEAD/dirty/identity, registry entry, entry-doc existence and observed-vs-claimed stack, fresh every run. Verified by hand on all 8 apps; **not yet exercised by a real scout**. The cache alternative was rejected on measured staleness — see Decisions log |
| 2026-08-28 | Token-cost review of `archive-adapters` (the first diamond): the shape heuristic itself was sound — 3 genuinely disjoint slices earned the diamond — but every slice got the same full adversarial reviewer regardless of risk, and that adversarial depth is what caught the leaked WHOOP measurement. Added risk tagging: `architect` now tags each slice `risk: high\|low` with a stated reason; `feature-graph` step 5 briefs the reviewer accordingly — full re-derivation for `high`, a lighter re-run-`done_when`-plus-scope-check for `low`, with a reviewer free to re-tag a slice `high` mid-review if it doubts the call. Not yet exercised by a run |
| 2026-08-31 | Direct edit (single line, below the stop-rule threshold): `conventions/mobile-first.md` reviewer checklist gained a note to watch for a recurring pattern of missed mobile issues as the trigger for building a specialized mobile reviewer variant — anticipatory, no examples yet, so no new agent was built |
| 2026-08-31 | Direct edit, owner-directed: `registry.json` narrowed 8 → 4 apps. `koenrane.xyz`, `personal-archive`, `thrml`, `whoop-med-tracker` deregistered as personal repos, not part of the development umbrella going forward. Repos untouched on disk; the fleet simply no longer routes to them |
| 2026-08-31 | Direct edit, owner-directed: umbrella given a working entity name, **Telos Research Group** (not yet formed). Recorded in `repos/CLAUDE.md`, `graph_agents/CLAUDE.md`, and `registry.json` (`org`/`org_status` fields) — one source of truth, not re-decided each time it comes up |
| 2026-08-31 | Direct edit, owner-directed: domain `telosrg.com` and GitHub name `telosrg` chosen (checked via RDAP against Verisign and GitHub's API, both confirmed available, neither purchased/registered yet). Recorded alongside the entity name in `repos/CLAUDE.md`, `graph_agents/CLAUDE.md`, and `registry.json` (`org_domain`/`org_github`/`org_domain_github_status`) |
| 2026-08-31 | `telosrg.com` marked **purchased** — owner reported buying it, re-verified independently via RDAP (now shows `objectClassName: domain`, was 404/unregistered earlier the same day). `org_domain_status` updated in `registry.json`; `repos/CLAUDE.md` and `graph_agents/CLAUDE.md` updated to say purchased. `org_github` split into its own `org_github_status` field, still unregistered |
| 2026-08-31 | GitHub org **github.com/TelosRG** marked **registered** — owner reported creating it, re-verified independently via `api.github.com/orgs/TelosRG` (returns `type: Organization`). `org_github`/`org_github_status` updated in `registry.json`; both `CLAUDE.md` files updated. All three of entity name, domain and GitHub org are now settled; only the legal LLC formation remains open |
| 2026-08-31 | `/new-app` exercised a third time: `telosrg-site`, own repo, initial commit `17a57b9`, registered as the 5th app (`kind: site`). The public marketing page for Telos Research Group — a hand-written card grid (no build step, no framework) linking out to each portfolio app's GitHub repo. Color palette taken from the TelosRG org avatar (a black-background swirling rainbow-eye mark, teal/cyan iris), deliberately restrained to black base + teal primary + a teal-to-violet gradient accent rather than a literal rainbow. Card list is hand-maintained, not generated from `registry.json` — kept that way deliberately so the site never depends on the fleet's tooling |
| 2026-08-31 | `telosrg-site` **pushed and deployed**, owner-directed. Repo created under the `TelosRG` org via the GitHub API (local branch renamed `master`→`main` to match the org repo's default), pushed as `github.com/TelosRG/telosrg-site` — push authored as `njcurtis3` per the GitHub API's `pusher` field (confirmed, not assumed) even though the repo lives in the org's namespace, not the personal one. GitHub Pages enabled via API, serving `main` at root; confirmed live at https://telosrg.github.io/telosrg-site/ by fetching it directly, not by trusting the "building" status. `registry.json` gained `repo`/`deployed_url` on the `telosrg-site` entry |
| 2026-09-02 | **Plan-scope guard fixed a second time: it did not glob.** `approved_paths()` normalised a `<dir>/**` plan entry with the literal `**` still attached, and `covered()` was a pure prefix test, so no real file could ever match — it denied *every* write under an approved directory. It blocked 3 of 4 slices of `2026-09-01-huntstack-mobile` (whose file sets were exactly `huntstack/apps/mobile/**`) and cost that run a round trip plus a `scope_exceptions` entry granting nothing the human had not already approved. Trailing `**`/`*` segments now reduce to the directory they stand for at parse time; residual wildcards (`a/**/*.ts`) fall through to `fnmatch`; and the absolute rule and the worktree rule now share one `_match()` — they had already drifted apart once (the 2026-08-26 diamond bug), and a matcher in two places disagrees with itself. Added `test_guard_builder_scope.py`, the fleet's first hook test: 14 cases driving the hook as a subprocess through real stdin payloads. Verified the fix against the pre-fix version rather than only asserting the new one — same payload, old hook `DENIED`, new hook `allowed`. Also **found and did not fix** that the guard fails open (gap #17): `|| true` plus a blanket `except` make a crash indistinguishable from "no opinion", so a typo silently disables the human gate rather than blocking on it. Left for the owner to rule on. |
| 2026-09-02 | **Scope guard now fails closed, and its command is cwd-independent.** Owner-directed, same day as the glob fix. `main()` wraps `decide()` and emits a deny that names the hook itself as broken; `settings.json` drops `2>/dev/null || true`. Before this, a syntax error in the guard did not block builders — it silently stopped guarding them, voiding the human gate for a whole run with no trace. Fail-closed is safe here because the guard already fires for builders only, so the cost is one loud self-identifying denial rather than a deadlock. A malformed payload stays an allow by design: with no `agent_type` the deny could not be scoped to builders. Removing `|| true` immediately exposed a second, older bug (gap #18): every hook command is cwd-relative, so from inside `graph_agents/` the path resolves to `graph_agents/graph_agents/...` and the script is not found — the guard's command is now `"${CLAUDE_PROJECT_DIR:-.}/graph_agents/..."`, proven by an `Edit` that failed from that cwd before the change and succeeded after. The other six hooks keep `|| true` and are untouched, so the same breakage stays silent there. Self-test grew 14 → 19 cases, including a real fault injected into a real copy of the hook. |
| 2026-09-03 | **`/close-run` — the fourth skill, and the first router built for a failure this fleet already had.** `feature-graph`'s "run `--audit` before you set `status: done`" was a rule placed at the moment attention is lowest, and `2026-08-25-fleet-hardening` is what that costs: closed with a log reading "5/5 slices PASS" while two reviews still recorded REJECT and `builders.closing_fix` had no reviewer, undetected for a day. `close-run.py` is that rule with a script behind it — audit clean, gate passed, every slice including off-plan ones built and PASSed, and **the work proved present in git**, which no reading of `state.json` can establish. Read-only, like every checker here; the orchestrator still writes `status` and the closing `log` entry itself. `--recheck` audits an already-closed run. Verified against all 8 historical runs and by `test_close_run.py`, 27 checks that build a **real git repo per case** — a stubbed git would have tested everything except the one check that matters. The test caught four defects in the first cut: the merge loop ran on unbuilt slices, a branch equal to the target branch was reported as proof of its own merge (`fleet-hardening` recorded `branch: master` and "proved" six merges that way), a deregistered app made a historical run unverifiable (`personal-archive` left the registry on 2026-08-31 and its repo still holds `archive-adapters`' merges), and piped stdout was block-buffered so evidence printed after the blockers citing it. |
| 2026-09-03 | **The board now prints itself.** Added `.claude/hooks/show-board.py`, a third `PostToolUse` entry on `matcher: "Agent"` that returns `brief.py`'s output as `systemMessage` when a node returns — so the board is machinery rather than orchestrator discipline, the same promotion `--audit` got from `flag-state-gap.py`. **`SubagentStop`, the obvious event, was ruled out on evidence** and the ruling is recorded in gap #19 with the docs quoted verbatim: it is a display event, and both its stdout and its `systemMessage` go to Claude's context "instead of being shown in the transcript". The fleet's own logs supplied a second reason, now gap #20 — 471 of 503 `stop` events are phantoms carrying an `agent_id` that never started, interleaved with running nodes. `Agent` was confirmed as the spawn tool from those same logs (31 occurrences, all main-session). Added `test_show_board.py`: 24 subprocess cases, run against a **copied** fleet in a temp directory rather than borrowing the live `.graph/CURRENT` the way the older hook tests do — that pointer is how the scope guard finds its run, and a concurrent session was live. The test caught a real defect immediately: `brief.py`'s `detail` line was **cwd-relative**, so the same run rendered differently depending on who printed it; it now resolves against the umbrella root per the launch rule. **Not observed**: that `systemMessage` actually reaches the main tab — hooks are snapshotted at session start, so it takes a fresh session to see. |
| 2026-09-03 | **The two-channel split: nodes return headlines, and `brief.py` renders the board.** Direct edit, owner-directed, no graph run (six node files, one skill, one spec, one new script — but it edits `.claude/agents/**` and `.claude/skills/**`, which `feature-graph` step 0.5 forces to single-loop anyway, and the change is one design ruling applied six times). `GRAPH.md` § 3 rule 3 now caps every node's return at a headline: no verbatim command output, no file lists, no findings bodies, because the next node reads `state.json` and nothing but the main tab reads the return. `scout`, `builder`, `reviewer` and `integrator` rewritten to fixed 3-line blocks; `architect` and `ops` keep their full blocks as the two gates, and now say why. The content those blocks stopped carrying is not lost but it was optional: `builders.<slice>.gate_results` and `reviews.<slice>.summary` are **required** as of this pass — `_schema.json` still calls both optional and was deliberately left byte-identical, because changing a template string flips old runs' untouched keys to "written" and breaks `--audit` on them (the exact regression `is_untouched()` was written for on 2026-08-26). Added `.graph/brief.py`, which renders a run as ~10 derived lines and is what the orchestrator now prints between nodes instead of relaying or re-narrating node text. Verified across all 8 runs on disk plus a synthetic mid-flight fixture. **Booked gap #19**: the cap is prose, nothing enforces it, and no run has executed under it yet. |
| 2026-09-02 | **All seven hook commands made cwd-independent; six stopped swallowing their errors.** Owner-directed follow-on to gap #18. Every command is now rooted at `"${CLAUDE_PROJECT_DIR:-.}/graph_agents/..."`; the six advisory `PostToolUse` hooks dropped `2>/dev/null` but KEPT `|| true`, since they must never block a write but have no business failing invisibly — all four scripts were verified silent on stderr when healthy first, so this adds no noise. The old form was shown to `exit 0` — reporting success — from inside `graph_agents/` while the interpreter never found the script, which is how six hooks could sit dead indefinitely; how long they actually were is unknown and unrecoverable. Added `test_hooks_resolve.py`, which parses the real commands out of `settings.json` rather than hardcoding them and runs each from a non-root cwd. It initially reported all 7 failing — that was the harness, not the hooks: `subprocess.run(shell=True)` on Windows is cmd.exe, which passes `${VAR:-default}` through literally; fixed to invoke a POSIX shell explicitly. |
| 2026-09-03 | **`builder.md` step 4 now spells out the `notes` one-line cap inline, not just in the Return block.** User-directed, prompted by FleetView being unreadable: real runs (`2026-09-02-date-accuracy`, all four slices) showed builders writing multi-paragraph self-justification prose into `notes` — narrating which tool they used, defending compliance with hooks, restating scope — instead of the one out-of-scope item the Return block already specified. `gate_results` was separately confirmed working as designed (verbatim evidence, per `_schema.json`); step 4 now says so explicitly so a builder doesn't over-correct and start summarizing it. `builder.md` 67→75 lines. No graph run — direct edit, single node file. FleetView side of the same complaint (progressive disclosure for `gate_results`) tracked as a separate `fleetview`-repo task, per the umbrella scope rule. |
