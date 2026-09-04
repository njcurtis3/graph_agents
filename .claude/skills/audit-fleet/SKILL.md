---
name: audit-fleet
description: Re-verify CURRENT-STATE.md against disk and fix what drifted — line counts, registry ids, run statuses, node execution claims, hook registrations, and whether the Last verified stamp still covers the fleet. Use when the staleness hook fires, before stamping a new Last verified date, at the end of any session that changed fleet definition files, and when asked to "audit the fleet" or "check if CURRENT-STATE is still true".
---

# audit-fleet

`CURRENT-STATE.md` is what every other doc and every fresh session trusts. On 2026-08-26 it
still said "no agent in this fleet has written a line of product code yet" — eleven hours
after one had, and nobody noticed. Its own rule says stale entries are worse than missing
ones, and the machinery behind that rule is a hook that can only **nag**: it fires on a
write, announces the snapshot is stale, and has no idea whether anyone then checked
anything.

This skill is the other half. The hook creates the obligation; this discharges it.

## Step 1 — diff the doc against disk

```bash
python graph_agents/.graph/audit-fleet.py         # drift only
python graph_agents/.graph/audit-fleet.py -v      # every claim it checked
```

Exit 0 means every checkable claim agrees with disk. Exit 1 lists each one that does not.

It checks nine families, all mechanically:

| Family | Against |
|---|---|
| `(N ln)` claims, anywhere in the doc | `wc -l` |
| roster model, tool grant, line count | each agent's own frontmatter |
| roster **has it ever executed** | a written key in some run's `state.json` |
| app / node / skill counts | directories on disk |
| registered apps | the directory, its own `.git`, its entry docs |
| the Runs table | the run directories and their `status` |
| the Status headline's run count | run directories |
| fleet branch and remote | `git` |
| hook commands and hook files | `settings.json` both ways |
| `Last verified:` | commit dates of fleet definition files |

## Step 2 — on drift, re-verify before you rewrite

Each class has one right response, and none of them is editing the number to match:

| Drift | What it means |
|---|---|
| a line count moved | a file changed and the snapshot did not. Re-measure, then ask whether the *description* of that row also went stale |
| a claimed path is gone | something was renamed or deleted. The row may need removing, not correcting |
| a node's execution claim is wrong | gap #2 is a claim about which nodes have never run. Fix the roster **and** the gap entry — they are two copies of one fact |
| a closed run is missing from the Runs table | this is the 2026-08-26 failure repeating. That run did something; the Status line, the Runs table and the Changelog all have to learn about it |
| the table contradicts a run's own `status` | the run file is authoritative about itself. Fix the table |
| a registered app has no directory or no repo | the registry is the routing index. A wrong entry sends the whole fleet somewhere that does not exist |
| an unregistered hook file | a script that looks live and runs never — the silence of gap #18. Register it or delete it |
| the stamp does not cover a definition file | exactly what this skill is for: read those files and re-verify the rows they affect |

Unregistered **sibling directories** print as a note, never drift. Four of them are
deliberate deregistrations, and nothing on disk records the difference between "left out on
purpose" and "forgotten".

## Step 3 — fix the doc, then re-run to green

Edit `CURRENT-STATE.md`, then run the checker again. A drift you *explained* rather than
fixed is still drift.

Then, and only then, set `Last verified:` to today and add the pass to the stamp paragraph
saying what you actually re-checked — including what you did **not**. That paragraph is the
honest part; the checker only earns you the mechanical half of it.

**The script will never write that date, and must not be made to.** A bot bumping
`Last verified:` asserts a verification that never happened, which is the exact failure the
header warns about — Decisions log, 2026-08-25, marked *user-confirmed, do not revisit*.

## What this skill is not

- **Not a proof the file is true.** Every narrative claim — the gap list's reasoning, the
  per-run "what happened" sections, the Decisions log — is prose about judgment, and no
  script has an opinion about it. A clean run means *the checkable claims agree*.
- **Not a substitute for reading what changed.** If the stamp check names three files, read
  those three files. The checker knows their line counts moved; it does not know whether
  what they now *do* matches what the doc says they do.
- **Not a run.** No `state.json`, no gate, no slices. It is a checker, like
  `verify-state.py` and `close-run.py`, and it never writes anything.

Fixing what it finds is usually a direct edit. If the fix turns into real work across
several files, that is `/feature-graph` against the umbrella, and the stop-rule in
`feature-graph` step 0 decides — not this skill.
