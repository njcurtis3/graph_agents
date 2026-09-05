#!/usr/bin/env python
"""Self-test for verify-state.py's attempt-resolution rule. Stdlib only, no pytest.

    python graph_agents/.graph/test_verify_state.py

`close-run.py` and `brief.py` both import `verify-state.py`, so the rule tested here is
the rule the whole fleet reads verdicts by. Two things it must get right, and the second
is the one a green suite will not notice on its own:

  - the LATEST attempt supplies the verdict, so a slice that was rejected and then fixed
    stops reporting as failed;
  - a rejection is never LAUNDERED. An implementation that answers "did any attempt pass"
    satisfies the happy path and quietly certifies a slice whose re-review REJECTed it.
    Case 3 is the only case that catches that, and `ever_rejected` is the primitive that
    keeps the earlier REJECT visible after the fix.

The synthetic cases call the helper directly. The last two are blast radius, ASSERTED and
never targeted: retiring four of 2026-08-25-fleet-hardening's stale blockers is a
consequence of reading verdicts correctly, and its remaining two -- an unreviewed slice and
a run with no authorship stamps -- are real findings that must survive this change. A fix
that quietly closes fleet-hardening fails here.
"""
import importlib.util
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
SCRIPT = os.path.join(HERE, "verify-state.py")
RUNS = os.path.join(HERE, "runs")
FAILURES = []


