# ADR 0002 — Recursive Language Models: a reading tool, never a judge

**Date:** 2026-10-06
**Status:** Accepted
**Scope:** `graph_agents/` only.

## The decision

The fleet adopts the Recursive Language Model pattern (Zhang, Kraska & Khattab,
arXiv:2512.24601) as **one tool and one skill** — `.graph/rlm.py` and `/rlm` — for
reading inputs too large to hold in context. It is wired into `scout`, `postmortem` and
`audit-fleet`, and deliberately into nothing else.

## What an RLM is, stated fairly

The root model never reads the long input. It sits in a REPL as a variable; the root
writes code to peek at it, grep it and partition it, and calls a cheaper sub-model over the
pieces. Only a constant-size prefix of each cell's output re-enters the root's context.
The paper reports large gains over the base model on long-context tasks — CodeQA, BrowseComp+,
OOLONG — at comparable median cost, using a depth-1 setup with a cheaper sub-model.

The premise holds here: `CURRENT-STATE.md` is ~135KB, a diamond's `activity.jsonl` reaches
110KB, and the questions asked of them ("which gaps are still open") need *every* part
looked at — exactly where reading the whole thing either does not fit or degrades.

## How it maps onto this fleet

| Paper | Here |
|---|---|
| root LM | the node already running |
| REPL | `rlm.py exec`, namespace pickled between cells |
| `llm_query` sub-LM | headless `claude -p`, haiku, `--effort low` |
| `FINAL_VAR` | `FINAL_VAR(name)` → `final.txt` |
| blocking sub-calls (a stated limitation) | `llm_map`, 4 concurrent |
| no cost guarantee (a stated limitation) | a dollar budget enforced before every call |

## Why the scope is this narrow

### 1. RLM is a downgrade of whoever reads through it

The pattern works by having a cheaper model read the input in the expensive model's
place. For `scout` that is the existing bargain — `GRAPH.md` § Model tiering already puts
retrieval on haiku. For `reviewer` it is the exact downgrade that section forbids: a
verifier whose reading was done by haiku launders a diff as reviewed. Same for `architect`
(shape errors are the expensive ones) and `integrator` (it must see the real conflict, not
a summary of it). Those three never use it.

### 2. Sub-model output is a lead, not a fact

The first live run over `CURRENT-STATE.md` found all 12 open gaps — and a 13th, which is
struck through as closed. A scout's `file:line` rule therefore survives intact: every
claim is confirmed with `grep` against the source before it is written as a FACT.

### 3. No hook may call it

A sub-call is a network call. ADR 0001 § 4 holds unconditionally.

### 4. No API key, no new dependency

Sub-calls use the `claude` CLI and the login the fleet already runs under. The tool is
stdlib Python. Removing `rlm.py` breaks no node — each wiring point says "use it when the
input is too big", and the fallback is reading the file.

## What was measured, and what it changed

All on 2026-10-06, haiku, one 30KB chunk of `CURRENT-STATE.md` unless noted:

- **The fleet's own settings must not reach a sub-call.** The default Claude Code system
  prompt costs $0.0105 for a one-word reply; a minimal one costs $0.00076. Sub-calls run
  with `--tools "" --setting-sources ""`, a minimal system prompt, and a cwd outside
  `repos/` so no hook records them as phantom nodes.
- **Thinking is most of the cost**: 6466 of 6491 output tokens, $0.051, 60s at default
  effort. Thinking off: $0.019, 2s — and the **wrong** answer. `--effort low`: $0.026,
  28s, right answer. Default is `low`; `none` is for literal extraction only.
- **`--max-budget-usd` bills, then discards.** Capped at $0.003, a call spent $0.027 and
  returned `error_max_budget_usd` with no result. The first live session passed it, gave
  each of five concurrent calls the whole remaining budget, and spent $0.237 against
  $0.10. Hence a worst-case reservation before every call, with waiting instead of
  refusing when only in-flight calls stand in the way.
- **End to end**, 135KB, 5 chunks: $0.0996 and 79s wall; recall 12/12, precision 12/13.

## What would reverse or widen this

- **Widen to `reviewer`**: only if a diff too large for the reviewer to read whole becomes
  routine — and then the answer is more likely a smaller slice than a cheaper reader. The
  stop rule's "3+ independent slices" exists so diffs stay reviewable.
- **Depth > 1**: only if a single piece is itself too large for haiku's window. At 30KB
  pieces against a 200K-token window this is far off.
- **Retire it**: if two months of `calls.jsonl` ledgers show it unused, or show its
  findings routinely corrected by the confirming `grep`.

## This is a decision record, not a dependency

Nothing reads this file at runtime.

## Sources

- Alex Zhang, *Recursive Language Models* — <https://alexzhang13.github.io/blog/2025/rlm/>
- Zhang, Kraska, Khattab — <https://arxiv.org/abs/2512.24601>
