# ADR 0001 — Jev is not adopted in the fleet

**Date:** 2026-09-22
**Status:** Accepted
**Scope:** `graph_agents/` only. Says nothing about whether an app may use Jev in its own product.

## The decision

The fleet does not adopt TypeSafe AI's **Jev** — not in the hooks, not in the nodes, not
in the routing. No fleet code calls it and none is planned.

This is written down so it does not get re-argued every time the model is in the news.
Re-open it only against § What would reverse this, which names the conditions, not the
mood.

## What Jev is, stated fairly

Shipped 2026-09-15. A "System One" model that returns a **typed, calibrated decision**
instead of text: a choice from up to 255 options, a score, or a probability. It gives up
string generation entirely — no prose, no code. Roughly 70–500ms end to end, priced around
$0.042 per million input tokens with output free, and claimed at ~200x faster and ~400x
cheaper than an LLM doing the same classification.

The premise is correct and worth stating, because the reason we decline is not that the
premise is wrong: **a production agent spends most of its steps deciding, not writing**,
and spending a full LLM call to learn "which tool / is this allowed / what category" is
waste. Where that waste exists, Jev removes it.

## Why it does not fit here

### 1. The fleet's decisions are already deterministic, and must stay that way

Every enforcement point in the fleet is exact Python with an auditable answer:

| Decision | Mechanism |
|---|---|
| is this path in the approved file set | set membership — `guard-builder-scope.py` |
| does this commit carry attribution | substring match — `guard-commit-trailers.py` |
| is the node's return over 3 lines | line count — `check-return-cap.py` |
| did the graph's edges hold | ordering check — `verify-state.py --audit` |
| did the branch actually merge | git ancestry — `close-run.py` |
| which app does this touch | table lookup — `portfolio/registry.json` |

Jev replaces an **LLM call** used as a classifier. It has nothing to offer a
`set.__contains__`. Substituting a calibrated probability for any row above is a strict
downgrade: a commit guard that denies at p=0.91 is not a guard. That guard exists because
the attribution rule was prose, prose failed, and on 2026-08-26 two repos had their
history rewritten over it. The lesson was *stop trusting a judgment where a check will do* —
adopting Jev at any of these points runs that lesson backwards.

### 2. The decisions that are genuine judgment all have to produce language

Scout's facts, architect's plan, builder's code, reviewer's findings, integrator's merge.
Each of these exists to hand a human or the next node something to read and act on — the
plan a human approves at step 4, the findings a builder fixes against. A typed verdict
with no prose behind it is not actionable by any of them. Jev structurally cannot do this
half of the fleet's work, and says so itself.

### 3. There is no volume to save

The layer Jev targets — high-frequency cheap classification — is about three calls per run
here, a few runs a week. 400x cheaper than approximately nothing is approximately nothing,
and 70–500ms is noise beside nodes that run for minutes. The cost case does not survive
contact with this fleet's actual traffic.

### 4. A hook that makes a network call fails open or fails shut, and both are bad

`PreToolUse` guards must work offline and must not fail open. Routing one through a paid
remote API adds two failure modes — timeout and rate limit — whose only two resolutions
are "deny every write when the network blips" (the fleet becomes unusable on a bad
connection) or "allow the write" (the guard is silently gone). Neither is acceptable for
code whose entire job is to be the boundary.

### 5. The most tempting integration point is the most dangerous one

`guard-builder-scope.py`'s `Bash` classifier already admits where it cannot resolve a
write target — a shell variable, a `$(...)`, a command over the 128KB cap — and allows it
with a recorded warning. Asking Jev "does this command write, and where" looks like the
perfect fix.

It is not, and the reason is documented. Jev treats input state **as data, not as
hostile**; TypeSafe's own docs warn that content written to steer it can move the answer.
A published test planted a fake tool-output field claiming prior approval and dropped the
block probability on a dangerous command from **0.76 to 0.48**. In our case the command
string is written by the *builder being guarded*. Putting an injectable model on that
boundary invents a hole where today there is only a known, logged blind spot — and a
logged blind spot is a better artifact than a confident wrong number.

LangChain's published mitigation is to exclude tool output from classifier input so
fetched content cannot authorize its own execution. That is sound, and it is a rule this
fleet would have to build and maintain from scratch to protect a boundary that currently
needs no such protection.

## What was considered and rejected on the merits

**The architect's `risk: high|low` slice tag.** The cleanest Jev-shaped decision in the
codebase: one typed classification, low cardinality, already load-bearing (it sets the
reviewer's brief depth). Rejected anyway — it is produced as a side effect of planning at
no marginal cost, it passes through the step-4 human gate before it does anything, and
moving it to a remote call would add a dependency to buy nothing. Correct shape, no
problem to solve.

## What would reverse this

A classification surface that is genuinely high-volume and genuinely low-stakes. None
exists today. Plausible ones, in the order they would likely arrive:

1. **An `activity.jsonl` event classifier.** Thousands of events per run rather than
   dozens of decisions. Gap #20's phantom-stop discriminator is hand-rolled heuristics
   today; if that grows into real classification over the full event stream, the volume
   argument in § 3 inverts.
2. **`fleetview` triage** across many repos, if it ever ranks or categorises at a rate a
   human cannot.
3. **Pre-scout routing** from a free-text goal to an app. At 5 portfolio apps this is a
   registry lookup and nothing more. At 50 it might stop being one.

Note what all three have in common and what the rejected candidates lack: **high volume,
no enforcement authority, and a cheap wrong answer.** That is the test. If a proposed
integration fails any of the three, this ADR still applies.

Even then, the § 4 constraint holds unconditionally: nothing in `.claude/hooks/**` may
depend on a network call, whoever is serving it.

## This is a decision record, not a dependency

Nothing reads this file at runtime. It is prose for a human deciding whether to re-open a
settled question. Deleting it breaks no build — it only costs the next reader the argument
above.

## Sources

- TypeSafe AI — <https://typesafe.ai/blog/introducing-system-one-models-and-jev>
- VentureBeat, on prompt injection moving Jev's verdict —
  <https://venturebeat.com/security/companies-are-putting-jev-in-charge-of-ai-agent-decisions-and-prompt-injection-can-influence-the-verdict>
- LangChain, on harness design and excluding tool output —
  <https://www.langchain.com/blog/building-a-harness-with-jev>
