# HISTORY — graph_agents

> Split out of `CURRENT-STATE.md` on 2026-09-22. Nothing reads this file at runtime.

This is the fleet's **sediment**: the parts of the record that are finished. A closed
run's narrative never changes again, and a changelog row never changes again. They were
worth 31% of `CURRENT-STATE.md` by weight while answering no question that file exists to
answer — which is "is this still true?"

`CURRENT-STATE.md` keeps everything that describes the present and everything a machine
checks: the `What is live` table, the node roster, the Runs *table*, the gap list, the
Decisions log, and `Last verified:`. `audit-fleet.py` parses those and reports drift
against disk. It parses nothing here, and said so before the split — per-run "what
happened" prose was already out of its scope by construction. The split was verified by
claim count: **126 claims before, 126 after.**

**Where to write what.** A closed run gets its row in the `CURRENT-STATE.md` Runs table
*and* its narrative here. A definition change gets its Changelog row here and its updated
rows there. `flag-stale-state.py` names both files in its message for that reason, and is
silent when you edit this one — appending history is how the obligation is discharged, not
a new reason to be stale.

---

## Run narratives

Newest first. Each is inserted above the narrative it describes, never above another
run's prose.

### `2026-10-07-native-followups` — what happened

The owner asked to "fix the follow ups" left by `2026-10-07-native-app-expertise`. Single loop,
forced. The scout returned once without writing its key and was re-prompted. The architect
found three more literal `responsive-web` conditions than the brief named, approved at the gate.

