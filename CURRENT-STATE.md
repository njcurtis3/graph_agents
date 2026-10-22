# CURRENT-STATE — graph_agents

> **Last verified: 2026-10-22**
>
> **What the 2026-10-18 pass covers** (after runs `2026-10-17-orchestra-p2-protocol-v1`, `2026-10-17-orchestra-p2-followups`
> `2026-10-17-orchestra-h1-linux`, `2026-10-17-orchestra-p3-host-link`, `2026-10-18-orchestra-p3b-desktop-pairing`, `2026-10-18-orchestra-p3b-followups`, `2026-10-18-orchestra-a1-pair-and-see`, `2026-10-20-orchestra-a1-followups`, `2026-10-20-orchestra-a2-answer` and `2026-10-22-orchestra-a3-notifications`, all **single-loop** against `orchestra`, sequential slices on one branch in a linked worktree, merged by the orchestrator;
> no fleet definition file changed; `HISTORY.md` gained only the appended P3a and P3b rows, read on 2026-10-18). Re-checked by `audit-fleet.py`: the status headline (34 runs, none in flight), the ten
> new Runs-table rows, and the roster's execution counts read from run state (scout 34 and architect 34 runs, builder 116
> slices, reviewer 115 reviews, integrator 5 runs). **Not re-checked:** any narrative claim outside those rows. The two
> `bash_write_targets.py` / `measure_bash_corpus.py` "registered" drifts are the long-standing false positives,
> unchanged; `Archer-Store` is an unregistered sibling, left out of the portfolio on purpose (owner, 2026-10-20).
>
## Status: 34 runs, 33 of them executed; the fifth diamond has run

Built 2026-08-25 in a single session. Eleven run directories on disk. The first five are
narrated in full below; three more ran 2026-08-31 → 2026-09-03 and were **missing from
this file entirely until 2026-09-03**, when `/audit-fleet`'s first run found them.

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
- `2026-08-31-mobile-first-criteria` against the fleet itself — **executed**, 3 slices, all
  PASS on attempt 1, merged `dd7ac0b`. Produced `conventions/mobile-first.md` and the
  registry's `ui` routing field.
- `2026-09-01-huntstack-mobile` against huntstack — **executed**, 4 slices, all PASS,
  branch `feat/mobile-expo-scaffold`. Closed its outstanding human-read gate on 2026-09-03
  against a physical Android phone, recorded in the run's own `log` rather than by editing
  a reviewer's key.
- `2026-09-02-date-accuracy` against huntstack — **executed**, 3 planned slices plus one
  off-plan (`s4`, CI), all PASS, merged `50a5299`. Closed with `s2`'s human-read gate
  explicitly **not** run, by the human's own decision, and said so at the close.