def load_module():
    """Import verify-state.py by path -- the hyphen makes it un-importable by name."""
    spec = importlib.util.spec_from_file_location("verify_state", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


v = load_module()


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %r, got %r" % (label, want, got))
        FAILURES.append(label)


def resolved(review):
    """The verdict the fleet reads off a slice. None when nothing resolves at all.

    Not `final_verdict(r)["verdict"]`: a broken helper that resolves to nothing would
    raise here and take the whole file down with it, and a suite that dies is a suite
    that cannot tell you WHICH case broke.
    """
    final = v.final_verdict(review)
    return final["verdict"] if final else None


def review(verdict, **attempts):
    """A `reviews.<slice>` value: top level IS attempt 1, kwargs nest as attempt_N."""
    node = {"written_by": "reviewer", "verdict": verdict, "attempt": 1,
            "summary": "attempt 1 said %s" % verdict, "findings": []}
    for key, nested in attempts.items():
        node[key] = {"written_by": "reviewer", "verdict": nested,
                     "attempt": int(key.split("_")[1]),
                     "summary": "%s said %s" % (key, nested), "findings": []}
    return node


def state_with(reviews, integrator=False, status="reviewing"):
    """A whole run state carrying `reviews`, for the audit-level checks."""
    state = {
        "run_id": "verify-state-self-test",
        "goal": "a test run",
        "app": "graph_agents",
        "status": status,
        "approved_by_human": True,
        "scout": {"written_by": "scout", "facts": ["f (a:1)"], "unknowns": [],
                  "risks": []},
        "architect": {"written_by": "architect", "shape": "single-loop",
                      "parallel_safe": False, "rationale": "r",
                      "plan": [{"slice": s, "intent": "i", "files": ["a.py"],
                                "done_when": "d", "risk": "low", "risk_reason": "r"}
                               for s in sorted(reviews)],
                      "edges": [], "not_doing": [], "human_gate": "g"},
        "scope_exceptions": [],
        "builders": {s: {"written_by": "builder", "status": "done", "branch": "b",
                         "changed": ["a.py"], "notes": "",
                         "gate_results": "ran it, it passed"} for s in reviews},
        "reviews": dict(reviews),
        "integrator": {"written_by": "integrator", "merged": ["b"], "conflicts": [],
                       "verification": "ran the suite"} if integrator else
                      {"written_by": "", "merged": [], "conflicts": [],
                       "verification": ""},
        "ops": {"written_by": "", "gated": True, "actions": []},
        "log": ["orchestrator | 2026-09-05 | opened"],
    }
    return state


def audit_lines(state):
    return v.audit(state, v.load_template())


def run_audit(run_id):
    """`--audit <run>` as a hook or a human runs it. Returns (exit code, output)."""
    proc = subprocess.run([sys.executable, SCRIPT, "--audit", run_id],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


print("attempt resolution")

# (1) The defect itself: attempt 1 REJECTed, a fresh reviewer PASSed the fix. The slice
#     is PASSing, and every gate in the fleet must read it that way.
fixed = review("REJECT", attempt_2="PASS")
check("(1) top REJECT + attempt_2 PASS resolves to PASS", resolved(fixed), "PASS")
check("(1) and the resolved attempt is numbered 2",
      (v.final_verdict(fixed) or {}).get("attempt"), 2)
check("(1) both attempts are kept, in order",
      [a["verdict"] for a in v.review_attempts(fixed)], ["REJECT", "PASS"])

# (2) The ordinary case, which must not regress while the interesting ones are fixed.
clean = review("PASS")
check("(2) top PASS with nothing nested resolves to PASS", resolved(clean), "PASS")
check("(2) a clean pass never looped", v.ever_rejected(clean), False)

# (3) THE ANTI-LAUNDERING CASE. A re-review may REJECT, and then REJECT is the answer.
#     An implementation that asks "did any attempt pass" passes every other case here.
relapsed = review("PASS", attempt_2="REJECT")
check("(3) top PASS + attempt_2 REJECT resolves to REJECT", resolved(relapsed),
      "REJECT")

# (4) The rejection stays VISIBLE after it is fixed -- the regression this whole change
#     would otherwise cause. Display only, forever: it must never gate anything.
check("(4) top REJECT + attempt_2 PASS still reports ever_rejected",
      v.ever_rejected(fixed), True)

# (5) The first gap stops the walk. A lone attempt_3 means the numbering is not what the
#     reader thinks it is, so the top level decides rather than a guess two steps out.
gapped = review("REJECT", attempt_3="PASS")
check("(5) attempt_3 with attempt_2 absent stops at the gap", resolved(gapped),
      "REJECT")
check("(5) and the skipped attempt is not in the list",
      len(v.review_attempts(gapped)), 1)

# (6) The cap matches fleetview's `for (i = 2; i < 10; i++)` exactly. Past it the two
#     readers WOULD disagree, so the helper is loud rather than quietly authoritative.
over = review("PASS", attempt_2="PASS", attempt_10="REJECT")
check("(6) attempt_10 is named as over the cap",
      v.over_cap_attempts(over), ["attempt_10"])
v._WARNED.clear()
captured, sys.stderr = sys.stderr, io.StringIO()
try:
    v.review_attempts(over)
    warning = sys.stderr.getvalue()
finally:
    sys.stderr = captured
check("(6) walking it warns on stderr", "attempt_10" in warning, True)
check("(6) and --audit reports it as a violation",
      any("attempt_10" in line and "past the attempt_9 cap" in line
          for line in audit_lines(state_with({"s1": over}))), True)

print()
print("the audit's own two verdict reads")

# verify-state.py:261, the `status: done` line. Nothing else in this run is wrong, so a
# stale read here is the only thing that can produce a violation.
check("a fixed slice does not block `status: done`",
      [p for p in audit_lines(state_with({"s1": fixed}, status="done")) if "reviews.s1" in p],
      [])
check("a slice whose latest attempt REJECTed still blocks `status: done`",
      any("reviews.s1 is REJECT" in p
          for p in audit_lines(state_with({"s1": relapsed}, status="done"))), True)

# verify-state.py:283, the fan-in check. It NARROWED on 2026-09-05, at a human gate: from
# "no slice ever REJECTed" to "no slice's LATEST attempt is REJECT". The second assertion
# is the half that keeps it a gate.
check("fan-in over a slice that looped and passed is not a violation",
      [p for p in audit_lines(state_with({"s1": fixed}, integrator=True))
       if "fan-in" in p], [])
check("fan-in over a slice still sitting at REJECT still blocks",
      any("fan-in" in p for p in audit_lines(state_with({"s1": relapsed},
                                                        integrator=True))), True)

print()
print("blast radius on the runs already on disk")

# 2026-08-25-fleet-hardening has been misreporting s4 and s5 as failed since the day it
# closed. Retiring those two is the consequence; the OTHER two are real and must survive.
CLOSING_FIX = ("verify-state: run is status 'done' but reviews.closing_fix is unwritten "
               "-- only PASS closes a slice")
NO_STAMPS = ("verify-state: no key in this run is authorship-stamped -- `written_by` was "
             "added to _schema.json on 2026-08-26; runs opened before that are "
             "unverifiable on the never-rewrite-another-node's-key contract and stay that "
             "way")

code, out = run_audit("2026-08-25-fleet-hardening")
check("fleet-hardening still fails its audit", code, 1)
check("fleet-hardening reports exactly 2 edge violations",
      "2026-08-25-fleet-hardening -- 2 edge violation(s)" in out, True)
check("the unreviewed closing_fix slice survives, verbatim", CLOSING_FIX in out, True)
check("the authorship blocker survives, verbatim", NO_STAMPS in out, True)
check("s4's stale REJECT is retired", "reviews.s4" in out, False)
check("s5's stale REJECT is retired", "reviews.s5" in out, False)

# The run that could not close. Its s2 was re-reviewed and passed.
code, out = run_audit("2026-09-04-payload-split")
check("payload-split audits clean", code, 0)
check("and says so", "2026-09-04-payload-split -- audit clean" in out, True)

# Every run on disk still audits, and none of them reports a slice as REJECT when a later
# attempt passed it. This is the live form of "no run is misread"; the byte-identity of
# every other run's output against its pre-change baseline was measured once, by hand.
for run_id in sorted(os.listdir(RUNS)):
    if not os.path.isdir(os.path.join(RUNS, run_id)):
        continue
    state, _ = v.load(run_id)
    code, out = run_audit(run_id)
    passing = [s for s in v.real_slices(state, v.load_template())
               if v.slice_verdict(state, s) == "PASS"]
    stale = [line for line in out.splitlines()
             for s in passing if "reviews.%s is REJECT" % s in line]
    check("%s reports no passing slice as REJECT" % run_id, stale, [])

print()
if FAILURES:
    print("%d FAILED" % len(FAILURES))
    for line in FAILURES:
        print("  - %s" % line)
    sys.exit(1)
print("all checks passed")