s2 is the run's lesson. The plan said `base = norm(cwd)`; `norm()` strips trailing separators, so a
drive-root cwd (`/c/`, `C:\`) became the drive-relative `c:` and a relative target resolved
against the hook process's own cwd -- an approved-looking write allowed while the shell wrote
outside the umbrella. The suite passed; the reviewer found it by hand (5 spellings x 2 hook cwds).
Attempt 2 never normalises the cwd before the join and fails closed on bare or drive-relative
cwds, which also closes a pre-existing allow on cwd `C:`; its re-review sent 33 cases through the
real hook. Merges: `7924db4`, `da4273f`, `83d8a8c`.

### `2026-10-07-native-app-expertise` — what happened

Goal, in the owner's words: prime the fleet to be "the ultimate experts at building desktop and
mobile applications". The owner settled the stack before the run: Expo for mobile, Tauri 2 for
desktop, EAS cloud builds for iOS (Windows host, no Mac). Expertise was added the way
mobile-first was -- a registry `ui` value, a convention, and gated rules in existing nodes --
not as new "expert" agents. Single loop, forced by step 0.5 check 2.

The scout missed that `huntstack/apps/mobile` is already an Expo app; the architect caught it,
and the owner approved making huntstack's `ui` an array at the gate. Two real REJECTs: s1's
mobile convention allowed the `appVersion` runtimeVersion policy without requiring a version
bump on native change, so an OTA update would reach binaries lacking a new native module
(fixed: `fingerprint` default, explicit bump rule, checklist item 7); s2 amended the
architect's skip line so that mobile-first was cancelled for any native `ui`, which
contradicted itself for huntstack's array (fixed: skip only when `ui` lacks `responsive-web`).
Merges: `bdd4e55`, `d731660`, `6fe6351`, `3317dd5`.

Follow-ups found, not fixed: reviewer/builder `responsive-web` blocks read literally for string
`ui`; a broken `package.json` double-reports expo and tauri in `scout-facts.py`;
`guard-builder-scope.py` misresolves relative Bash paths from a `/c/...` cwd as `c:/c/...`
(denied approved writes, three builders worked around it with absolute paths); `new-app` says
`app.config` where the scaffold produces `app.json`.

### `2026-09-20-fleet-gaps` — what happened

The fleet's **second diamond**, run against itself, and the first run of any kind since
2026-09-06. Three slices, three disjoint file sets, all under `.graph/`: `postmortem.py`
gained stop-event classification (s1), `check-return-cap.py` was created (s2), and
`audit-fleet.py` stopped reporting the five deregistered siblings (s3). All three merged
clean; the full 13-suite run is green from merged `master`.

**The goal's own wording was unbuildable, and the scout's fact was wrong in the same
place.** The run was opened to make `postmortem.py` read the `parent` field. Before the
architect planned anything, the orchestrator checked this run's own `activity.jsonl`:
**0 of 52 events carried `parent`**, on a live run, because `record-activity.py:332`
writes it only when the payload has `parent_tool_use_id` and the payload never does. The
scout had reported that only this run would produce such data; it had already executed a
node and produced none. The architect re-scoped s1 onto what the fleet actually collects.

**Gap #20 stopped being a mystery and became a number.** One `scout` spawn produced 1
`start` and 6 `stop` events; across the run, 52 stops — **3 matched, 0
orphan-with-evidence, 49 phantom**. The discriminator is that a real node stop carries
`say` and `tokens` because its transcript exists, and a phantom carries neither because
none does.

**The one REJECT was correct, and traced two nodes upstream of where it appeared.** s2's
first attempt counted the last `text` block of a transcript and reported two compliant
returns (3 and 2 lines) as 4 and 10 — then its builder reported those false positives as
real gap #19 violations. The reviewer hand-counted the transcripts and refuted it. The
failure traced to the **architect's spec** (`last_said_by`'s definition, right for a
heartbeat caption and wrong for a return), with a minor to the **scout** for reporting
that return text survives in the transcript without reporting the shape it survives in.
Attempt 2 read the `SubagentHandback` payload; a fresh reviewer confirmed the fix by hand,
proved the new fixture load-bearing (reverting the reader drops the suite 50/50 → 38/50),
and ruled that the on-disk handback message is byte-identical to what the orchestrator
received — so the cap is measured where it is enforced.

**The approved shape was blocked by the harness, not by the plan** — see gap #23. Three
`isolation: "worktree"` spawns failed because the harness builds worktrees relative to the
launch dir, `repos/`, which is not a repo. The owner approved builders making their own
worktrees, which worked and incidentally proved `guard-builder-scope.py` maps a *fleet*
worktree correctly, something no run had exercised.

**What the run was also for.** Everything untested since 2026-09-06 executed: per-node
`--for` briefs (every node), the sonnet builder, `tokens`/`say` on every real lane,
`/postmortem`'s code path, and the four 2026-09-19 fixes. **The append lock carried three
concurrent builders and later three concurrent reviewers writing one `activity.jsonl`,
472 events, with no torn or lost line** — the contention that produced the corrupt line in
the 2026-09-06 log. `close-run.py`'s new pointer reminder fired on its first real close.

**It produced three findings of its own** (gaps #23, #24, #25), and the cost of #24 is
worth stating: every node in the run had to be told in its prompt to ignore a "prior
review attempt" that was schema placeholder text.

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
| 2026-09-03 | **The board was observed rendering — and the observation corrected the design.** A fresh session with `.graph/CURRENT` on a probe run spawned one `scout`, and the board appeared in the main tab. That closes the delivery half of gap #19: `systemMessage` from a non-display `PostToolUse` event reaches the user, which had been documented in two sentences that did not obviously agree and believed on the strength of the more specific one. The heartbeat then contradicted the *other* half of the design. `show-board.py` was written believing `Agent` completes when its subagent finishes; across the five runs carrying `activity.jsonl`, **all 32 `Agent` events land 0.0–0.2s after a `SubagentStart`**, nearest real stop 3.5s–1772s away, never the other way round — subagents run in the background and the spawn call returns a handle. So the hook prints a **dispatch** board, and nothing can print a return board, because the only event there is `SubagentStop`. Rather than lose the board that carries what a node actually did, the two were split by actor: the hook's is free and automatic, the orchestrator's is by hand. `feature-graph`'s "a node returning prints it for you, do not print it again" was written on the wrong premise and is now inverted; `GRAPH.md`, `show-board.py`'s docstring and gap #19 corrected to match. Second time in three days that a claim about what a hook event *means* survived review and was settled only by measuring the fleet's own logs. The probe run was deleted afterwards, as its own Runs-table row instructed. |
| 2026-09-03 | **`/audit-fleet` — the fifth skill, and the honour system replaced with a diff.** This file went materially false once (2026-08-26: still claiming zero product code eleven hours after run 3 merged) and its rule against that was enforced by `flag-stale-state.py`, a hook that can only *nag* — it fires on a write, says the snapshot is stale, and cannot tell whether anyone then re-checked anything. `audit-fleet.py` is the other half: it re-derives every mechanically decidable claim here from disk — `(N ln)` counts, roster frontmatter and has-it-ever-executed, app/node/skill counts, each registered app's directory + repo + entry docs, the Runs table against run directories and their own `status`, branch and remote, `settings.json` hooks against hook files in both directions, and `Last verified:` against the commit dates of definition files — and reports only drift. **Its first run found 8 real drifts in 94 claims**, all confirmed by hand: three line counts stale since the 2026-09-02 guard fixes, the roster's `integrator` cell still reading **no** while two other places in this same file said it ran, and **three closed runs missing from the Runs table**, one of them absent from this file entirely. That last one is the 2026-08-26 failure recurring, caught by machine instead of by accident. `test_audit_fleet.py`: 63 checks over 30 synthetic umbrellas, each a real `git init` fleet with a controlled committer date, because the tool's whole job is comparing a document to a filesystem and a mocked filesystem would test the parser and skip the comparison. It **never writes** — asserted by a case that hashes every fleet file before and after — and in particular never stamps `Last verified:`, per the 2026-08-25 do-not-revisit ruling. Prose claims (the gap list, the per-run narratives, the Decisions log) are out of scope by construction and the tool says so on every clean run. `feature-graph`'s orchestrator rules now run it **after every close**, which is where this particular drift is born: a finished run is the one event that changes what the fleet has done. |
| 2026-09-03 | **The board now prints itself.** Added `.claude/hooks/show-board.py`, a third `PostToolUse` entry on `matcher: "Agent"` that returns `brief.py`'s output as `systemMessage` when a node returns — so the board is machinery rather than orchestrator discipline, the same promotion `--audit` got from `flag-state-gap.py`. **`SubagentStop`, the obvious event, was ruled out on evidence** and the ruling is recorded in gap #19 with the docs quoted verbatim: it is a display event, and both its stdout and its `systemMessage` go to Claude's context "instead of being shown in the transcript". The fleet's own logs supplied a second reason, now gap #20 — 471 of 503 `stop` events are phantoms carrying an `agent_id` that never started, interleaved with running nodes. `Agent` was confirmed as the spawn tool from those same logs (31 occurrences, all main-session). Added `test_show_board.py`: 24 subprocess cases, run against a **copied** fleet in a temp directory rather than borrowing the live `.graph/CURRENT` the way the older hook tests do — that pointer is how the scope guard finds its run, and a concurrent session was live. The test caught a real defect immediately: `brief.py`'s `detail` line was **cwd-relative**, so the same run rendered differently depending on who printed it; it now resolves against the umbrella root per the launch rule. **Not observed**: that `systemMessage` actually reaches the main tab — hooks are snapshotted at session start, so it takes a fresh session to see. |
| 2026-09-03 | **The two-channel split: nodes return headlines, and `brief.py` renders the board.** Direct edit, owner-directed, no graph run (six node files, one skill, one spec, one new script — but it edits `.claude/agents/**` and `.claude/skills/**`, which `feature-graph` step 0.5 forces to single-loop anyway, and the change is one design ruling applied six times). `GRAPH.md` § 3 rule 3 now caps every node's return at a headline: no verbatim command output, no file lists, no findings bodies, because the next node reads `state.json` and nothing but the main tab reads the return. `scout`, `builder`, `reviewer` and `integrator` rewritten to fixed 3-line blocks; `architect` and `ops` keep their full blocks as the two gates, and now say why. The content those blocks stopped carrying is not lost but it was optional: `builders.<slice>.gate_results` and `reviews.<slice>.summary` are **required** as of this pass — `_schema.json` still calls both optional and was deliberately left byte-identical, because changing a template string flips old runs' untouched keys to "written" and breaks `--audit` on them (the exact regression `is_untouched()` was written for on 2026-08-26). Added `.graph/brief.py`, which renders a run as ~10 derived lines and is what the orchestrator now prints between nodes instead of relaying or re-narrating node text. Verified across all 8 runs on disk plus a synthetic mid-flight fixture. **Booked gap #19**: the cap is prose, nothing enforces it, and no run has executed under it yet. |
| 2026-09-02 | **All seven hook commands made cwd-independent; six stopped swallowing their errors.** Owner-directed follow-on to gap #18. Every command is now rooted at `"${CLAUDE_PROJECT_DIR:-.}/graph_agents/..."`; the six advisory `PostToolUse` hooks dropped `2>/dev/null` but KEPT `|| true`, since they must never block a write but have no business failing invisibly — all four scripts were verified silent on stderr when healthy first, so this adds no noise. The old form was shown to `exit 0` — reporting success — from inside `graph_agents/` while the interpreter never found the script, which is how six hooks could sit dead indefinitely; how long they actually were is unknown and unrecoverable. Added `test_hooks_resolve.py`, which parses the real commands out of `settings.json` rather than hardcoding them and runs each from a non-root cwd. It initially reported all 7 failing — that was the harness, not the hooks: `subprocess.run(shell=True)` on Windows is cmd.exe, which passes `${VAR:-default}` through literally; fixed to invoke a POSIX shell explicitly. |
| 2026-09-03 | **`builder.md` step 4 now spells out the `notes` one-line cap inline, not just in the Return block.** User-directed, prompted by FleetView being unreadable: real runs (`2026-09-02-date-accuracy`, all four slices) showed builders writing multi-paragraph self-justification prose into `notes` — narrating which tool they used, defending compliance with hooks, restating scope — instead of the one out-of-scope item the Return block already specified. `gate_results` was separately confirmed working as designed (verbatim evidence, per `_schema.json`); step 4 now says so explicitly so a builder doesn't over-correct and start summarizing it. `builder.md` 67→75 lines. No graph run — direct edit, single node file. FleetView side of the same complaint (progressive disclosure for `gate_results`) tracked as a separate `fleetview`-repo task, per the umbrella scope rule. |
| 2026-09-04 | **`reviewer.md` gains a 1,200-character cap on `summary` — the same overflow one layer up.** User-directed, from a review of what else FleetView renders badly. The builder-side fix the day before left the worse case untouched: `reviews.<slice>.summary` is specced as "one paragraph a human can read without opening `findings[]`" and the reviews on disk are **10,637 / 8,497 / 7,980 characters** — roughly 1,500 words in a one-paragraph field, and FleetView renders two of them side by side in narrow columns on a REJECT-then-PASS slice. Step 4 now caps it and says where the overflow goes: `findings[]` for per-issue detail, one sentence for the re-run instead of its transcript. `reviewer.md` 79→85 lines. Direct edit, single node file, no graph run. Note the cap is prose and nothing enforces it — same standing weakness as gap #19. |
| 2026-09-06 | **Claude commit attribution is now a check, not a convention — `guard-commit-trailers.py`, the fleet's second blocking hook and the first on `Bash`.** Owner-directed, prompted by the trailers landing in fleet commits *consistently* despite the rule being written down since 2026-08-26, when the history of two repos had to be rewritten to strip them. The diagnosis is that prose could never have held: Claude Code injects an attribution instruction into **every** session, orchestrator and subagent alike, as a system turn, so a node reading `CLAUDE.md` is being told opposite things by two authorities and the system turn tends to win. Four layers landed: the hook (denies the co-author, `Claude-Session`, the generated-with line, a claude.ai/code link, `noreply@anthropic.com`, and a non-owner `--author`; reads a `-F` message file too; applies to every `agent_type`); a new **invariant section in the constitution** and a restatement in the root `CLAUDE.md` that both say explicitly that the harness reminder does not apply here; a rule apiece in `builder.md`, `integrator.md` and `ops.md` — `ops` carries the part no hook can see, the PR body, release note and tag message; and `GRAPH.md` § 3 explaining why it is machinery rather than a sentence. **It denied its own documentation within minutes**: the first matcher was `git…commit` on one line and a heredoc writing that very sentence tripped it, so `git` must now sit in a command position with only git's own globals in between, pinned by three cases. Verified live twice in-session (denied, then the same commit clean, authored `njcurtis3`), 38 subprocess cases, `test_hooks_resolve.py` green at 9 commands. **Not** applied to history: 12 already-contaminated commits survive in `graph_agents` (4), `koenrane.xyz` (7) and `whoop-med-tracker` (1) — rewriting them means a force-push and is the owner's call, recorded in gap form rather than done unasked |
| 2026-09-09 | **The plan-scope guard now reads a builder's Bash command before it runs — gap #13 narrowed to *mostly guarded*.** Run `2026-09-06-bash-write-guard`, three sequential slices: a standalone write-target classifier (`bash_write_targets.py`, 199 self-test cases) plus a corpus measurement tool; then the matcher `Write\|Edit` -> `Write\|Edit\|Bash` on the existing guard, with the classifier imported inside `main()`'s `try` so a broken import denies loudly instead of failing open; then this file and the three fleet docs that had said `Write`/`Edit`. Measured, not asserted: 2.63% of real commands are a write shape whose target cannot be resolved and are allowed **with a warning**; the pre-filter passes 67.7% of commands, so 32.3% touch no disk at all. **Not closed** — the 16 named limits are in gap #13, led by the deliberate one: a write by a program the builder invokes is not caught, because catching it means denying every test command |
| 2026-09-09 | **Direct fix (below the stop-rule threshold): findings gain an optional `origin` — a failure-mode triage a reviewer can name instead of a REJECT just landing on the builder.** Owner-directed, from comparing this fleet's design against another. `_schema.json`'s `findings[]` example gained `"origin": ""`, `reviewer.md`'s Return-block rules now ask for it explicitly: `scout` when the fact behind the plan was wrong or missing, `architect` when the fact was right but the plan misread it, `builder` when the plan was right and the slice didn't match it, `""` when it's a plain implementation bug or doesn't trace cleanly — guessing a tag is worse than leaving it blank. `brief.py`'s `--for builder:<slice>`/`--for reviewer:<slice>` prior-attempts section now renders it as `(traces to <node>)` when set, silent when not, so a re-run builder sees it without opening `state.json`. `is_untouched()` needed no change — it already compares leaf-by-leaf, the exact fix 2026-08-26 made for schema growth like this. Confirmed old runs with no `origin` on their findings render with no crash and no spurious tag. `reviewer.md` 100→108, `brief.py` 680→682. Not yet exercised by a real reviewer — the taxonomy is untested against an actual REJECT |
| 2026-09-09 | **Direct fix (below the stop-rule threshold): `record-activity.py` now logs `parent_tool_use_id`, diagnostic for gap #20.** An external audit independently re-measured the phantom-stop pollution against all 9 runs and got numbers matching this file's stale 2026-09-03 ones exactly in shape and much worse in scale: 1,411 of 1,496 `stop` events (not 471/503) have no matching `start`, all 1,411 stamped `orchestrator`, and 97 real starts against only 85 matched stops — 12 nodes that verifiably ran never recorded a stop at all. Whatever these are, they are not "a subagent finished," and the two design decisions already settled by this file (ruling out `SubagentStop` as the board trigger; "scout is cheap" being unmeasured) both rest on data this pollution makes unreadable. Rather than redesign the contract on a guess, `record-activity.py` now records `parent_tool_use_id` when the payload carries one — a field it previously read and dropped — so the next real run can show whether a phantom nests under a real node's own tool call (a backgrounded `Bash` process, an internal agent behind `WebSearch`/`WebFetch`) or is genuinely orphaned. Logs the field; draws no conclusion. Verified end-to-end against a synthetic payload in an isolated copy of the fleet, not against a live phantom |
| 2026-09-09 | **Direct fix (no graph run, below the stop-rule threshold): per-node briefs, and `builder` moved opus → sonnet.** Both came out of an external review of the fleet's own token spend, which the fleet's heartbeat data confirmed: every node's contract was "read the whole `state.json`", several hundred KB on a mature run, most of it keys the reading node never uses. `brief.py` gained `--for <node>[:<slice>]`, deriving — never authoring — the slice one node type actually needs: an architect gets the scout's facts in full with nothing else written yet; a builder gets its own plan entry, the facts behind it, and any prior REJECT findings on its slice; a reviewer gets that plan entry plus what the builder reported; integrator and ops get the whole built/reviewed picture, since fan-in has no smaller unit. `GRAPH.md` §3's contract and all six agent files' read steps now point at the brief first, `state.json` only for what it omits. Measured on `2026-09-06-bash-write-guard`: 168KB down to 2.8KB for the integrator brief, 33-38KB for a builder/reviewer brief on a run whose reviews ran to five-figure character counts. **`builder` → sonnet** on a different argument than the scout downgrade: a builder implements a slice a human already approved at the gate, so the judgment call already happened, and the never-downgraded `reviewer` exists to catch what a cheaper executor misses. `reviewer` and `architect` stay opus, unchanged. Exercised `--for` by hand across all six node types and both its error paths; not yet run through a live builder spawn or added to `test_brief.py` — both booked, not closed. Also extended `audit-fleet.py`'s number-word map (`WORDS`) past twelve to fifteen, which it needed the moment the fleet reached its thirteenth run and this file started spelling that out in prose |
| 2026-09-11 | **`/postmortem` — the sixth skill, and the third of three routers a brainstorm named worth building.** The other two, `/close-run` and `/audit-fleet`, were built 2026-09-03; this is the leftover, deliberately deferred at the time because it reads `activity.jsonl` and gap #20 (phantom `SubagentStop` events) makes duration unsound. Owner-directed: build it now, scoped around the gap rather than waiting on it. `postmortem.py` reports tool counts per node, diamond concurrency (builder lanes' first/last `start`/`tool` timestamp windows overlapping — never a `stop`), slice round-trip counts via `verify-state.py`'s own `review_attempts`/`ever_rejected`, and risk-tag fit (`architect.plan[].risk` grouped against which slices looped) — the 2026-08-28 `archive-adapters` review's method, data-backed instead of remembered. Phantom-stop filtering: a lane is real once it has a `start` or `tool` event; a lone `stop` on a fresh, never-seen `id` is counted and discarded, never folded into a lane. Verified against every run on disk with a heartbeat (no crash on `2026-09-06-bash-write-guard`, which has none) plus 17 synthetic cases in `test_postmortem.py`, built the same way `test_close_run.py` was — real fixture data, not a stub — because the one thing this script must never get wrong is exactly gap #20's shape, and a clean synthetic log would not have caught it. First run against real history (`archive-adapters`) surfaced a finding worth booking rather than papering over: its diamond recorded only **one** `builder` agent_id for three concurrent worktree builders, so the heartbeat cannot currently show a diamond's concurrency after the fact — the postmortem's own concurrency section says so as a note, not a bug in the script. Read-only, never gates, exit 0 unless the run cannot be read. Not yet exercised on a request that wasn't this one |
| 2026-09-11 | **`record-activity.py` now attaches a real `tokens` total, for FleetView's per-node token counter.** Owner-directed. Checked against the hooks reference first: no hook payload carries a usage/token field at all, on any event. What does exist is a location Claude Code owns, not this fleet — `~/.claude/projects/<encoded cwd>/<session_id>/subagents/agent-<agent_id>.jsonl`, one line per subagent turn, each carrying a real `message.usage` block — confirmed by reading actual files from past sessions on this machine before writing anything against the shape. On every `tool`/`stop` event carrying an `agent_id`, the four usage fields are summed across that one agent's transcript and written as `tokens`, a running total (so the last value written is that instance's true final count). This is a real, accepted coupling to an undocumented internal layout rather than a documented API — the alternative was fabricating a number — and it fails silent: `tokens_used_by` returns `None` on any read/parse problem and the field is simply omitted, same as every other best-effort field here. 15 checks added in a new `test_record_activity.py`. FleetView's own half (attributing a count to a specific graph node only where the fleet's data can actually back it — never on a diamond's concurrent builders/reviewers) lives in its own repo |
| 2026-09-11 | **`record-activity.py` now also attaches a real `say` field — the newest thing that agent's own transcript has it saying — for FleetView's live agent-caption feature.** Owner-directed, same session as the token counter and the same underlying transcript file, read once for both. The same `message` object that carries `usage` also carries `content`, a list of blocks; `last_said_by` keeps the newest `text`-type block it finds (never a `tool_use` block), collapses it to one line, and caps it at 220 chars (`SAY_MAX_CHARS`) so the heartbeat log stays a heartbeat, not a transcript copy. Unlike `tokens`, `say` is a snapshot, not a running total — a later event replaces it rather than accumulating. Fails silent identically: `None` on any read/parse problem, on an empty file, or on a transcript that never once contains a text block, and the field is simply omitted. 8 more checks added to `test_record_activity.py` (23 total, was 15): newest-text-wins across turns, tool-only-transcript stays `None`, empty file, missing file, and the 220-char cap with its ellipsis. FleetView's half (`sayForNode` in `index.html`, reusing the exact one-open-instance attribution rule `tokensForNode` already established) was visually verified in Chrome against a synthetic fleet directory: the caption appears on the one attributable open instance, updates as new lines are appended to `activity.jsonl`, freezes at its last-seen value once the node stops being live, is correctly absent on a queued sibling of the same kind, and is correctly absent on both slices of a diamond's concurrent same-type builders |
| 2026-09-19 | **Gap #14 closed: the `_schema.json` placeholder is no longer an approved path.** `schema_placeholders()` walks the schema and compares entries by identity — the question "is this the untouched template?" has a correct answer on disk. One recorded loosening: a gated run with no real file set now gets "no opinion" instead of a deny built on a junk path |
| 2026-09-19 | **Gap #15 closed: the staleness hook goes quiet inside builder worktrees**, and got its first tests ever (`test_flag_stale_state.py`, 125 ln, 18 checks). Proved non-vacuous by firing the pre-fix hook at the exact payload that reported the gap. Deliberate cost: fleet edits made inside a worktree are silent too, and the merge to the main tree is what flags them |
| 2026-09-19 | **Gap #22 booked: the heartbeat's append was losing events, and the old logs cannot be repaired.** Measured 471/600 events surviving four concurrent writers, with zero torn lines — invisible to every reader in the fleet. Fixed forward with a sidecar-file lock; `O_APPEND` alone was the first attempt and does not hold on Windows |
| 2026-09-19 | **The open-run pointer stops meaning anything once a run is parked or closed.** `parked` added to `record-activity.py`'s and `guard-builder-scope.py`'s closed-status lists, matching `show-board.py`; `close-run.py` now tells you to clear `.graph/CURRENT` on a green close, and still never writes it |
| 2026-09-20 | **Gap #19's open core CLOSED: `check-return-cap.py`, the first machine check for the three-line return cap.** Reads the `SubagentHandback` message, not the last text block — attempt 1 did the latter, turned two compliant returns into false positives, and was REJECTed for it. Report-only by decision; enforcement is a later call |
| 2026-09-20 | **Gap #20 measured, not merely described.** `postmortem.py` classifies every stop MATCHED / ORPHAN-WITH-EVIDENCE / PHANTOM: 52 stops, 3 matched, 49 phantom. A phantom is an id with no start and no transcript. The 2026-09-09 `parent` diagnostic is confirmed dead — 0 events carried it across a full live run — and its removal is deferred, not forgotten |
| 2026-09-20 | **`audit-fleet.py` stops reporting the five deregistered siblings.** The list is data carrying the owner's permanent ruling; the five are silent, an unknown sibling still raises a note, and a deregistered name appearing in `registry.json` is DRIFT — with no inverse claim |
| 2026-09-20 | **The second diamond, and the append lock's first contention test**: three builders then three reviewers writing one `activity.jsonl`, 472 events, nothing torn or lost. Also the first run to exercise `--for` briefs, the sonnet builder, `tokens`/`say` and the four 2026-09-19 fixes. Booked gaps #23–#25, all found by executing rather than reading |
| 2026-09-22 | **ADR 0001: Jev is not adopted, and `decisions/` exists to say so.** TypeSafe's Jev (shipped 2026-09-15) returns typed calibrated decisions instead of text, ~200x faster and ~400x cheaper than an LLM classifying. Declined for the fleet on four grounds, none of them "the premise is wrong": every enforcement point here is already exact Python and a probability is a downgrade (`guard-commit-trailers.py` exists *because* prose judgment failed, 2026-08-26); every genuine judgment node must emit prose a human or the next node acts on, which Jev structurally cannot; the target layer is ~3 decisions per run, so 400x of nothing is nothing; and no `PreToolUse` hook may depend on a network call, whose only failure modes are fail-open (the guard is gone) or fail-shut (the fleet is unusable offline). The tempting integration — Jev resolving `guard-builder-scope.py`'s unresolvable `Bash` write targets — is the most dangerous one: the command string is written by the builder being guarded, and a published test moved a block probability from 0.76 to 0.48 with one planted field. The architect's `risk` tag was considered on the merits and rejected as a correct shape with no problem to solve. Three named conditions would reopen it, sharing one test: high volume, no enforcement authority, cheap wrong answer. `decisions/` is a new directory, scoped to the fleet, read at runtime by nothing |
| 2026-09-22 | **ADR 0001: Jev is not adopted, and `decisions/` exists to say so.** TypeSafe's Jev (shipped 2026-09-15) returns typed calibrated decisions instead of text, ~200x faster and ~400x cheaper than an LLM classifying. Declined for the fleet on four grounds, none of them "the premise is wrong": every enforcement point here is already exact Python and a probability is a downgrade (`guard-commit-trailers.py` exists *because* prose judgment failed, 2026-08-26); every genuine judgment node must emit prose a human or the next node acts on, which Jev structurally cannot; the target layer is ~3 decisions per run, so 400x of nothing is nothing; and no `PreToolUse` hook may depend on a network call, whose only failure modes are fail-open (the guard is gone) or fail-shut (the fleet is unusable offline). The tempting integration — Jev resolving `guard-builder-scope.py`'s unresolvable `Bash` write targets — is the most dangerous one: the command string is written by the builder being guarded, and a published test moved a block probability from 0.76 to 0.48 with one planted field. The architect's `risk` tag was considered on the merits and rejected as a correct shape with no problem to solve. Three named conditions would reopen it, sharing one test: high volume, no enforcement authority, cheap wrong answer |
| 2026-09-22 | **Model tiering measured for the first time, and its central claim is false.** `GRAPH.md` §198 had listed tiering as something that "argues cost hard and has never measured it". Aggregating the `tokens` field over `2026-09-20-fleet-gaps` (10 spawns, 34.3M tokens, max-per-agent since the field is cumulative): builder **51.4%**, reviewer 22.1%, scout **17.4%**, architect 5.1%, integrator 3.9%. § Model tiering says scout "is usually the single biggest lever on a run's total spend"; measured, it is third and builders are triple it. Caveats recorded with the number: n=1 run, a diamond fans three builders against one scout, and `tokens` counts context processed (mostly cache reads), not fresh input. Not yet corrected in `GRAPH.md` — booked as gap #26 |
| 2026-09-22 | **The snapshot split in two: `CURRENT-STATE.md` (what is true) and `HISTORY.md` (what happened).** The run narratives and this Changelog were 31% of the file by weight — the Changelog alone was 22% in 77 dense lines — and neither answers the question the snapshot exists to answer. The cut follows the line `audit-fleet.py` already drew between checked tables and out-of-scope prose, and was verified by claim count rather than by eye: **126 before, 126 after**, so no check was silently deleted. `flag-stale-state.py` now routes each obligation to the right file (Runs table row → `CURRENT-STATE.md`; narrative + Changelog row → here) and never fires on `HISTORY.md`, since writing here is how the obligation is discharged. Its tests went 18 → 23 checks, and one existing check had to be sharpened: it asserted the word `HISTORY` was absent to prove the definition branch had fired, which the new message made ambiguous |
| 2026-10-06 | **Recursive Language Models, as a reading tool and never a judge.** `.graph/rlm.py` is an RLM REPL after Zhang, Kraska & Khattab (arXiv:2512.24601): the input sits in `context`, the caller peeks/greps/chunks it in code and maps headless `claude -p` haiku sub-calls over the pieces (`llm_map`, 4 concurrent — the paper's blocking sub-calls fixed). `/rlm` is the skill; `scout.md`, `postmortem` and `audit-fleet` point to it for inputs over ~50KB. `reviewer`/`architect`/`integrator` are excluded, because reading through haiku is a downgrade of the reader (ADR 0002). Three live measurements reshaped it before it shipped: the fleet's default system prompt made a sub-call 14x dearer, so sub-calls run bare and outside `repos/`; `--max-budget-usd` bills and then discards the answer, and the first session overspent $0.237 against $0.10, so every call now reserves a worst-case estimate first; thinking was ~90% of cost, but switching it off gave a wrong answer, so the default is `--effort low`. First real use, over `CURRENT-STATE.md`: $0.0996, 79s, 12/12 open gaps plus one false positive. |
| 2026-10-06 | **Docs caught up with RLM, and v1.0.0 cut.** README gained the recursive-reading section, the `rlm` router row (seven skills, not six), `/rlm` in the command list, and a layout block that finally lists `HISTORY.md`, `conventions/`, `decisions/` and `rlm.py`. `reviewer.md`, `architect.md` and `integrator.md` each now say in their own file that they do not read through `/rlm` — ADR 0002 had said so, but a node reads its own page, not the decision log. Tagged `v1.0.0`: the first release, covering the fleet as it stands — six nodes, seven routers, the hooks, the checkers and the RLM reader. |
| 2026-10-06 | **README reformatted to match `omaorchestra`'s.** Centred wordmark (`docs/assets/logo-{light,dark}.svg`, new), tagline, badge row and nav row; Introduction with `[!WARNING]`/`[!NOTE]` callouts; features as a two-column table; Install, Setup and a hooks table; Supported versions; Documentation. Badges are limited to what exists — no tests badge (no CI) and no license badge (no LICENSE). The registry example was corrected on the way: it is an object with an `apps` array, not a bare array, and carries `ui`. |
| 2026-10-07 | Native app expertise: ADR 0003 (Expo/EAS + Tauri 2), `conventions/native-mobile.md` + `native-desktop.md`, `ui` values `native-mobile`/`native-desktop` (array allowed), gated native rules in architect/builder/reviewer/ops/scout, native scaffolding in `new-app`, Expo/Tauri detection in `scout-facts.py` + `test_scout_facts.py`. Run `2026-10-07-native-app-expertise` |
| 2026-10-07 | Native follow-ups: `responsive-web` conditions are array-aware (architect, builder, reviewer, new-app, mobile-first); plan-scope guard resolves MSYS/Cygwin drive paths on Windows and fails closed on drive-relative cwd; `scout-facts.py` reports unparseable `package.json` as its own kind; `new-app` names `app.json`. Run `2026-10-07-native-followups` |
| 2026-10-09 | Orchestra fleet sync: `.graph/orchestra-sync/` (`sync.py`, `test_sync.py`, `payload.json`, `alternates/`) -- a one-way, owner-run sync of the core fleet into the `orchestra` app's vendored `fleet/`, with umbrella-only spans marked upstream and replaced from sha256-pinned alternates, a `@FLEET@` path token, a leak gate that refuses on owner paths/username/registry ids/sibling names/dated run ids, and `--verify-upstream` proving the umbrella copy unchanged. Marker lines added to all 6 agents, 3 skills, `GRAPH.md`, 5 hooks and 6 scripts (insertions only). `orchestra` registered as the 6th portfolio node. Run `2026-10-09-orchestra-fleet-sync` |