These three are the drift `/audit-fleet` was built to find, and it found them on its first
run: all three were `status: done` on disk while the Runs table listed five runs and this
paragraph said "five runs so far". `2026-08-31-mobile-first-criteria` was not mentioned
anywhere in this file. That is the 2026-08-26 failure repeating, in a file whose header
warns about exactly it.

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
| Umbrella constitution | live | `graph_agents/CLAUDE.md` (131 ln) |
| Fleet history | live, **split out of this file 2026-09-22**. Holds the sediment: the per-run `### <run-id> — what happened` narratives and the Changelog. Both are append-only and never revised, and together they were **31% of this file by weight** while answering nothing about what is currently true. The split line is the one `audit-fleet.py` already drew — it parses neither section and said so before the move — so it was verified by claim count: **126 claims before, 126 after**. `flag-stale-state.py` names both files and is silent on this one | `graph_agents/HISTORY.md` (418 ln) |
| Decision records | live, **added 2026-09-22**, 3 records (0002, RLM scope, added 2026-10-06; 0003, native stack -- Expo/EAS + Tauri 2, added 2026-10-07). Numbered records for questions settled once, so they are not re-argued from scratch. Distinct from `conventions/`: a convention says *how we build*, a decision says *what we chose and what would reverse it*. Nothing reads them at runtime | `graph_agents/decisions/0001-no-jev-in-the-fleet.md` (136 ln) |
| Graph spec | live | `graph_agents/GRAPH.md` (445 ln) |
| Portfolio index | live, **6 nodes** — 3 products, 2 tools, 1 site — ids and `kind` verified 2026-08-31; **`orchestra` added 2026-10-09** via `/new-app` (product, `ui` `["native-desktop","native-mobile"]`, repo github.com/njcurtis3/Orchestra): desktop command center + Android remote for coding agents, carrying a vendored copy of this fleet in `orchestra/fleet/` filled only by `.graph/orchestra-sync/sync.py`. **Narrowed from 8 to 4 on 2026-08-31**: `koenrane.xyz`, `personal-archive`, `thrml`, `whoop-med-tracker` removed at the owner's direction — those repos are personal, not part of the development umbrella going forward. Not deleted from disk, just deregistered; the fleet routes to none of them. **`telosrg-site` added same day** via `/new-app` — the org's public marketing site. Also gained `org`/`org_status`/`org_domain`/`org_domain_status`/`org_github`/`org_github_status` fields (2026-08-31): "Telos Research Group", working name not yet a formed legal entity; domain `telosrg.com` **purchased** 2026-08-31 (re-verified registered via RDAP against Verisign after the owner reported buying it); GitHub org **github.com/TelosRG registered** 2026-08-31 (re-verified via `api.github.com/orgs/TelosRG` after the owner reported creating it) | `graph_agents/portfolio/registry.json` (174 ln), **untracked on purpose** — see below |
| Run-state schema | live | `graph_agents/.graph/runs/_schema.json` (32 ln) |
| Root memory shim | live, `@`-imports the constitution | `repos/CLAUDE.md` |
| `.claude` junction | live, verified same-dir | `repos/.claude` → `graph_agents/.claude` |
| 6 agent nodes | live; **5 of 6** have executed as registered agents — `integrator` first ran 2026-08-26 (`archive-adapters`). **`ops` is the only node never executed** | `.claude/agents/` |
| 7 skills | `feature-graph` exercised 3× (398 ln); `new-app` **exercised three times** — `personal-archive` 2026-08-26, `roamex` 2026-08-28, `telosrg-site` 2026-08-31; **native-mobile/native-desktop scaffolding added 2026-10-07** (134 ln); `fleetview` exercised (56 ln); `close-run` **added 2026-09-03, first real closes 2026-09-05 — the payload-split and review-attempts runs** (95 ln); `audit-fleet` **added 2026-09-03, exercised on this file the same day** (93 ln); `postmortem` **added 2026-09-11, not yet exercised on a real request** — deliberately scoped around gap #20, no duration/wall-clock anywhere in it (74 ln); `rlm` **added 2026-10-06, exercised live the same day over this file** (98 ln) | `.claude/skills/` |
| Fleet auditor | live, **added 2026-09-03**, and the first checker whose first run found live drift in this file. Diffs the *checkable* claims here against disk: every `(N ln)`, the roster's model/tool/line/has-executed cells against frontmatter and run state, app + node + skill counts, each registered app's directory and repo and entry docs, the Runs table against the run directories and their own `status`, branch and remote against git, `settings.json` hooks against the hook files **both ways**, and `Last verified:` against the commit dates of fleet definition files. Reports only drift. ****2026-09-20, s3:** the five deregistered siblings became a module-level `DEREGISTERED` tuple carrying the owner's permanent ruling; they now produce NO output, an unknown sibling still produces the note, and a deregistered name appearing IN `registry.json` is DRIFT -- no inverse claim, so deleting one of those repos never turns the auditor red. It never writes, and in particular never stamps the date** — that decision is marked do-not-revisit. Prose is out of scope by construction | `graph_agents/.graph/audit-fleet.py` (616 ln), `graph_agents/.graph/test_audit_fleet.py` (399 ln), `.claude/skills/audit-fleet/SKILL.md` |
| Close checker | live, **added 2026-09-03**, and **first used for real 2026-09-05** — it REFUSED `2026-09-04-payload-split`, which is why `2026-09-05-review-attempts` exists. Answers whether a run may be closed: `--audit` clean, gate passed, every slice — off-plan included — built and `PASS`, and **the work proved present in git** rather than in `state.json`. That fourth check is the one nothing else in the fleet makes. Read-only like `verify-state.py`; on green it prints the close for the orchestrator to write. Re-run against all 8 historical runs: `archive-adapters` reports closeable under `--recheck`, `fleet-hardening` reported **8 blockers**; since 2026-09-05 it reports **3** — the four verdict-based ones were a tooling blind spot, not findings, and the survivors (`closing_fix` unreviewed, no authorship stamps) are the real answer about it. `--recheck` exists to audit an already-closed run. **2026-09-19:** on green, and only when `.graph/CURRENT` names the run just closed, it also says to clear that pointer — nothing else in the fleet does, and it still writes nothing itself | `graph_agents/.graph/close-run.py` (281 ln), `graph_agents/.graph/test_close_run.py` (309 ln), `.claude/skills/close-run/SKILL.md` |
| Postmortem | live, **added 2026-09-11**, not yet run against a real request — verified by hand across all runs carrying a heartbeat (no crash, no traceback on a run with no `activity.jsonl`) plus 17 synthetic cases. Reports tool counts per node, diamond concurrency (builder lanes' tool-bounded windows overlapping), slice round-trip counts, and risk-tag fit (do `risk: high` slices carry the loops, or does `risk: low` loop just as much) — the 2026-08-28 `archive-adapters` review done again, data-backed. **Deliberately prints no duration or wall-clock anywhere**: **2026-09-20, run `2026-09-20-fleet-gaps` s1:** gained `## Stop-event integrity` -- every `stop` classified MATCHED / ORPHAN-WITH-EVIDENCE / PHANTOM with the ratio printed, the first thing in the fleet that MEASURES gap #20 rather than describing it. Its SKILL.md section table is now stale, found by s1's reviewer, outside that run's file set and needing a fresh session to fix. Even so, gap #20 is still open, so nothing here reads a `start`/`stop` pair — only `tool` events (always correctly attributed) and lanes filtered to exclude a phantom `stop`'s fresh, never-started `agent_id`. Read-only, never gates, exit 0 unless the run cannot be read at all | `graph_agents/.graph/postmortem.py` (309 ln), `graph_agents/.graph/test_postmortem.py` (238 ln), `.claude/skills/postmortem/SKILL.md` (74 ln) |
| Return-cap checker | live, **added 2026-09-20** by run `2026-09-20-fleet-gaps` s2, and **report-only by decision** -- not a hook, not a gate, not wired into `settings.json`; promotion is a decision to take after it has run against more real data. Machine check for `GRAPH.md` section 3 rule 3's three-line return cap, prose since 2026-09-03 with nothing enforcing it. Reads the **`message` argument of a node's `SubagentHandback` tool_use** in its own transcript -- NOT the last text block, which is what attempt 1 did and was REJECTed for: post-handback chatter the orchestrator never received made two compliant returns (3 and 2 lines) read as 4 and 10, so its only failure signal was wrong on its first real data. A lane with no handback on disk is `unverifiable`, never certified compliant. Exit 1 only for a real over-cap return; every read failure is exit 0. **Never echoes transcript text** -- type, id and line count only. Second deliberate coupling to Claude Code's undocumented transcript layout, after `record-activity.py` 2026-09-11, approved at the gate. Its reviewer confirmed the on-disk handback message is byte-identical to what the orchestrator received, so the cap is measured where it is enforced, not on a proxy. First full outing, on the run that built it: **9 compliant, 0 over cap, 1 unverifiable** (the in-flight integrator) | `graph_agents/.graph/check-return-cap.py` (301 ln), `graph_agents/.graph/test_check_return_cap.py` (423 ln, 50 checks) |
| RLM reader | live, **added 2026-10-06**, and **exercised live the same day** -- not by a node yet, by the orchestrator over this file. A Recursive Language Model REPL (arXiv:2512.24601): the input sits in a variable, the caller peeks/greps/chunks it in code and maps `claude -p` haiku sub-calls over the pieces, 4 concurrent, `--effort low`, no tools, no settings, cwd outside `repos/`. A dollar budget is reserved per call before it runs. Not a hook and never called by one (ADR 0001 § 4); scope in ADR 0002. Suite: `graph_agents/.graph/test_rlm.py` (186 ln), offline under `RLM_FAKE_LLM` | `graph_agents/.graph/rlm.py` (529 ln) |
| Scout fact collector | live, **added 2026-08-28**, not yet exercised by a real scout run. Verified by hand across all 8 apps: correct git/HEAD/dirty/identity, `--all` and `--json` modes, and the registry-vs-disk contradiction lines. Computes, never caches — a per-app fact *store* was designed and **rejected on evidence** the same day (see Decisions log) | `graph_agents/.graph/scout-facts.py` (378 ln), `graph_agents/.graph/test_scout_facts.py`; **since 2026-10-07** detects Expo and Tauri up to 2 levels deep and flags a `ui` that omits the matching native value, `scout.md` step 0 |
| Staleness hook | live, **observed firing** 2026-08-25; rewritten 2026-08-26 (junction paths, run-close, `.py`) — 20 synthetic payloads pass. **Stopped firing inside builder worktrees 2026-09-19** (gap #15), and **gained its first tests the same day** after 25 days and a rewrite with none: `test_flag_stale_state.py` (141 ln, 23 checks), run as a subprocess the way the harness runs it, so exit 0 and parseable JSON are asserted too | `.claude/settings.json`, `.claude/hooks/flag-stale-state.py` (143 ln) |
| State verifier | live, **two modes**. Named-key mode: advisory, a check the orchestrator runs. `--audit` mode: fires from a hook, checks edge ordering. **Fixed 2026-08-26 (`4cbe78c`)** — it counted `_schema.json`'s example slice as real, so the fan-in check fired on *every* run reaching an integrator and no diamond could close green. 5 new fixtures + byte-identical output on all four prior runs | `graph_agents/.graph/verify-state.py` (578 ln), `graph_agents/.graph/test_verify_state.py` (238 ln) |
| Plan-scope guard | live. **Fixed 2026-08-26 (`46e0f25`) to be worktree-aware** — it resolved plan entries against `repos/`, so it denied *every* write by *every* builder in a diamond. **Fixed again 2026-09-02: it did not glob.** A plan entry of `<dir>/**` normalised with its literal `**` attached, and since no real file is equal to or prefixed by a path ending in `**`, it denied *every* write under an approved directory — it blocked 3 of 4 slices of `2026-09-01-huntstack-mobile`, whose file sets were exactly that. Trailing `**`/`*` segments are now reduced to the directory they stand for at parse time, residual wildcards fall through to `fnmatch`, and both match sites share one `_match()` so they cannot drift apart a third time. **Now has a real self-test** (82 checks, up from 14; previously the 14 "synthetic cases" lived only in a builder's transcript). **Exercised for real** across 9 builder runs with zero false denials since. **Matcher is `Write\|Edit\|Bash` since 2026-09-09** — run `2026-09-06-bash-write-guard`, which narrows gap #13 to **mostly guarded** rather than closing it, and the honest limits are listed there in full. How the Bash half works: `bash_write_targets.py` classifies a command string into resolved write targets and an unresolved-write-shape flag, and every resolved path is judged by the **same `_match()`/`approved_paths()`** the `Write` branch uses — one matcher extended, not a second hook that can drift from it. Redirects, heredocs, `tee`, `sed -i`, `perl -i`, `rm`, `mkdir`, `touch`, `cp`, `mv`, `install`, `dd`, `truncate`, `ln`, `git checkout/restore/apply`, `curl -o`/`wget -O` and inspected `python -c`/`node -e` bodies are read; wrappers, `eval` of a literal, `$(...)` bodies and `xargs` are unwrapped. A correction the run measured and this file should not lose: `install`, `dd`, `truncate` and `ln` are implemented and tested but appear **0 times in command position** in the corpus — the scout's counts for them were substring hits (`npm install`, `dd` inside a hash, "truncate" in prose), and the mechanism list was planned partly on those. `curl` sits at 171 command-position uses, which is why it was added mid-slice on the human's call. **What it cannot resolve it ALLOWS and records** — 2.63% of real commands (55 of 2091 when last measured) are a write shape whose target is a variable or a substitution, and those emit a warning rather than a denial, which closes the trace half of gap #13 where it cannot close the denial half. A cheap regex pre-filter runs before any disk read so read-only work pays nothing: **pre-filter PASS rate 67.7%, zero-disk-I/O share 32.3%** (676 of 2091) — two different numbers, which this run conflated four times before measuring them apart; expect roughly one Bash call in three to skip the state read, not two in three. The pre-filter is a superset of the parser **anchor-relative, over unquoted, unescaped command-position spellings** — not a proof, a list, and the spellings outside it (`r""m`, `$'rm'`, a line continuation inside the verb) fail OPEN, 0 in the corpus. `MAX_COMMAND` (128KB) is checked **before** the pre-filter, so it bounds inputs above 128KB; it does **not** bound the pre-filter, whose regex is quadratic below the cap (gap #13, item 10). Adding `curl`/`wget` moved **14 corpus commands from clean to resolved**, added a target to 3 already-resolved ones and moved 1 to unresolved — the durable figure, since the corpus is live and grew 2073 → 2091 during this run's own passes. **Fails closed both ways**: a broken or missing classifier denies *every* builder Bash call, `git status` included, naming this hook — proven across eleven fault injections — while a classifier that returns a confident wrong answer is not detectable at all. **A changed matcher took effect MID-SESSION**: the `s2` builder's own Bash calls became guarded the moment `settings.json` was written, with no restart. Observed once, live, by that builder and corroborated by its reviewer from the shipped `warn()` string — **not independently reproduced**, because the guard exempts every non-`builder` agent, so a reviewer's own calls stay silent either way. **Fails CLOSED since 2026-09-02**: `main()` wraps `decide()` and emits a deny naming the hook itself as broken, and `settings.json` no longer swallows errors — a crash blocks builders loudly instead of silently voiding the human gate (gap #17, closed). All seven hook commands are now cwd-independent via `${CLAUDE_PROJECT_DIR:-.}` and covered by `test_hooks_resolve.py` (gap #18, closed). **2026-09-19:** an untouched `_schema.json` placeholder is no longer read as an approved path (gap #14, closed) — identity against the schema, not a cleverer prose heuristic — and a pointer at a **`parked`** run no longer constrains a builder, matching `show-board.py`. **2026-10-07 (run `2026-10-07-native-followups` s2):** on Windows, `norm()` now reads MSYS/Cygwin drive spellings (`/c/...`, `/cygdrive/c/...`) as `C:/...` and the Bash cwd is joined before normalising -- relative writes from a Git-Bash cwd were being misresolved to `c:/c/...` and denied even when approved. Attempt 1 opened a fail-open (a drive-root cwd collapsed to drive-relative `c:` and resolved against the hook's own cwd) and was REJECTed; the shipped version fails closed on any bare or drive-relative cwd, which also tightens a pre-existing allow on cwd `C:`. `/mnt/c` is not translated | `.claude/settings.json`, `.claude/hooks/guard-builder-scope.py` (687 ln), `.claude/hooks/test_guard_builder_scope.py` (738 ln) |
| Bash write classifier | live, **added 2026-09-09**, and **not a hook** — a pure module the plan-scope guard imports (inside `main()`'s `try`, never at module top, because a top-level `ImportError` exits non-zero and the harness reads that as a hook error and lets the write through). `classify(command)` returns resolved target paths plus an unresolved-write-shape flag and holds **no opinion about scope**: it returns paths, the guard judges them. Self-tested at **199 cases**, 77 of them not-a-write and 42 of those lifted from the real corpus, with every command in the file swept through five re-spellings to check the pre-filter never hides a write the parser would act on. `measure_bash_corpus.py` is the measurement tool, run by hand, and the source of every ratio in the guard row above: it reads this machine's session transcripts **read-only** (owner-approved for this run) and emits counts, rates and shape labels — never command text, because those transcripts carry absolute owner paths. ⚠️ **Both files live in `.claude/hooks/` and neither is registered**, so `audit-fleet.py` reports each as "is registered — no settings.json entry runs it": its rule is that every non-`test_` `.py` under `hooks/` is a hook, and a module and a measurement tool are neither. Booked rather than silenced; the fix is to relocate them or to teach the auditor the difference, and it belongs to a later run | `.claude/hooks/bash_write_targets.py` (1693 ln), `.claude/hooks/test_bash_write_targets.py` (734 ln), `.claude/hooks/measure_bash_corpus.py` (272 ln) |
| Commit-attribution guard | live, **added 2026-09-06**, and **verified live the same session** — a `git commit` carrying a Claude co-author was denied in a throwaway repo, then the same commit without it went through authored `njcurtis3`; re-verified after the matcher was tightened. The fleet's **second blocking hook** and the first registered on `Bash`. Denies any real `git commit` whose message carries a Claude co-author, a `Claude-Session:` trailer, a `Generated with [Claude Code]` line, a claude.ai/code link, `noreply@anthropic.com`, or an `--author` that is not the owner; reads a `-F`/`--file` message file as well as the command string, because a message composed with `Write` never appears in the command at all. Applies to **every** `agent_type`, orchestrator included — unlike the plan-scope guard, which is builder-only. **It denied its own documentation within minutes of being written**: the first matcher was `git…commit` on one line, and a heredoc writing the sentence *"denies any `git … commit`"* tripped it. `git` must now sit in a command position with only git's own globals between it and `commit`, and the false positive is pinned by three cases — prose about committing is not committing, and a guard that cannot tell them apart gets routed around instead of obeyed. **Its own first commit message was then denied too**, for enumerating the patterns it blocks — accepted rather than fixed, because tightening the *command* matcher worked (prose about running a command is not running it) and there is no equivalent move for a message (a trailer in a commit message IS prose in a commit message). Write about them without writing them. A `Co-Authored-By:` naming a **human** passes, and so does `git log \| grep -i co-authored`, which is how you audit for the thing. Fails **closed for commits and silent for everything else** — it sees every `Bash` call in the session, so a crash must not block `ls`; the last-ditch branch in `main()` emits the deny without going through `deny()`, since `deny()` is one of the things that can break. 38 subprocess cases | `.claude/settings.json`, `.claude/hooks/guard-commit-trailers.py` (223 ln), `.claude/hooks/test_guard_commit_trailers.py` (234 ln) |
| Run board | live, **added 2026-09-03**, **used by real runs from 2026-09-04**, and since 2026-09-05 it draws a slice that looped. Renders one run's `state.json` + `activity.jsonl` as a ~10-line board: gate, goal, a line per node, a row per slice pairing build with verdict, and the in-flight lane. Authored by nothing — every value is derived, and the placeholder rules are imported from `verify-state.py` rather than restated, so "written" means the same to the board as to the audit. Verified against all 8 runs on disk (diamond, off-plan slices, an untouched template run, a `parked` run, runs with no heartbeat) plus a synthetic mid-flight fixture; ASCII fallback when the console encoding cannot take the glyphs. **Gained `--for <node>[:<slice>]` 2026-09-09** — a per-node brief (goal + that node's plan entry + the scout facts or builder report it needs + prior review attempts) instead of the whole `state.json`, cutting what a node reads on start from ~168KB to a few KB on the runs measured. Every node's read step in `GRAPH.md` §3 and its own `.md` now points here first, `state.json` only for what the brief omits. Manually exercised against `2026-09-06-bash-write-guard` for all six node types plus its two error paths (unknown node, missing slice); **`test_brief.py` was not extended to cover it** — booked, not closed | `graph_agents/.graph/brief.py` (694 ln), `graph_agents/.graph/test_brief.py` (191 ln), `feature-graph` § the board |
| Orchestra fleet sync | live, **added 2026-10-09** (run `2026-10-09-orchestra-fleet-sync`), **exercised once for real**: the first sync wrote 24 files into `orchestra/fleet/` at upstream `506afe9`, left uncommitted for the owner. One-way, stdlib-only, owner-run. Ships the 6 agents, `feature-graph`/`close-run`/`rlm`, `GRAPH.md`, and the core hooks and scripts; **not** `postmortem`, `guard-commit-trailers`, `flag-stale-state`, `flag-cross-app-import`, `verify-invariant`, `audit-fleet`, `new-app`, `fleetview`, run state, registry, conventions or decisions. Umbrella-only spans in the shipped files carry whole-line `umbrella:begin/end` markers (prose and code), replaced from `alternates/` entries **pinned by sha256** — tune a marked span upstream and the next sync refuses until its alternate is re-pinned. `graph_agents` paths become `@FLEET@`. `--verify-upstream 0adbe2a` proves the umbrella copy is byte-identical once markers are stripped. **Leak gate refuses the sync** on owner paths (Windows, MSYS, project slug), username, live registry ids, every sibling directory name and its stems, dated run ids. **Known holes, booked:** undated run slugs and stoplisted stems (`archive`) are not derived as terms — `archive-adapters` reached `orchestra/fleet/` and was caught only by the s4 reviewer's hand sweep; case/space variants of sibling names (`Personal_Archive`) pass; `SOURCE` carries a `-05:00` commit-date offset; a `__pycache__` under the target makes the sync refuse. **Every marker is a standing tax**: an unmarked umbrella concept added upstream makes the next sync refuse | `graph_agents/.graph/orchestra-sync/` (`sync.py`, `test_sync.py`, `payload.json`, `alternates/`) |
| Run board hook | live, **added 2026-09-03**, and **observed rendering in the main tab the same day** — a fresh session, `.graph/CURRENT` pointed at a probe run, one `scout` spawned, board on screen. That closes the delivery half of gap #19: `systemMessage` from a non-display `PostToolUse` event does reach the user. The same test corrected the design: it fires at **dispatch, not at return**. All 32 `Agent` events across the five runs carrying a heartbeat land within 0.2s of a `SubagentStart` and never near a node's own stop, because a spawn call returns a handle and the node runs in the background. So this prints the board a node *picks up*, and the post-return board is the orchestrator's own by hand — no hook can print that one, since the event that fires there is `SubagentStop`. Silent on every other tool, on `SubagentStop`, on a subagent caller, on a closed run and on no open run. Self-tested through 24 subprocess cases against a **copied** fleet in a temp dir rather than by borrowing the live `.graph/CURRENT` | `.claude/settings.json`, `.claude/hooks/show-board.py` (118 ln), `.claude/hooks/test_show_board.py` (160 ln) |
| Node heartbeat | live — `SubagentStart`/`SubagentStop` + a `*`-matcher `PostToolUse` entry append one line per node event to `.graph/runs/<run>/activity.jsonl`. **The append became atomic 2026-09-19** (gap #22): a lock on a sidecar `.lock` file, after a measurement showed a buffered append losing 129 of 600 concurrent events with no torn line to show for it, and `O_APPEND` alone not fixing it on Windows. Verified: events recorded with agent/tool, main-session writes recorded as `orchestrator`, silent on a closed run and with no open run. **Gained `parent` (`parent_tool_use_id`) 2026-09-09**, diagnostic for gap #20: 1,411 of 1,496 recorded `stop` events have no matching `start`, are stamped `orchestrator` for lack of `agent_type`, and interleave with live work — not what "a subagent finished" should look like. `parent` is logged, not yet read; the hypothesis it tests (a phantom nests under a real node's own `tool_use_id` rather than being orphaned) is unverified until a run produces one. **Gained `tokens` 2026-09-11** — a real per-agent-id running total, summed on every `tool`/`stop` event from that specific subagent's own transcript (`~/.claude/projects/<encoded cwd>/<session_id>/subagents/agent-<agent_id>.jsonl`, `message.usage` per turn), not from anything the hook payload itself carries — confirmed against the hooks reference that no usage field exists there at all. A real coupling to an undocumented, internal Claude Code storage layout, accepted deliberately (built for FleetView's per-node token counter) and unwritten on any read/parse failure rather than fabricating a count. **Gained `say` the same day** — the same transcript line's `message.content` text blocks, kept as the newest one seen, collapsed to one line and capped at 220 chars; a snapshot (later write replaces, never accumulates), unlike `tokens`' running total. Built for FleetView's live agent-caption feature; same silent-on-failure rule (`last_said_by` returns `None` rather than a fabricated quote). 28 checks total in `test_record_activity.py` (was 23, then 15): `encode_cwd` against the one observed real mapping, path construction, token summation and last-said-text extraction against synthetic transcripts (real usage/text lines + a torn line + a no-usage/no-text line + one over the 220-char cap), and `main()` end-to-end with `HOME` and `CURRENT` redirected into a temp fleet — an orchestrator-side event (no `agent_id`) and a missing transcript both correctly omit `tokens` and `say` rather than raising or writing a fake value. The transcript shape and location (`agent-<id>.jsonl` under a session's `subagents/`, `message.usage`/`message.content` per line) were confirmed against real files from past sessions on this machine before writing either reader; neither the token nor the caption path has yet fired against a live fleet run, since none was open while this was built. Visually verified in Chrome against a synthetic fleet directory (not a real run): the live caption renders, updates, freezes on the last value seen while live, and correctly shows nothing on a diamond's concurrent same-type builders | `.claude/settings.json`, `.claude/hooks/record-activity.py` (370 ln), `.claude/hooks/test_record_activity.py` (266 ln) |
| Open-run pointer | live, untracked — written by `feature-graph` step 1; read by the scope guard, the heartbeat and the board hook. A pointer to a `done`, `blocked` or **`parked`** run is ignored by all three — `parked` was missing from the heartbeat's and the guard's lists until 2026-09-19, so a pointer left on `2026-08-25-refuge-freshness` would have collected later sessions' events into a stopped run while the board stayed correctly silent. **Nothing clears it**: `close-run.py` now says to, on green and only when the pointer names the run just closed, and still never writes it | `graph_agents/.graph/CURRENT` |
| State-audit hook | live, third `PostToolUse` entry — fires `--audit` on every `Write`/`Edit` of a `state.json`, silent on `_schema.json`, on non-run files, and on a merely half-filled run. **Caught a real defect on first run** (see gap #7) | `.claude/settings.json`, `.claude/hooks/flag-state-gap.py` (131 ln) |
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
| `scout` | haiku | Read, Glob, Grep, Bash, WebSearch, WebFetch | 88 | yes, 34 runs |
| `architect` | opus | Read, Glob, Grep, Bash | 121 | yes, 34 runs |
| `builder` | sonnet | Read, Write, Edit, Glob, Grep, Bash | 103 | yes, 116 slices |
| `reviewer` | opus | Read, Glob, Grep, Bash | 149 | yes, 115 reviews |
| `integrator` | opus | Read, Write, Edit, Glob, Grep, Bash | 62 | yes, 5 runs |
| `ops` | opus | Read, Write, Edit, Glob, Grep, Bash | 84 | **no** |

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

`builder` moved a third time on 2026-09-09, 80→89, and this one was forced rather than
chosen: step 1 said a `PreToolUse` hook denies a `Write`/`Edit` outside the approved set,
which after run `2026-09-06-bash-write-guard` taught a builder the opposite of the truth —
that a Bash write was unwatched. Step 1 and the first **Hard boundaries** bullet now name
`Bash` and, in the same breath, what the guard does **not** catch, so no node is taught to
trust it further than it goes. `GRAPH.md` § 5 and `feature-graph` step 5 carry the same
correction; those three files are the fleet's only prose about that boundary.

`reviewer` moved 79→85 on 2026-09-04 for the same reason, one layer over: `summary` is
specced as "one paragraph a human can read without opening `findings[]`" and the reviews
on disk run to **10,637, 8,497 and 7,980 characters** (`2026-09-01-huntstack-mobile` s4/s3,
`2026-09-02-date-accuracy` s2). Step 4 now carries a hard 1,200-character cap and names
where the overflow belongs — `findings[]` for per-issue detail, one sentence for the
re-run rather than its transcript. Worth noting the field is rendered *twice* side by side
in FleetView's REJECT-then-PASS diff view, so the cost is paid in a narrow column.

Model tiers and tool grants were re-read from frontmatter this pass and are unchanged
since creation. Line counts were re-counted with `wc -l` on 2026-08-26 — three had drifted
(`GRAPH.md` 215→219, `verify-state.py` 125→129, `builder.md` 49→50) because the direct fix
that closed gaps #8–#12 edited those files without re-counting. `scout` and `architect` are
now 3 runs each. Re-counted again after the authorship pass, which added a `written_by`
line to all six node files: `scout` 39→41, `architect` 70→72, `builder` 50→51, `reviewer`
52→54, `integrator` 40→41, `ops` unchanged at 43.

The `integrator` cell read **no** until 2026-09-03, when `/audit-fleet`'s first run
caught it contradicting both gap #2 and the What-is-live row three tables up, each of which
had said since 2026-08-26 that `integrator` ran in `archive-adapters`. One fact, three
copies, and only two of them were updated. The **counts** in that column are deliberately
left unchecked by the auditor — they are explicitly scoped to run 3 below, so a later run
outdates the number without falsifying the claim — but the yes/no is unscoped, load-bearing
and now machine-checked against written keys in every run's `state.json`.

Execution counts run through the end of run `2026-08-25-transclusion-external-previews`:
**6 builder slices** (5 in fleet-hardening + 1 in run 3) and **9 reviews** — fleet-hardening
contributed 7 over 5 slices (`s4` and `s5` each REJECTED once and re-reviewed by a second,
fresh `reviewer`), run 3 contributed 2 over 1 slice (REJECTED once, re-reviewed fresh).
Both runs are closed, so these are final rather than as-of-writing.

Tiering rationale: `GRAPH.md` § Model tiering. Short version — spend on judgment, not
retrieval. `reviewer` and `architect` are never-downgrade. **`builder` moved opus → sonnet
2026-09-09**, on the same argument as the scout downgrade but for a different reason: a
builder executes exactly one slice against a file set and a `done_when` a human already
approved at the gate, so the judgment call happened before it starts, and the
never-downgraded `reviewer` — always a fresh context — exists specifically to catch what
it misses. Not yet run against a live builder spawn as of this pass; the change is
frontmatter-only and the next `single-loop` or diamond run is what actually exercises it.

`builder` also grew 89→91 the same day, for `--for builder:<slice>` (below): step 1 now
names the brief instead of the raw `state.json` read. `architect` 96→97, `reviewer`
97→100, `integrator` 52→55 and `ops` 54→56 moved for the matching change in their own
protocol steps — each now reads its brief first and `state.json` only for what the brief
omits. `GRAPH.md` grew 366→386 for the same contract change written once in §3 rather
than six times.

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

**Since 2026-09-03 the mechanical half of that pass is `/audit-fleet`.** The hook could only
ever nag: it fires on a write, announces this file is stale, and has no way of knowing
whether anyone then checked anything — which is how three closed runs went unrecorded here
for three days. `graph_agents/.graph/audit-fleet.py` re-derives every checkable claim in
this file from disk and reports only what drifted. It does **not** stamp the date, for the
reason in the paragraph above; it earns you the mechanical half of the stamp paragraph and
nothing else. The prose — the gap list, the per-run narratives, the Decisions log — is
still read by a human or by an agent that says which parts it actually re-read.

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
13. **A Bash write is now MOSTLY GUARDED — narrowed 2026-09-09, deliberately not closed.**
    Run `2026-09-06-bash-write-guard`, three sequential slices, `Write|Edit` →
    `Write|Edit|Bash`. A builder's Bash command is classified for write targets and every
    path that resolves is judged against the approved file set by the same matcher a
    `Write` goes through, so `sed -i`, a heredoc, `tee`, `rm`, `cp`, `curl -o` and a
    `python -c` body are denied outside scope where they used to pass unseen — and a write
    shape whose target cannot be resolved is **allowed with a warning**, which leaves a
    record where it cannot leave a denial. The original raising stands as written:
    **raised by a builder itself, unprompted** — `s1-whoop` reported that it had
    deliberately kept using `Edit` *because* a Bash edit would have evaded the guard
    silently. That is still the best evidence the fleet's norms hold.
    **The phrase is "mostly guarded" by the human's own condition at the gate**, and the
    reason is worth keeping: a snapshot that reads *closed* over a boundary that is
    measurably open is worse than the documented hole it replaces. So the limits are a
    list, not an implication. Items 1–9 are the NOT DOING list approved **before** the
    build; 10–16 are what the build and its five reviews then found.
    1. **NOT** catching writes performed by a program the builder invokes: `npm run
       build`, `make`, `bash script.sh`, `pytest`, or a script written to an approved file
       and then executed. **This is the largest hole and it is deliberate** — catching it
       means denying every test command, and a guard that denies `pytest` is switched off
       within a day.
    2. **NOT** catching obfuscated writes: a base64 or `exec` payload inside `python -c`, a
       target assembled by joining runtime variables, `eval` of a variable.
    3. **NOT** catching writes whose target is a shell variable the parser cannot resolve
       within the single command string. These **allow with a warning; they do not deny**.
       The plan estimated 126 of 2070 unique corpus commands (6%); measured against the
       built classifier it is **2.63% — 55 of 2091 when last measured**, inside the 3%
       budget the architect set. The bucket is 24 unassigned variables, 15 `$(...)` or
       backtick substitutions, 7 heredoc-fed interpreters, 5 interpreter bodies and 4
       `xargs` — noise, not a mechanism hiding in it.
    4. **NOT** catching a write by any tool other than `Write`, `Edit` and `Bash`.
       `NotebookEdit` and MCP tools stay unguarded.
    5. **NOT** closing gap #14 (the `scope_exceptions` placeholder parsed as a path) or
       gap #15 (the staleness hook firing in worktrees), even though both live in these
       files and both are tempting.
    6. **NOT** adding caching to `open_run()`. The pre-filter solves the hot path; a state
       cache inside a `PreToolUse` hook is a correctness hazard of its own and needs its
       own run.
    7. **NOT** switching the guard from deny to *ask* for the unresolvable bucket.
       Subagent `ask` behaviour is unverified harness behaviour, and a plan should not
       branch on one.
    8. **NOT** touching the Status headline count or the Runs table in this file. That
       belongs to `/close-run`.
    9. **NOT** writing anything to the session scratchpad during the build — the guard
       lands mid-run and the scratchpad is outside every approved set.
    10. **The pre-filter regex is quadratic below the cap, and the human decided to
        document it rather than fix it.** `MAX_COMMAND` (128KB) is checked *before* the
        pre-filter, so it bounds inputs above 128KB — it does **not** bound the pre-filter.
        Measured: 32,000 semicolons is ~15.1s of pre-filter, at 32KB, well under the cap,
        against the `timeout: 10` the hook is registered with. The decision and its
        reasoning: the approved threat model is a **cooperative population**, an actual
        evader has strictly easier routes already on this list, and rewriting the hot
        regex of a classifier validated by three reviews trades a correctness risk for a
        low-severity stall. What the harness does when a `PreToolUse` hook exceeds its
        timeout is **NOT ESTABLISHED** — two probes were blocked by the safety classifier
        and the builder correctly did not route around them, so this file asserts neither
        deny, nor allow, nor error.
    11. **Partial-quoting and intra-word-backslash spellings leak the pre-filter.** The
        superset property is **anchor-relative, over unquoted, unescaped command-position
        spellings** — a list, not a proof. An independent sweep of 1221 spellings found
        ~90 leaks, every one inside the two families the module already names as missed.
        They fail open: no denial, no record. 0 in the corpus.
    12. **`exec rm -rf build` is not caught** — `exec` is not in the wrapper-verb list,
        while `command rm -rf build` is. Fails open, 0 in the corpus.
    13. **`cd a || echo x > f.md` assumes the `cd` was taken**, so it reports `a/f.md` for
        a write that lands at `f.md`. Deny direction — an approved path can be denied on a
        command that writes it. Same shape behind an `if`. 0 in the corpus.
    14. **The guard's linked-worktree path has no self-test** and is reviewer-verified
        only. This matters more than its size: diamonds run in linked worktrees, and this
        guard once denied *every* builder write in one, undetected, because it had never
        fired there. The Bash branch just doubled the number of callers depending on it.
    15. **The fail-closed trap catches a classifier that breaks, not one that lies.**
        Eleven fault modes — deleted, empty, syntax error, raise-on-import, each symbol
        stripped — were proven to deny and exit 0. A stub returning a well-formed wrong
        answer (`has_write_signature → False`) goes silent, and a `PreToolUse` hook cannot
        tell *this writes nothing* from *I decided not to look*. Inherent to the deny-list
        design, recorded so nobody reads the trap as wider than it is.
    16. **Known debt: `bash_write_targets.py:97` states a measured claim that does not
        reproduce** — "356 commands use this shape and only 57 of them write … 299 false
        positives" could not be reproduced under four independent readings, on any
        denominator. The design conclusion survives and is in fact understated; only the
        pair of numbers is wrong. Byte-identical across all three of that slice's commits,
        so two reviewers passed it before a third caught it. The human decided **not** to
        reopen the slice to correct it, so it is booked here instead of fixed.
    One number this list deliberately does not carry: **a corpus size as a fixed fact.**
    The corpus is live and growing — 2073 → 2078 → 2089 → 2091 across this run's own
    passes — so the ratios and the classifier deltas are the durable figures and an
    absolute count is only ever true on the day it was taken.
14. ~~**`--audit` parses the untouched `scope_exceptions` placeholder as a file path.**~~
    **Closed 2026-09-19**, owner-directed, direct edit. The bug: `approved_paths()` skipped prose
    with a heuristic — a space and no separator — and the `_schema.json` placeholder contains `/`
    (in "Write/Edit"), so it slipped through, became a bogus allowed path and a bogus `rel_map`
    root, and polluted the `Approved:` list a denied builder is shown — the list whose whole job
    is to tell that builder what to do next. Worked around in `archive-adapters` by setting that
    run's `scope_exceptions` to `[]`.
    The general fix is `schema_placeholders()` in `guard-builder-scope.py`: every string in
    `_schema.json`, walked recursively, as a set, and an entry identical to one of them is
    template text rather than a path. **Identity, not a smarter heuristic** — "is this the
    untouched template?" has a correct answer on disk, and `verify-state.py` already answers it
    the same way. A missing or malformed schema returns an empty set, so the old heuristic still
    runs and the worst case is the cosmetic pollution this closed, never a guard that stopped
    guarding.
    **One deliberate loosening, recorded so it is not read later as a regression:** a gated run
    whose plan has no real files and whose only entry is that placeholder used to yield a file set
    of one junk path and deny every builder write. It now yields no file set, which `main()`
    treats as "no opinion" — the same answer an ungated or unplanned run already got. A human gate
    passed over an empty plan is a broken run either way; reporting it as a scope violation was
    the wrong diagnosis. Covered by 5 new cases in `test_guard_builder_scope.py`, including one
    asserting the placeholder really would still slip the prose heuristic, so the rest cannot pass
    vacuously.
15. ~~**The staleness hook fires on app files edited inside a builder worktree.**~~
    **Closed 2026-09-19**, owner-directed, direct edit. Reported twice by `s1-whoop`: every
    fixture edit under `personal-archive`'s worktree returned "you changed the agent
    architecture's definition, `CURRENT-STATE.md` is now STALE". Nothing about the fleet changed.
    The worktrees live under `graph_agents/.graph/worktrees/` only because `repos/` is not a repo,
    and the hook matched on that prefix. Same path-matching class as the guard bug closed in
    `46e0f25`. Noise rather than damage — but it trains agents to ignore a hook that exists to be
    heeded, which is how a real staleness warning gets missed later.
    The fix is one early return on `/.graph/worktrees/`, after the fleet-prefix test.
    **Demonstrated, not assumed:** a copy of the pre-fix hook fed the exact reported payload —
    `.graph/worktrees/2026-08-26-archive-adapters/fixtures/whoop/sleep.json` — still emits the
    stale warning, so the new cases are not vacuous.
    **The deliberate cost:** a builder working on the FLEET from inside a worktree is now silent
    too. That is the right trade — what is true of the fleet is what is on the main tree, and the
    merge back to it fires this hook then.
    This hook had **no tests at all** until now, across 25 days and one rewrite, which is most of
    why this gap lived as long as it did. `test_flag_stale_state.py` (141 ln, 23 checks) now covers
    both drift kinds, the worktree silence, the junction path, `_schema.json` as a definition file,
    the `tool_response.filePath` payload shape, and malformed stdin.
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
    **The delivery half is CLOSED, observed 2026-09-03.** Fresh session, `.graph/CURRENT` pointed
    at a probe run, one `scout` spawned: the board appeared in the main tab, verbatim, under a
    `PostToolUse:Agent says:` label nested beneath the tool call. So `systemMessage` from a
    non-display `PostToolUse` event does reach the user, and the doc sentence that sits next to a
    field description reading "shown to Claude" is the one that governs.
    **And the test corrected the design it was verifying.** The hook was written believing `Agent`
    completes when the subagent it spawned finishes. It does not: across the five runs carrying a
    heartbeat, **all 32 `Agent` events land 0.0–0.2s after a `SubagentStart`**, with the nearest
    real subagent stop between 3.5s and 1772s away — never once the other way round. Subagents run
    in the background and the spawn call returns a handle immediately. The board is therefore a
    **dispatch** board: it shows the run as the node picks it up, before that node has written a
    thing.
    The observed render says the same two things without any arithmetic, which is why it is worth
    keeping verbatim: the harness printed `Backgrounded agent (↓ to manage)` directly above the
    board — the handle-return, stated by the harness itself — and the board's own live lane read
    `now  scout | 0s | 0 tools | last ?`. A node zero seconds old with zero tools spent is a node
    that has not started working. **The board proves its own timing.**
    The consequence is not cosmetic. **No hook prints a board when a node comes back** — the event
    that fires there is `SubagentStop`, ruled out above — so the return board, which is the one
    carrying what the node just did, exists only if the orchestrator runs `brief.py` itself.
    `feature-graph` § the board previously said the opposite ("a node returning prints it for you,
    do not print it again"); that rule was written on the wrong premise and is now inverted. This
    is the second time in three days a claim about what a hook event *means* survived review and
    was only settled by measurement — gap #20 was the first.
    ~~Still open, and the core of it: the headline cap is prose and nothing checks it.~~
    **CLOSED 2026-09-20** by run `2026-09-20-fleet-gaps` s2. `check-return-cap.py` reads the `message`
    argument of a node's own `SubagentHandback` tool_use and counts non-empty lines against the cap of 3.
    It is **report-only by decision** -- not a hook, not a gate -- so the rule is now *measurable*, not yet
    *enforced*; promoting it is a separate decision, deliberately left until it has run against more data.
    **What the first attempt got wrong is the durable lesson**: it read the last `text` block, which is
    post-handback chatter the orchestrator never received, and so reported two compliant returns (3 and 2
    lines) as 4 and 10. A checker whose only failure signal is wrong on its first real data is worse than
    no checker. Its reviewer refuted it by hand-counting the transcripts, and the failure traced to the
    ARCHITECT's spec (`last_said_by`'s definition -- right for a heartbeat caption, wrong for a return),
    with a minor to SCOUT for reporting that the text survives without reporting the SHAPE it survives in.
    **And the run no longer has 'no run has executed under any of this' as an excuse**: 10 nodes ran under
    the board, the briefs and the cap, and the checker's first full outing scored the run that built it at
    **9 compliant, 0 over cap, 1 unverifiable**.

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
    **MEASURED 2026-09-20, and it now has a discriminator -- still open, but no longer undiagnosed.**
    Run `2026-09-20-fleet-gaps` reproduced it live and `postmortem.py` s1 now classifies it: of **52 stop
    events, 3 matched, 0 orphan-with-evidence, 49 phantom**. A phantom is an id with **no `start` and no
    subagent transcript** -- the hook finds nothing at
    `~/.claude/projects/<encoded cwd>/<session_id>/subagents/agent-<id>.jsonl` to read, which is why it
    carries neither `say` nor `tokens`, while every real node stop carries both. That test runs on data the
    fleet already collects. **The `parent` diagnostic added 2026-09-09 is dead and should be removed**:
    `record-activity.py:332` writes it only when the payload has `parent_tool_use_id`, and across a full
    live run of 10 nodes **not one event carried one**. Removing it was deliberately deferred -- that hook
    is what every builder writes through, and editing it mid-run would have corrupted the same run's
    append-lock contention test. What remains unknown is unchanged: whether Claude Code delivers some other
    event under this name, or the fleet misreads the payload.
    `postmortem.py` (added 2026-09-11) is scoped around this rather than blocked on it: it prints
    tool counts and tool-bounded (never stop-bounded) concurrency windows, and no duration
    anywhere. If this gap closes, add duration to `postmortem.py` once, rather than letting a
    second definition of "how long" grow next to `brief.py`'s.
21. **Twelve commits already in history carry Claude attribution, and the guard is
    prospective only.** Booked 2026-09-06, the day `guard-commit-trailers.py` closed the
    forward-looking half. Measured across all 11 sibling repos with `git log --all`:
    `graph_agents` **4** (all 2026-09-05, the review-attempts run), `koenrane.xyz` **7**
    (2026-07-21 to 2026-08-26), `whoop-med-tracker` **1** (its initial commit). Every other
    repo is clean, and **no repo has a commit authored by anyone but the owner** — the
    2026-08-26 re-authoring held; it is only trailers that came back. Cleaning these means
    `filter-repo`/`filter-branch` and a **force-push** on repos with remotes, which is the
    owner's call and not a thing to do unasked. Recorded here so the number is known rather
    than rediscovered: the guard stops the 13th, it cannot unmake the 12.
22. **Every `activity.jsonl` written before 2026-09-19 is lossy, and by an unknown amount.**
    Booked 2026-09-19, the day the forward-looking half was fixed. `record-activity.py` appended
    through a buffered `open(path, "a")`, and in a diamond six nodes fire that hook from six
    processes at once. `2026-09-06-bash-write-guard`'s log carries the proof at line 1225: the
    bare fragment `"Bash"}`, the tail of an event whose head another process's append overwrote.
    **The fix is a lock, not `O_APPEND`, and believing otherwise was the first attempt.** On POSIX
    the seek-to-end and the write are one atomic operation; the Windows CRT emulates `_O_APPEND`
    as a seek followed by a write, and the gap between them is the bug. Measured here, four
    processes × 150 lines: **471 of 600 events survived, with zero torn lines** — the loss is
    invisible to any check that only asks whether each line parses, which is exactly what every
    reader in this fleet does. Now serialised by an advisory lock on a sidecar `.lock` file
    (`flock`, else `msvcrt.locking`) — a sidecar because a Windows lock is mandatory, and locking
    the log itself would make `brief.py` and `postmortem.py` fail to READ it mid-run. After ~1s of
    contention it writes anyway: a line that might collide beats an event that certainly never
    existed, and this hook must never stall a run.
    **What cannot be recovered is how much the old logs already lost.** Nothing counted, the same
    way nothing counted how long the six cwd-relative hooks were dead (gap #18). This matters
    because `activity.jsonl` is the evidence base for `GRAPH.md` § the heartbeat's four claims and
    for everything `postmortem.py` reports: **a tool count read off a pre-2026-09-19 run is a
    floor, not a number.** Gap #20's phantom-stop ratios were measured on those same files.
23. **`feature-graph` step 0.5 asks the wrong question, and a diamond it approves can be unexecutable.**
    Booked 2026-09-20, found by execution rather than by reading. The pre-flight checks
    `git -C <target> rev-parse --is-inside-work-tree` -- true for `graph_agents` -- and on that basis
    approved a diamond. All three `isolation: "worktree"` spawns then failed: **the harness creates the
    worktree relative to the session's LAUNCH DIR (`repos/`), which `CLAUDE.md` deliberately keeps out of
    git**, not relative to the target repo. The check has been wrong since it was written; the only prior
    diamond targeted `personal-archive` and never surfaced it. **Worked around, not fixed**: the owner
    approved builders creating their own worktrees under `.graph/worktrees/<run>/<slice>`, which worked --
    and proved, for the first time, that `guard-builder-scope.py`'s `worktree_context()` maps a FLEET
    worktree correctly (it was built for app repos). The fix belongs in `.claude/skills/feature-graph/`,
    which forces single-loop by step 0.5's own rule 2 and needs a fresh session.
24. **`brief.py` renders `_schema.json` placeholder text as a real prior review attempt.**
    Booked 2026-09-20. `--for builder:<slice>` on a slice with no prior review prints a
    "prior review attempts on this slice (fix what these flagged)" block containing
    `attempt 1: PASS|REJECT` and `[?] ?` -- the untouched schema template, rendered as data. **Every one of
    the six nodes in this run had to be told in its prompt to ignore it**, which is the cost: a brief that
    lies about a slice's history is a brief a node must be briefed about. Same class as gap #14, closed
    2026-09-19 in `guard-builder-scope.py`, and the fix is the same shape -- compare against the schema by
    identity. `brief.py` was in no slice's file set this run.
25. **`postmortem/SKILL.md`'s section table no longer matches `postmortem.py`'s output.**
    Booked 2026-09-20, found by s1's reviewer, who correctly traced it to the architect's file set rather
    than reporting it against the builder. s1 added `## Stop-event integrity`; the skill's table still lists
    the old sections. Not fixable in that run: `.claude/skills/**` forces single-loop and needs a fresh
    session. Small, and exactly the kind of drift that is invisible until someone trusts the table.

26. **`GRAPH.md` § Model tiering asserts a cost ranking the data contradicts.**
    Booked 2026-09-22. §198 of that file already listed tiering as something that "argues cost hard and
    has never measured it" -- that is now measured, from the `tokens` field over `2026-09-20-fleet-gaps`
    (10 spawns, 34.3M tokens, max-per-agent because the field is cumulative): builder **51.4%**, reviewer
    22.1%, scout **17.4%**, architect 5.1%, integrator 3.9%. § Model tiering says scout "is the
    highest-token node in a typical run" and "usually the single biggest lever on a run's total spend."
    It is third, and builders are triple it. **What survives is the reasoning, not the ranking** -- spend
    on judgment not retrieval is still right, and the argument against ever cheapening the reviewer is
    untouched. Only the empirical claim about scout is wrong, and it is the claim the section leans on.
    Three caveats belong in the correction, not a footnote after it: n=1 run; a diamond fans three
    builders against one scout, so the shape flatters builders; and `tokens` counts context *processed*,
    mostly cache reads, not fresh billable input. Needs `.claude`-adjacent editing and a fresh session,
    so it joins #23-#25.

---

## Runs

| Run | App | Shape | Status | Outcome |
|---|---|---|---|---|
| `2026-08-25-refuge-freshness` | huntstack | single-loop | **parked** at human gate | Plan complete, unapproved, no code written |
| `2026-08-25-fleet-hardening` | umbrella (the fleet itself) | single-loop, 5 slices | **executed**, approved at the gate — but its **state file is an incomplete record**: see gap #7 | Fleet got a git repo, a state contract in all 6 nodes, an owner for `branch`, `verify-state.py`, and this snapshot corrected. `reviews.s4`/`s5` still hold attempt 1's `REJECT` and `builders.closing_fix` was never reviewed; found 2026-08-26 by the new state audit, left unedited on purpose |
| `2026-08-25-transclusion-external-previews` | App 1 | single-loop, 1 slice | **executed**, approved at the gate | First product code by this fleet. External-link popovers no longer surface browser frame-block errors. Merged to `main` as `79c3c32` |
| `2026-08-26-archive-adapters` | `personal-archive` | **diamond, 3 slices** | **executed**, approved at the gate. s2/s3 PASS on attempt 1; **s1 took 3 attempts, two REJECTs, both real data leaks** | The fleet's **first diamond**. Three concurrent worktree builders, three independent reviewers, one integrator that resolved both a textual and a **semantic** cross-slice conflict. Merged to `master` (`a5ebed4`), 32 tests green together. Closed gap #3 and the `integrator` half of #2; found gaps #13–#16 and fixed two fleet defects (`46e0f25`, `4cbe78c`) |
| `2026-08-26-invariant-check` | umbrella (the fleet itself) | single-loop, 1 slice | **executed**, approved at the gate, PASS on attempt 1 | Closed gap #5: `verify-invariant.py` + `flag-cross-app-import.py` make the umbrella invariant a live, automated check instead of prose. Committed directly to `graph_agents` `master` (`ae97640`) — no branch, nothing to merge |
| `2026-08-31-mobile-first-criteria` | umbrella (the fleet itself) | single-loop, 3 slices | **executed**, approved at the gate, 3/3 PASS on attempt 1 | Mobile-first became a routing lookup instead of a debate: `conventions/mobile-first.md`, a `ui` field on every registry entry, and matching instructions in `new-app`, `architect`, `builder` and `reviewer`. Forced single-loop by step 0.5 (it edits `.claude/agents` and `.claude/skills`). Merged `dd7ac0b` |
| `2026-09-01-huntstack-mobile` | huntstack | single-loop, 4 slices | **executed**, approved at the gate, 4/4 PASS on attempt 1 | huntstack's React Native + Expo app at `apps/mobile/`, talking to the existing Fastify API over HTTP and sharing no code with `apps/web`. Branch `feat/mobile-expo-scaffold`. Its human-read gate was left open at close and **closed 2026-09-03** on a physical Android phone via Expo Go, against a throwaway stub API — recorded in the run's `log`, never by editing `reviews.s3`. This is the run whose `**`-shaped file sets exposed the guard's glob bug |
| `2026-09-02-date-accuracy` | huntstack | single-loop, 3 slices + 1 off-plan | **executed**, approved at the gate, 4/4 PASS | The UTC off-by-one: season dates now render the calendar day the regulation says, in `packages/shared` and in `apps/web`'s separate local copy, without double-shifting mobile's already-guarded caller. `s4` was added off-plan to run the shared package's tests in CI. Merged `50a5299`, no conflict, no integrator. Closed with `s2`'s human-read gate deliberately **not** run and the close saying so |
| `2026-09-04-fleetview-payload` | fleetview | single-loop, 2 slices | **executed**, approved at the gate, both PASS — **s2 only after the orchestrator overrode a reviewer's PASS** | FleetView items 4 and 5 from an improvement review. `/api/graph` became a conditional request: a strong ETag over the payload minus `generated`, 304 with no body on a match, landing on the nothing-changed path that already existed. The architect **refused the payload split** that was the obvious reading of item 4, because it cannot be built without breaking `fleetview/CLAUDE.md`'s "selection never triggers a refetch" and the test enforcing it; 304 preserves the invariant and also kills the `JSON.parse` + whole-payload `JSON.stringify` the browser ran every 4s on an unchanged poll. Growth with run count is **accepted, not fixed** — revisit at ~40 runs or ~2 MB, starting with that amendment. s2 surfaced `_mtime`, `scope_exceptions` and `written_by`, three fields the fleet had always written and the viewer had never shown. Reviewed PASS at attempt 1 and **sent back anyway**: `ACTIVE_STATUSES` includes `awaiting-approval`, so a run parked at the human gate — both clocks stopped by design — rendered a red *wedged* pill, and the test naming that rule sat on a fixture that could not fail, so deleting the guard left the suite green. Attempt 2 reproduced both mutations red. Suite 61 → 125 assertions. Merged `3e9bb04` and `29537a0`, no conflict, no integrator |
| `2026-09-04-payload-split` | fleetview | single-loop, 3 slices | **executed**, approved at the gate, 3/3 PASS — **s2 on attempt 2 after a REJECT** | The split the previous run's architect refused, authorized by the human after that refusal. `/api/graph` now splits by **depth, not count**: `?runs=light` returns flat rows for every run, `?run=<id>` returns one run's depth, and **no parameters returns the byte-identical full payload**, so an old client sees exactly what it saw before. Measured on master on the live 10-run fleet: 863507 B → 12304 B idle (**98.6%**), **76.3%** with a run selected. 125 → 193 assertions. The client invariant was **amended, not abandoned** — selecting a *node* still never fetches, ever — and s1 landed that amendment as prose *before* any code, then could not be merged alone because it describes the split in the present tense. Merged as one `--no-ff` at the tip, `b261a7f`. Three reviewers were lost to infrastructure (a 429, a second 429, a power loss) before one delivered s3's verdict; none consumed an attempt |
| `2026-09-05-review-attempts` | umbrella (the fleet itself) | single-loop, 5 slices | **executed**, approved at the gate, 5/5 PASS on attempt 1 | Opened because a **close was refused**, not because anyone went looking. A re-reviewed slice keeps attempt 1's `REJECT` at the top of `reviews.<slice>` and nests the fresh verdict as `attempt_2` — a shape two reviewers invented independently, that FleetView already read, and that the fleet **never wrote down**. So `_schema.json` did not define it and `close-run.py`, `brief.py` and *both* of `verify-state.py`'s verdict reads saw only the top level: a slice rejected and then fixed was recorded, and reported, as failed. The scout found the plan-killer — `verify.resolve()` is a dumb dotted walker and `brief.py` did not even use it — so the deliverable became **one shared rule with every caller routed through it**, not four independent edits with four chances to disagree. Cap matches FleetView exactly (`attempt_9`, loud at 10). A rejection stays **visible** after it is fixed: `ever_rejected` is display-only, forever, and the board draws the loop. Fan-in narrowed at the gate from *ever REJECTed* to *latest attempt is REJECT*. Merged `ea53381`. Retired 4 of `fleet-hardening`'s 7 stale blockers and left its 3 real ones standing |
| `2026-09-06-fleetview-followups` | fleetview | single-loop, 2 slices | **executed**, approved at the gate, 2/2 PASS — **`s1` on attempt 2 after a PASS, a correction pass, and a second PASS** | The two follow-ups `2026-09-04-payload-split` carried forward and did not fix. `s2` is the fix: `scopeExceptionsMalformed` now tests the field's **members** as well as its type, returning `""`/`"type"`/`"member"` instead of a boolean, and the panel renders banner-**then**-block instead of banner-**or**-block, so a junk entry no longer suppresses the real grants beside it. The boundary is the whole slice: a list of strings that all fail `isRealPath` is the schema-docstring case and stays **not** malformed — flagging it would have turned healthy runs red on the default screen. Proved twice by mutation (the type-only revert **and** a deliberately broken `isRealPath` boundary, each red on distinct assertions) and once against the real fleet: **0 of 12 runs change their banner decision**. 193 → 212 assertions. `s1` is prose: item A — `collect_activity` reading every `activity.jsonl` in full on every request — is recorded as measured, **accepted and not fixed**, with all four rejected designs and why each is out. Deferred at the gate on the argument that *no design both wins big and keeps an invariant this app already paid for*, not on the size of the win: `os.stat` is 48× cheaper but mtime is not the displayed clock (918s drift on a real run would render a wedged run *fresher* than it is), and a cross-request cache is the server state `CLAUDE.md:32`/`:59` forbid. Revisit at **~40 runs**, reusing the trigger `2026-09-04-fleetview-payload` booked, **archiving first**. `serve.py` byte-identical to baseline, which is what makes that paragraph true. Merged `4787640` and `ed38d7e`, no conflict, no integrator |
| `2026-10-07-native-followups` | umbrella (the fleet itself) | single-loop, 3 slices (**forced**) | **executed**, approved at the gate; s1/s3 PASS on attempt 1, **s2 REJECTed on attempt 1 and PASSed on attempt 2** | Closed the four follow-ups of `2026-10-07-native-app-expertise`: every `responsive-web` condition now says *includes* so array `ui` (huntstack) gets mobile-first; the plan-scope guard reads MSYS `/c/` paths; `scout-facts.py` reports a broken `package.json` once as `unparseable`, never as expo/tauri evidence; `new-app` names `app.json`. s2's REJECT was a **fail-open the plan itself specified** (`base = norm(cwd)` turned a drive-root cwd drive-relative) -- caught by the reviewer by hand, not by the suite |
| `2026-10-09-orchestra-fleet-sync` | umbrella (the fleet itself) | single-loop, 4 slices (**forced**, edits `.claude/agents/**` and `.claude/skills/**`) | **executed**, approved at the gate; **every slice REJECTed once** (s1, s2, s3, s4) and PASSed on re-review; s3 reopened after s4's review and PASSed a third attempt | Built the one-way sync of this fleet into the new `orchestra` app's vendored `fleet/` (see the Orchestra fleet sync row). Four rejections, all real: s1's leak gate missed backslash/MSYS owner paths and unregistered repo names and allowed `../` includes; s2 left registry/`ui` prose that s3 could never mark (architect split prose and code without a pinned CLI contract -- the orchestrator ruled one mid-run); s3's shipped guard mapped a plan's first segment to a repo, killing worktree builds in a single-repo project; s4's landed tree still named `archive-adapters`. Merged to `master` as `76e5cae`, `d3dbd62`, `0fca600`, `506afe9`. The first sync's output in `orchestra/fleet/` is **uncommitted**, for the owner |
| `2026-10-09-orchestra-desktop-mvp` | orchestra | **diamond, 3 slices** (s1 -> s2, s3 parallel) | **executed**, approved at the gate; s2/s3 PASS on attempt 1, **s1 REJECTed on attempt 1 and PASSed on attempt 2** | The fleet's **third diamond** and the first against a product repo since `archive-adapters`. Orchestra's desktop MVP: the app spawns headless `claude -p` stream-json sessions and answers tool permissions, AskUserQuestion and free-text replies over stdin (`--permission-prompt-tool stdio`, settled by s1's live spike against claude 2.1.296); Rust session manager (s2, 27 tests) and React session list + inbox (s3, 10 tests). s1's REJECT was a real leak: the init message's `tools[]` carried the owner's claude.ai connector tool names after `mcp_servers` had been redacted -- amended, never in branch history. The orchestrator created the orchestra worktrees by hand (launched from `repos/`, harness worktree isolation does not target the app repo). Merged to orchestra `main` as `fba4ea1` (s1+s2) and `b38ae28` (s3), full suite plus `tauri build --debug --no-bundle` green; **not pushed**, GUI smoke test not yet done by the owner. Terminal-session hook tracking deferred |
| `2026-10-09-orchestra-review-followups` | orchestra | **diamond, 3 parallel slices** | **executed**, approved at the gate; s3 PASS on attempt 1, **s1 and s2 each REJECTed once, on commit identity only**, PASS on attempt 2 | Fixed the 8 review notes left by `orchestra-desktop-mvp`: per-session Windows Job Object with KILL_ON_JOB_CLOSE (s1), off-main-thread writes, ordered publish, commit-after-write and surfaced unsupported control_requests (s2), reply box and snapshot-merge UI fixes (s3). **Fleet lesson:** the s2 builder ran `git config user.name user.email` meaning to read two keys; git wrote `user.name = user.email` into the app repo's config and both Rust commits were authored under that name. Both reviewers caught it; the orchestrator unset the line and the builders amended `--reset-author` with identical trees. The commit-trailer guard reads the command string (trailers, `--author` naming Claude), not the identity git config resolves to, so it did not fire. The integrator walked the s1/s2 lock seam neither reviewer could see (s2 reviewed against the old reaper). Merged to orchestra `main` as `31657b8`, `64f9f7f`, `2815684`; cargo test 38, npm test 16, tauri debug build green; **not pushed**; owner manual checks M1/M2/M4/M6 pending |
| `2026-10-10-orchestra-d1-closeout` | orchestra | **single-loop, 4 slices on one branch** | **executed**, approved at the gate; all four slices PASS on attempt 1 (s2 high-risk, 3 notes) | ROADMAP D1 close-out of the desktop MVP: `stop_session` on the blocking pool (s1); a sticky `needs_attention` status for unsupported control_requests, end to end with `LIVE` as `Record<SessionStatus, boolean>` so tsc catches a missing status (s2); the spawn-to-job-assign race and stdio pipe inheritance documented rather than closed with CREATE_SUSPENDED, revisit at rust#96723 (s3); stale README/CLAUDE.md lines (s4). **Fleet lessons:** (1) `guard-builder-scope.py` matched the plan path `ipc.test.ts (new)` literally and denied the bare path, so the orchestrator added a scope exception for a file the human had approved; (2) `close-run.py` blocked on `s3-alt`, a gate-declined alternative still in `architect.plan`, until the architect moved it to `architect.alternatives_not_chosen`. Merged to orchestra `main` as `3880f1a`; cargo test 44, npm test 18; owner manual checks M1/M2/M4/M6 still pending |
| `2026-10-10-orchestra-d2-persistence` | orchestra | **single-loop, 5 slices on one branch** (shared state.rs/mod.rs/lib.rs ruled out a diamond) | **executed**, approved at the gate with all 7 decisions as recommended; all five slices PASS on attempt 1 | ROADMAP D2, sessions survive a restart: `suspended`/Paused status, expired inbox items and full result text (s1); versioned atomic snapshot in app_data_dir with a revision-ordered writer and a quit path that saves Paused before killing children, so a clean quit no longer records Failed (s2); lazy `--resume` on reply with a UUID-checked id (s3); window-state plugin plus an own visible-display check (s4); docs (s5). The s3 reviewer probed real claude 2.1.296 to confirm an unknown resume id gives is_error:true and exit 1. **Fleet lessons:** the architect listed bare paths and kept gate options out of `plan`, and both D1 tooling gaps stayed quiet; the architect accidentally ran a stale D1 script left in the shared scratchpad, which overwrote its own key before it rewrote it. Merged to orchestra `main` as `329e93c`; cargo test 67, npm test 25; owner GUI checks pending |
| `2026-10-14-orchestra-d4-tasks-worktrees` | orchestra | **single-loop, 5 slices on one branch** (session/mod.rs, lib.rs, commands.rs and git.rs each shared by 2-3 slices) | **executed**, approved at the gate with all 11 decisions as recommended plus an orchestrator-proposed amendment (land refuses Claude-attributed task commits); s3/s5 PASS on attempt 1, **s1 and s2 on attempt 2, s4 on attempt 3** (owner-authorized past the cap) | ROADMAP D4: git runner with typed refs and a containment check (s1); wait_exit/stop_and_wait covering grandchildren via the job object, plus an on-machine probe (s2); Task entity, schema 2, queue of 2 in per-task worktrees under app_data_dir (s3); diff, land (--no-ff onto the recorded base, clean-checkout and attribution refusals that keep the session resumable) and discard with link-safe cleanup (s4); tasks UI with confirms and plain-text diff (s5). **Measured on this machine:** `git worktree remove` while a child holds the folder half-removes it (checkout deleted, worktree unregistered, empty dir left); `git worktree remove --force` **follows NTFS junctions** and deleted a canary outside the worktree — found when a reviewer's own probe emptied the real `node_modules` (restored with `npm ci`). **Fleet lessons:** parallel reviewers on one checkout must not link shared dirs into probe worktrees; a builder's commit message claimed a fail-closed check that did not exist, caught by the attempt-2 reviewer and confirmed by grep — the attempt-3 reviewer was briefed to verify every claim against code. Merged `--no-ff` to orchestra `main` as `7e62149`; cargo test 191, npm test 58; not pushed; owner GUI checks pending |
| `2026-10-16-orchestra-p1-a0-h0` | orchestra | **diamond, 3 parallel slices** in linked worktrees under a short path (`C:/Users/natha/wt/`), one run for three ROADMAP milestones because `.graph/CURRENT` names one run and the scope guard reads only that run | **executed**, approved at the gate with the P1 link decision (8 items) and the H0/A0 decisions as recommended; s1 and s3 PASS on attempt 1, **s2 REJECTed once** (jest packages in `dependencies`; the 48dp touch floor was overridable) and PASSed on attempt 2; integrator merged s3, s2, s1 with 0 conflicts | P1: the client<->host link contract in `protocol/README.md` (s1); A0: Expo starter replaced by the real mobile shell with jest-expo and expo-dev-client (s2); H0: the Rust core split into `orchestra-core` under a root Cargo workspace, 19 pure renames, 181 core + 10 shell tests (s3). **Fleet lessons:** orchestra's repo-local git config had `user.name = user.email` (source untraced; the classic `git config user.name user.email` slip) and one s3 commit took that name before it was caught, fixed and re-authored; `git worktree remove` fails with Filename too long on worktrees holding `node_modules`/cargo targets, so worktrees went under a short path and leftovers were removed only after a reparse-point check. Merged `--no-ff` to orchestra `main` as `3422e61`; cargo test --workspace 191, desktop npm 58, mobile 5 tests + expo-doctor 21/21; not pushed |
| `2026-10-17-orchestra-p2-protocol-v1` | orchestra | **single-loop, 4 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/op2`); the architect declined a diamond because a Rust/serde misfit would land back in s1's fixtures | **executed**, approved at the gate with G1-G7, S1, S2 as recommended plus one orchestrator amendment (gitignored `ROADMAP.md` dropped from s4: a worktree cannot see it); all 4 slices PASS on attempt 1, three fresh reviewers in parallel (s1 high, s2 high, s3+s4 low); no integrator | P2: protocol v1 as TS source of truth in `protocol/`, Rust copy `orchestra_core::wire`, 87 shared JSON fixtures checked by cargo, desktop vitest and mobile jest; IPC arg structs moved into core with `deny_unknown_fields` intact. **Fleet lesson:** two concurrent reviewers each truncated `state.json` (`json.dump(..., ensure_ascii=False)` in `w` mode hit a lone surrogate in finding text; the second empty-write came seconds after the orchestrator's first restore). Restored twice by the orchestrator from the intact prefix, both reviewers then rewrote their own keys via a scratch file + `cat`; node-written log lines after the architect's were lost. Read-only reviewers writing `state.json` by script is unguarded. Merged `--no-ff` to orchestra `main` as `9d8f98f`; cargo 181+4+10, desktop vitest 153, mobile jest 94, expo-doctor 21/21; pushed |
| `2026-10-17-orchestra-p2-followups` | orchestra | **single-loop, 2 sequential slices** on one branch in a linked worktree | **executed**, approved at the gate with D1-D4 as recommended; both slices PASS on attempt 1, two fresh reviewers in parallel (s1 high, s2 low), each running the planned mutations (M1-M8, R1-R4) themselves; no integrator | P2 review follow-ups: unknown transcript entry kinds tolerated on the client, fixtures locking v-first order and the non-ASCII call.id byte cap, `utf8Length` and `__proto__` fixes, a `wire_fixtures` count that can fail (99 fixtures). **Fleet lessons:** the builder was denied by the scope guard because the plan named 12 new files as a free-text string inside `files`, not as paths; the orchestrator added exactly those 12 to `scope_exceptions`. Every node wrote `state.json` once via a validated scratch file + `cat`, and there was no corruption. Merged `--no-ff` to orchestra `main` as `5efc224`; not pushed |
| `2026-10-17-orchestra-h1-linux` | orchestra | **single-loop, 5 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/oh1`) | **executed**, approved at the gate with G1-G7 as recommended plus the ROADMAP amendment; first push blocked until the owner added the gh `workflow` scope; CI red once (a test hook lacked the exec bit on Linux), fixed in-slice; 3 of 4 approved pushes of the branch only; all 5 slices PASS on attempt 1, three fresh reviewers in parallel (s1 high, s4 high, s2+s3+s5 low) reading the real CI logs; no integrator | H1: Linux parity for the core (process-group kill with PDEATHSIG via a spawner thread, symlink link guards on Unix, an XDG state-dir resolver, `test.yml` CI on Linux x86_64/arm64, Windows, both front ends and a macOS check); merged to orchestra `main` (`e84d179`). **Fleet lessons:** Linux behaviour on a Windows-only box is provable only through CI, so the gate must authorize a branch push; a reviewer briefed read-only still ran `git checkout` in the worktree (restored, recorded) |
| `2026-10-17-orchestra-p3-host-link` | orchestra | **single-loop, 4 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/op3`); the architect split P3 at the gate into P3a (core) and P3b (desktop) | **executed**, approved at the gate with G1-G13 as recommended plus G14 (bounded branch push); 4 fresh reviewers in parallel (s1, s2, s3 high; s4 low); **s3 REJECT on attempt 1** (the bind validator let the IPv4-mapped unspecified address through, which binds INADDR_ANY on Linux), fixed in one commit, **PASS on attempt 2** with a fresh reviewer; a builder push hung on a credential prompt and the owner had the orchestrator push; no integrator | P3a: the host side of the link in `orchestra-core`: seq'd event fan-out and atomic subscribe, wire dispatch moved out of the shell, a Noise IKpsk2/KK server over blocking tungstenite with pairing, scopes and revocation, 26 loopback integration tests; merged to orchestra `main` (`edaca7e`). **Fleet lessons:** an adversarial reviewer writing an independent client from the README alone is what proves a self-tested crypto link; a canonicalisation miss in an address check passed every test the builder wrote |
| `2026-10-18-orchestra-p3b-desktop-pairing` | orchestra | **single-loop, 4 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/op3b`) | **executed**, approved at the gate with G1-G14 as recommended plus G15 (bounded branch push); all 4 slices PASS on attempt 1, four fresh reviewers in parallel (s1, s2, s3 high; s4 low); 2 of 4 pushes, no credential hang (pushes now run with GIT_TERMINAL_PROMPT=0 and a 90 s timeout); no integrator | P3b: the desktop side of the link (Credential Manager host key via windows-sys, `link/config.json` with auto-start, QR drawn in Rust so the secret never reaches the webview as text, confirm dialog, Devices view, CSP pin) plus three P3a core follow-ups; merged to orchestra `main` (`806c4c3`). **Fleet lessons:** with no component-test infrastructure, a high-risk UI slice rests on the reviewer's reading plus an owner hand test, so the hand test is a gate item, not a footnote |
| `2026-10-18-orchestra-p3b-followups` | orchestra | **single-loop, 2 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/op3f`) | **executed**, approved at the gate with F1-F5 plus F6 (bounded branch push); both slices PASS on attempt 1 (s1 low, s2 high); the builder's push and one retry hung on a Git Credential Manager account picker, fixed when the owner had pushes use njcurtis3 explicitly, and push 3 of 4 landed | The three medium findings from P3b's review: an out-of-range port on disk is a start error with the settings left editable (s1, `link_config::port_error`); the startup link snapshot never overwrites a newer status, and both pairing dialogs trap Tab, inert the background and restore focus (s2, `focus.ts`). CI 6/6 green; merged `4948a58`. Four review notes recorded, none blocking |
| `2026-10-18-orchestra-a1-pair-and-see` | orchestra | **single-loop, 5 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/orchestra-a1`); reviewers ran in detached per-commit worktrees so builds and reviews overlapped | **executed**, approved at the gate with G1-G13 as recommended plus G14 (bounded branch push); s1, s2, s5 PASS on attempt 1, **s3 and s4 PASS on attempt 2 after a REJECT each**; two small post-PASS follow-ups (s1 README, s5 Back) each reviewed; one s3-fix builder stalled on the stream watchdog and a fresh builder resumed its uncommitted draft; 1 of 4 pushes | ROADMAP A1, the phone pairs and sees: deterministic Noise IKpsk2/KK vectors generated by a cfg(test) core module with a drift guard (s1); a hand-written initiator-only Noise and framing over noble 2.4.0 replaying them byte for byte, tsc added to mobile CI (s2); camera/crypto/network/build-properties deps, cleartext on, RECORD_AUDIO removed, QR offer parser, secure-store host store (s3); link client, reducer and controller against a fake host (s4); home, pair and session screens (s5). The reviewer-caught bugs: expo-crypto `getRandomBytes` falls back to Math.random in dev bundles on bridgeless RN (the Expo Go path), and dispose during pair left a reconnecting controller. CI 6/6 green; merged `37537f1` |
| `2026-10-20-orchestra-a1-followups` | orchestra | **single-loop, 4 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/oa1f`), reviewers in detached per-commit worktrees | **executed**, approved at the gate with F1-F9 as recommended; all 4 slices PASS on attempt 1, plus one reviewed s3 follow-up; two reviewers stalled on the stream watchdog with nothing written and were re-run fresh; 1 of 4 pushes | The A1 review follow-ups: the dispose test now goes live over /link and pins the attempt guard by mutation (s1); restart loads the most recently paired host, cancel during re-pair restores the previous record, a damaged host index is salvaged (s2); a used or closed pairing code reads as closed on a phone, matched on OkHttp's upgrade text, and a drop after msg1 names both causes (s3); the test handshake shares the production builder setup (s4). CI 6/6 green; merged `e6f56ab` |
| `2026-10-20-orchestra-a2-answer` | orchestra | **single-loop, 4 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/oa2`), reviewers in detached per-commit worktrees | **executed**, approved at the gate with A2-G1..G16 as recommended; s1, s2, s4 PASS on attempt 1, **s3 PASS on attempt 2 after a REJECT**; four reviewed post-PASS follow-ups (two README, one s2 outbox fix); the architect wrote app-relative file paths, so the scope guard matched nothing until the orchestrator listed the same files umbrella-relative in `scope_exceptions`; one builder key lost to a concurrent state.json write and re-written by its builder; 1 of 4 pushes | ROADMAP A2, answer from the phone. The scout caught an A1 bug: the host's inbox-updated carries one session's inbox, but the phone replaced the whole list (s1 records it, s2 fixes it). An in-memory outbox with call-id routing, reconcile on snapshot and inbox-updated, and Cancel on unconfirmed and failed (a reviewer found a cached host `failed` could hold an answer unconfirmed forever) (s2); Needs you list and permission and question screens (s3); the desktop refuses question answers over the host's 4096-byte cap (s4). CI 6/6 green; merged `b6dd32f` |
| `2026-10-22-orchestra-a3-notifications` | orchestra | **single-loop, 3 sequential slices** on one branch in a linked worktree (`C:/Users/natha/wt/oa3`), reviewers in detached per-commit worktrees | **executed**; the owner chose before planning that alerts arrive only while the app is open or recently used (no foreground service; asleep-phone push stays with PR3), then approved the plan as is; s1 PASS on attempt 1, **s2 and s3 PASS on attempt 2 after a REJECT each**; three plan gaps went through `scope_exceptions` (prebuild's generated `android/`, and `os.ts` plus `os.test.ts` for s3's tap wrappers); the s1 builder ran `expo install --fix` and bumped four unplanned packages, which the orchestrator sent back to revert; the architect keyed plan entries `id` instead of `slice` and re-wrote its own key when the board showed 0 slices | ROADMAP A3, notifications. expo-notifications and POST_NOTIFICATIONS with RECORD_AUDIO still blocked (s1); alerts only for items new since the connection's snapshot, payload data `{id, kind}`, one file imports the library, and a reviewer caught that Android 8-12 would post on expo's fallback channel and show contents on a secure lock screen (s2); tap routing and a home Alerts card with rationale first and denied paths, and a reviewer caught a warm tap re-routed on remount (s3). Mobile 437 tests; merged `97179a0` |
| `2026-10-10-orchestra-d3-notify-detail` | orchestra | **single-loop, 5 slices on one branch** (session/mod.rs is the hub every slice touched) | **executed**, approved at the gate with all 7 decisions as recommended; s1/s2/s5 PASS on attempt 1, **s4 PASS on attempt 2 and s3 on attempt 3** after an owner-ordered fix round (attempt 2 REJECTed on a torn tail cut inside a multi-byte UTF-8 character; the third attempt was owner-authorized past the 2-attempt cap) | ROADMAP D3: inbox events carry only the changed session and text-only lines skip the snapshot (s1); per-session model and permission mode from a Rust allowlist, re-passed on resume (s2); per-session transcripts on disk outside the snapshot, read as bytes with lossy decoding so a torn tail cannot reset numbering or hide history (s3); OS notifications on needs-input/finish/fail (s5); session detail view with transcript, cost and follow-up prompts, keyed by session id (s4). A paid probe confirmed all four permission modes still emit can_use_tool. **Fleet lesson:** the "notes, not blockers" from attempt-1 reviewers were worth a fix round — one of them hid a second, worse bug that only a fresh reviewer found. Merged `--no-ff` to orchestra `main` as `7e62e10`, pushed 2026-10-14; cargo test 108, npm test 41; owner GUI checks pending (Windows toasts need an installed build) |
| `2026-10-07-native-app-expertise` | umbrella (the fleet itself) | single-loop, 4 slices (**forced**, edits `.claude/agents/**` and `.claude/skills/**`) | **executed**, approved at the gate; s3/s4 PASS on attempt 1, **s1 and s2 each REJECTed on attempt 1 and PASSed on attempt 2** | Primed the fleet for native apps: `decisions/0003-native-stack.md` (Expo + EAS for mobile, Tauri 2 for desktop, no Mac so iOS on EAS and macOS on a GitHub Actions runner), `conventions/native-mobile.md` and `native-desktop.md`, new `ui` values `native-mobile`/`native-desktop` (and `ui` may be an array), gated native rules in five agents, native scaffolding in `new-app`, Expo/Tauri detection in `scout-facts.py`. huntstack's `ui` became `["responsive-web","native-mobile"]` (registry untracked, on disk only). s1 REJECT: an `appVersion` runtimeVersion policy with no version-bump rule would OTA to binaries lacking a new native module. s2 REJECT: an amended skip line cancelled mobile-first for array `ui` |
| `2026-09-20-fleet-gaps` | umbrella (the fleet itself) | **diamond, 3 slices** | **executed**, approved at the gate; s1/s3 PASS on attempt 1, **s2 REJECTed on attempt 1 and PASSed on attempt 2** | The fleet's **second diamond**, and the first run since 2026-09-06. Closed gap #19's open core (`check-return-cap.py`) and gave gap #20 its first measurement (52 stops: 3 matched, 0 orphan-with-evidence, 49 phantom). `audit-fleet.py` stopped reporting the five deregistered siblings. Three builders in three worktrees wrote one `activity.jsonl` concurrently with no torn or lost line -- the 2026-09-19 append lock's first contention test. Also the first run to exercise `--for` briefs, the sonnet builder, `tokens`/`say`, and all four 2026-09-19 fixes. Produced three new findings of its own (step 0.5's wrong question, `brief.py`'s placeholder rendering, `postmortem/SKILL.md` stale) |
| `2026-09-06-bash-write-guard` | umbrella (the fleet itself) | single-loop, 3 slices | **executed**, approved at the gate, 3/3 PASS — **`s1` on attempt 3 after a REJECT, `s2` on attempt 2** | Closed gap #13 to **mostly guarded**, by explicit human condition it is not fully closed. `s1`: `bash_write_targets.py`, a standalone classifier resolving a Bash command string to write targets (redirects, heredocs, `tee`, `sed -i`, `rm`, `cp`, `mv`, `install`, `dd`, `truncate`, `ln`, `git checkout/restore/apply`, `curl -o`, inspected `python -c`/`node -e` bodies) plus an unresolved-write-shape flag, opinion-free — it returns paths, the guard judges them. `s2`: wired into `guard-builder-scope.py` as a `Bash` branch sharing the existing `_match()`/`approved_paths()`, so the guard fails closed on a broken classifier and warns rather than denies on an unresolvable target (2.63% of the corpus). `s3`: made `builder.md`, `GRAPH.md` §5 and `feature-graph` step 5 honest about what the Bash half does and does not catch. Merged `--no-ff` to `graph_agents` `master` as `3751ddf`, 10 files, 3539 insertions; pushed to origin 2026-09-09. Booked, not fixed: `audit-fleet.py` false-positives `bash_write_targets.py`/`measure_bash_corpus.py` as unregistered hooks (they are a module and a measurement tool, not hooks) |

Run state lives at `graph_agents/.graph/runs/<run-id>/state.json` for each of the fifteen.

The per-run `what happened` narratives moved to **`graph_agents/HISTORY.md`**
on 2026-09-22 — they are append-only and never revised, and they carried 9% of this
file's weight. The table above is the checked record; `HISTORY.md` is the prose behind it.

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-08-25 | Holding company, not monorepo — each app its own git repo | Shared packages turn N sellable products into one distributed monolith |
| 2026-09-22 | **No enforcement point in the fleet may be probabilistic, and no hook may depend on a network call** (ADR 0001, prompted by Jev) | Two separate claims that happened to be settled by one question. The first is `guard-commit-trailers.py`'s whole origin story read forwards: the attribution rule was a judgment, the judgment failed, two repos had their history rewritten on 2026-08-26, and the fix was to replace the judgment with a check. A calibrated probability is a judgment wearing a number, so substituting one at any guard runs that lesson backwards. The second is narrower and unconditional: a `PreToolUse` guard that calls out to a remote service has exactly two behaviours when the call fails, and both are unacceptable — allow the write (the boundary is silently gone) or deny every write (the fleet stops working offline). Holds for any vendor, not just this one |
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
| 2026-09-03 | **The fleet auditor checks claims and never stamps the date** | `/audit-fleet` exists because "stale entries are worse than missing ones" was enforced by a hook that can only nag: it announces the obligation and cannot tell whether anyone discharged it. The obvious next step — have the script bump `Last verified:` once it goes green — is refused, because it would assert a verification that never happened for every prose claim in the file, which is the exact failure the header warns about. This does not overturn the 2026-08-25 do-not-revisit ruling; it is that ruling applied to a second tool |
| 2026-09-03 | **The auditor checks the unscoped half of a claim and reports the scoped half as evidence** | The roster's "Has executed?" column carries two claims in one cell. The yes/no is unscoped and load-bearing — gap #2 is entirely a statement about which nodes have never run — so it is machine-checked against written keys. The count beside it is explicitly scoped ("through the end of run 3"), so a later run outdates the number without making the claim false; checking it would report correct prose as drift, and a checker that cries wolf gets ignored, which is how the six dead hooks of gap #18 stayed dead |
| 2026-09-03 | **Node execution is counted from `state.json`, never from `activity.jsonl`** | The heartbeat looks like the natural source and is not: gap #20 says 471 of 503 recorded stop events are phantoms carrying an `agent_id` that never started. A written key is the fleet's own definition of a node having run, and `verify-state.py` owns what "written" means — imported rather than restated, so the auditor and the audit cannot drift into two definitions |
| 2026-09-03 | **The close is checked by a script, and written by the orchestrator — never both by one actor** | `close-run.py` follows `verify-state.py`'s contract exactly: it decides and prints, it does not write. A script that set `status: done` and appended the closing `log` entry itself would be doing to the orchestrator's keys what `written_by` was added to stop a node doing to another's. The check is mechanical; the close is an act with an author |
| 2026-09-03 | **A merge is proved against git, never against `state.json`** | The first three close checks read the state file, and a state file cannot know whether a merge happened — a run whose slices all say PASS and whose branch never landed passes every existing check and is not done. So each slice's branch, or its recorded commit for a branch since deleted, must be an ancestor of the target's HEAD. Degraded shapes (no repo, direct commit, no branch) are notes, not blockers, because `feature-graph` step 0.5 describes them as legitimate |
| 2026-09-03 | **The board is delivered from `PostToolUse`/`Agent`, never from `SubagentStop`** | `SubagentStop` is a *display event*: the docs put both its stdout and its `systemMessage` into Claude's context "instead of being shown in the transcript", so a board emitted there reaches the orchestrator — which already knows — and never the human. The fleet's own heartbeat gives the second reason: 471 of 503 stop events are phantoms (gap #20), so the event is not even a reliable "a node finished" signal here. `Agent` `PostToolUse` is non-display, so `systemMessage` surfaces — **verified by observation 2026-09-03**. *Corrected the same day: this entry originally said "exactly one per node return". It is one per node* ***dispatch*** — see the row below |
| 2026-09-03 | **Two boards per node, from two actors: the hook prints at dispatch, the orchestrator prints at return** | Measured, after the assumption behind the hook turned out to be wrong: all 32 `Agent` events in the heartbeat land within 0.2s of a `SubagentStart`, never near a node's own stop, because a spawn call returns a handle and the node runs in the background. Nothing can be done about that — the only event at a node's return is `SubagentStop`, which cannot address a human — so rather than lose the board that matters, the two are split by actor. The hook's dispatch board is free and shows what the node is picking up; the orchestrator's return board is manual and shows what it did. The rule that said "a node returning prints it for you, do not print it again" was written on the wrong premise and is inverted |
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
| 2026-09-09 | **A changed `settings.json` matcher takes effect MID-SESSION — so a hook change is sequenced LAST in a run.** New fleet fact, measured rather than assumed: scout searched and found it recorded nowhere | The `s2` builder of `2026-09-06-bash-write-guard` wrote `Write\|Edit\|Bash` into `settings.json` and its *own* next Bash calls were guarded, with no restart and no re-registration. Corroborated by its reviewer — the pasted deny/warn text is byte-for-byte the string that commit's hook ships — but **not independently reproduced**, because the guard exempts every non-`builder` agent, so a reviewer's own calls stay silent whichever matcher is loaded. Recorded at that width: observed once, live, not a harness guarantee. The consequence is the rule: the switch goes live under the feet of whoever throws it, so a slice that changes a matcher must be the last thing a run does, and everything that has to be written *around* the new boundary is written before the flip. `feature-graph` step 0.5 already says to start a fresh session before the next run; this says the change bites before that session ever starts |
| 2026-09-09 | **Gap #13 closes to "mostly guarded", never to "closed"** | Human's own condition at the step-4 gate, and the 9-item NOT DOING list was approved as the literal content of the new gap text. A deny-list over command strings cannot be complete — it fails open on an invoked program, on obfuscation, and on a target assembled at runtime — and a snapshot that reads *closed* over a boundary measurably 2.63% open is worse than the documented hole it replaced. The same rule governed the run's own numbers: five figures were corrected mid-run, and each correction was recorded rather than the earlier number quietly kept |
| 2026-09-11 | **A router is scoped around an open gap, not blocked on it — and never re-derives a metric a sibling tool already owns** | `/postmortem` was the one router of the 2026-09-03 brainstorm's three deliberately left unbuilt, because it reads `activity.jsonl` and gap #20 makes duration unsound. Building it anyway meant drawing the line explicitly: tool counts and tool-bounded (`start`/`tool`, never `stop`) windows are sound and go in; any `start`/`stop`-pair duration does not, full stop, until the gap closes. If it closes, duration is added to this script once — never computed a second, independent way that could quietly disagree with `brief.py`'s |

---

## Changelog

Moved to **`graph_agents/HISTORY.md`** on 2026-09-22. It was 77 lines but 22% of this
file by weight — the single heaviest section — and every row in it describes something
that already happened and will not change. Append new rows there.
