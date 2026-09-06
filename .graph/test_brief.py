#!/usr/bin/env python
"""Self-test for brief.py's slice rows. Stdlib only, no pytest.

    python graph_agents/.graph/test_brief.py

The board is what a human looks at INSTEAD of the state file, so the property under test
is not "the verdict is correct" -- it is "a rejection that was later fixed is still
visible". A board that resolved to the latest attempt and printed nothing else would pass
every naive check while quietly turning every loop this fleet has ever run into a clean
first-try pass, which is a worse defect than the one it fixed.

So the four numbered cases below are the four ways the row can lie: show the stale
verdict, show the fixed slice as though it never looped, launder a re-review's REJECT,
and -- with no `verify-state.py` to import the rule from -- guess. Each is asserted on its
own so it can go red on its own.

Everything runs through `brief.board(state, path, brief.ASCII)`, the exact call
`.claude/hooks/show-board.py` makes, because that hook forces ASCII and a loop marker
legible only in a Unicode terminal would vanish in the one place the board prints by
itself.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
RUNS = os.path.join(HERE, "runs")
FAILURES = []


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %r, got %r" % (label, want, got))
        FAILURES.append(label)


def load_brief(path, name):
    """`brief.py` from a given path. A fixture fleet's copy is a different module."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review(verdict, attempt=1, attempts=None):
    """`reviews.<slice>` as reviewers actually write it.

    The top level IS attempt 1 and stays put; `attempts` is {N: verdict} for the
    re-reviews, each nesting under its own `attempt_N`.
    """
    out = {"written_by": "reviewer", "verdict": verdict, "attempt": attempt,
           "summary": "s", "findings": []}
    for number, again in sorted((attempts or {}).items()):
        out["attempt_%d" % number] = {"written_by": "reviewer", "verdict": again,
                                      "attempt": number, "summary": "s", "findings": []}
    return out


def state_for(reviews):
    """A one-slice run, mid-flight, with `reviews.s1` supplied by the caller."""
    return {
        "run_id": "brief-self-test",
        "goal": "prove the board shows the loop",
        "app": "targetapp",
        "status": "reviewing",
        "approved_by_human": True,
        "scout": {"written_by": "scout", "facts": ["f (a:1)"], "unknowns": [], "risks": []},
        "architect": {"written_by": "architect", "shape": "single-loop",
                      "parallel_safe": False, "rationale": "r",
                      "plan": [{"slice": "s1", "intent": "i", "files": ["a"],
                                "done_when": "x"}]},
        "builders": {"s1": {"written_by": "builder", "status": "done", "branch": "b",
                            "changed": ["a"], "notes": "", "gate_results": "cmd -> ok"}},
        "reviews": {"s1": reviews} if reviews is not None else {},
        "log": ["orchestrator: opened"],
    }


FAKE_PATH = os.path.join(RUNS, "brief-self-test", "state.json")


def row(brief, state, sid="s1", g=None, path=FAKE_PATH):
    """One slice row off a rendered board -- the line a human's eye lands on."""
    lines = brief.board(state, path, g if g is not None else brief.ASCII)
    for line in lines:
        if line.startswith("  %s " % sid):
            return line
    return ""


def cell(line):
    """Just the review half of a row, so a build-column change cannot fake a pass."""
    return line.split("review", 1)[1].strip() if "review" in line else ""


REAL = load_brief(os.path.join(HERE, "brief.py"), "brief_real")

print("brief.py slice rows")

# The hook calls `brief.board(state, path, brief.ASCII)` by file path and nothing tells
# it when that stops being true -- it is a PostToolUse hook, so it fails silently.
check("board(state, path, glyphs) and ASCII are still the hook's contract",
      callable(getattr(REAL, "board", None)) and isinstance(getattr(REAL, "ASCII", None), dict),
      True)

# -- (1) the stale verdict: attempt 1 REJECTed, attempt 2 passed, the slice is PASS
looped = row(REAL, state_for(review("REJECT", attempts={2: "PASS"})))
check("(1) a slice fixed on attempt 2 renders as PASS", cell(looped).startswith("PASS"), True)
check("(1) and not as the top-level REJECT it still carries",
      cell(looped).startswith("REJECT"), False)

# -- (2) the loop itself. This is the regression the fix could cause: a row that resolves
# correctly and reads as though the slice sailed through first time.
clean = row(REAL, state_for(review("PASS")))
check("(2) a fixed slice does not render byte-identical to a first-try PASS",
      looped == clean, False)
check("(2) the row names the loop", "looped" in looped, True)
check("(2) the row names the attempt it passed on", "attempt 2" in looped, True)
check("(2) the row shows both verdicts, in order",
      "REJECT -> PASS" in looped, True)
check("(2) a first-try PASS stays a bare PASS", cell(clean), "PASS")

# -- (3) anti-laundering: a re-review may REJECT what attempt 1 passed, and then the
# slice IS rejected. A helper answering "did any attempt pass" renders this as PASS.
relapse = row(REAL, state_for(review("PASS", attempts={2: "REJECT"})))
check("(3) a slice REJECTed on re-review renders as REJECT",
      cell(relapse).startswith("REJECT"), True)

# -- (4) degraded: a fleet with no verify-state.py has no attempt rule. The row must say
# so rather than read the top-level verdict, which is attempt 1's and may be stale.
tmp = tempfile.mkdtemp(prefix="brieftest-")
try:
    graph = os.path.join(tmp, ".graph")
    os.makedirs(os.path.join(graph, "runs", "a-run"))
    shutil.copy(os.path.join(HERE, "brief.py"), os.path.join(graph, "brief.py"))
    lone = load_brief(os.path.join(graph, "brief.py"), "brief_degraded")
    check("(4) the fixture fleet really has no verify-state.py",
          os.path.isfile(os.path.join(graph, "verify-state.py")), False)
    degraded = row(lone, state_for(review("REJECT", attempts={2: "PASS"})),
                   path=os.path.join(graph, "runs", "a-run", "state.json"), g=lone.ASCII)
    check("(4) the row says it is degraded", "degraded" in degraded, True)
    check("(4) and prints no verdict at all -- guessing from the top level is the defect",
          "PASS" in degraded or "REJECT" in degraded, False)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# -- the hook renders ASCII and the terminal renders Unicode. A loop marker that survives
# only one of those is the invisible rejection again, one layer down.
check("the ASCII board is ASCII, all of it", all(ord(c) < 128 for c in looped), True)
uni = row(REAL, state_for(review("REJECT", attempts={2: "PASS"})), g=REAL.UNICODE)
check("the Unicode board shows the loop too",
      "looped" in uni and "attempt 2" in uni and "REJECT → PASS" in uni, True)

# -- the count folds in from the resolved attempts, not from `reviews.s1.attempt`
check("three attempts count as three",
      "attempt 3" in row(REAL, state_for(review("REJECT", attempts={2: "REJECT",
                                                                   3: "PASS"}))), True)
check("and the whole chain is on the row",
      "REJECT -> REJECT -> PASS" in row(REAL, state_for(
          review("REJECT", attempts={2: "REJECT", 3: "PASS"}))), True)
check("a re-review from before the nesting convention still reads as a re-review",
      cell(row(REAL, state_for(review("PASS", attempt=2)))), "PASS (attempt 2)")
check("a lone REJECT is not dressed up as a loop",
      cell(row(REAL, state_for(review("REJECT")))), "REJECT")
check("an unreviewed slice is untouched by any of this",
      cell(row(REAL, state_for(None))), ".. waiting")

# -- the run this was all found in. The synthetic cases prove the rule; this proves the
# rule reaches the file a human actually opens.
real_path = os.path.join(RUNS, "2026-09-04-payload-split", "state.json")
check("2026-09-04-payload-split is on disk to be checked", os.path.isfile(real_path), True)
with open(real_path, encoding="utf-8") as fh:
    real_state = json.load(fh)
real_row = row(REAL, real_state, "s2", path=real_path)
check("its s2 -- REJECTed, fixed, passed -- reads as a loop on the real board",
      "looped" in real_row and "attempt 2" in real_row and "REJECT -> PASS" in real_row,
      True)
print("       %s" % real_row.strip())

print()
if FAILURES:
    print("%d FAILED" % len(FAILURES))
    for line in FAILURES:
        print("  - %s" % line)
    sys.exit(1)
print("all checks passed")
