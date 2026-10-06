#!/usr/bin/env python
"""Self-test for rlm.py. Stdlib only, no pytest, no network.

    python graph_agents/.graph/test_rlm.py

Everything runs under RLM_FAKE_LLM=1 in a throwaway RLM_HOME, so it costs nothing and
needs no login. What it must get right, in the order a regression would hurt:

  - the sub-call is ISOLATED: no tools, no settings, no session, minimal system prompt,
    cwd outside repos/. Lose one flag and every sub-call lands in the open run's
    activity.jsonl as a phantom node, or pays for the constitution as input.
  - spend is CAPPED: the call cap and the dollar budget both stop a flailing trajectory,
    and a failed call still takes a slot -- otherwise an erroring loop is unbounded.
  - the root's window stays clean: output is truncated to a constant-size prefix.
  - state persists across cells, and FINAL_VAR writes the answer.
"""
import importlib.util
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
REPOS = os.path.dirname(os.path.dirname(HERE))
FAILURES = []

TMP = tempfile.mkdtemp(prefix="test-rlm-")
os.environ["RLM_HOME"] = TMP
os.environ["RLM_FAKE_LLM"] = "1"

spec = importlib.util.spec_from_file_location("rlm", os.path.join(HERE, "rlm.py"))
rlm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rlm)


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %r, got %r" % (label, want, got))
        FAILURES.append(label)


def load(session, text, budget=1.0, max_calls=200):
    src = os.path.join(TMP, session + ".src")
    with open(src, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    rlm.cmd_load(session, src, budget, max_calls, "haiku")


def cell(session, code, output_chars=rlm.DEFAULT_OUTPUT_CHARS):
    return rlm.run_cell(session, code, output_chars)


DOC = "".join("line %d %s\n" % (i, "NEEDLE" if i == 731 else "hay") for i in range(1, 2001))

try:
    print("isolation")
    argv = rlm.build_argv("haiku", "low")
    pairs = {argv[i]: argv[i + 1] for i in range(len(argv) - 1)}
    check("-p present", "-p" in argv, True)
    check("--tools is empty", pairs.get("--tools"), "")
    check("--setting-sources is empty", pairs.get("--setting-sources"), "")
    check("--no-session-persistence present", "--no-session-persistence" in argv, True)
    check("--system-prompt is the minimal one", pairs.get("--system-prompt"), rlm.SUB_SYSTEM_PROMPT)
    check("--max-budget-usd absent (it bills, then discards the answer)",
          "--max-budget-usd" in argv, False)
    check("--effort low by default", pairs.get("--effort"), "low")
    check("prompt caching off for one-shot excerpts",
          rlm.build_env("low").get("DISABLE_PROMPT_CACHING"), "1")
    check("effort none: no --effort flag", "--effort" in rlm.build_argv("haiku", "none"), False)
    check("effort none: thinking off", rlm.build_env("none").get("MAX_THINKING_TOKENS"), "0")
    check("estimate covers the measured 30KB haiku call ($0.030 at medium, uncached)",
          rlm.estimate_usd(30000, "haiku") >= 0.030, True)
    check("unknown model priced as the dearest",
          rlm.estimate_usd(1000, "mystery") == rlm.estimate_usd(1000, "opus"), True)
    check("--model passed", pairs.get("--model"), "haiku")
    sdir = os.path.realpath(rlm.session_dir("x"))
    check("session dir (sub-call cwd) is outside repos/",
          os.path.commonpath([sdir, os.path.realpath(REPOS)]) == os.path.realpath(REPOS), False)
    del os.environ["RLM_HOME"]
    default = os.path.realpath(rlm.session_dir("x"))
    os.environ["RLM_HOME"] = TMP
    check("default session dir is outside repos/ too",
          os.path.commonpath([default, os.path.realpath(REPOS)]) == os.path.realpath(REPOS), False)
    try:
        rlm.session_dir("../escape")
        check("session name with a path separator is refused", False, True)
    except rlm.RLMError:
        check("session name with a path separator is refused", True, True)

    print("helpers")
    load("h", DOC)
    rc, out = cell("h", "hits = grep('needle')\nprint(hits)")
    check("grep finds the needle at its 1-based line", "(731, 'line 731 NEEDLE')" in out, True)
    rc, out = cell("h", "print(repr(peek(0, 11)), repr(peek(-4, 4)))")
    check("peek from start and from end", "'line 1 hay\\n' 'hay\\n'" in out, True)
    rc, out = cell("h", "ps = chunks(5000)\nprint(len(ps), all(p[1].endswith('\\n') for p in ps), "
                        "''.join(p[1] for p in ps) == context, ps[1][0])")
    check("chunks by line: never split a line, reassemble exactly", out.splitlines()[0].split()[1:3],
          ["True", "True"])
    rc, out = cell("h", "print(sum(len(p[1]) for p in chunks(1000, by='chars')) == len(context))")
    check("chunks by chars reassemble exactly", out.splitlines()[0], "True")

    print("persistence and output")
    rc, out = cell("h", "kept = 41\nfn = lambda: 1")
    check("unpicklable names reported, not silently lost",
          "not persisted (unpicklable): fn" in out, True)
    rc, out = cell("h", "print(kept + 1)")
    check("variables persist across cells", out.splitlines()[0], "42")
    rc, out = cell("h", "print('x' * 5000)", output_chars=100)
    check("output truncated to a constant-size prefix", out.splitlines()[0], "x" * 100)
    check("truncation states the full length", "100 of 5001 chars shown" in out, True)
    rc, out = cell("h", "1/0")
    check("an exception exits 1 and shows the traceback", (rc, "ZeroDivisionError" in out), (1, True))
    rc, out = cell("h", "print(len(re.findall('NEEDLE', context)), json.dumps(1))")
    check("re and json are preloaded, and not reported as unpicklable",
          (out.splitlines()[0], "unpicklable" in out), ("1 1", False))
    rc, out = cell("h", "print(type(context).__name__, len(context) == %d)" % len(DOC))
    check("context restored verbatim every cell", out.splitlines()[0], "str True")

    print("sub-calls")
    rc, out = cell("h", "a = llm_query('where is it?', chunks(5000)[0])\nprint(a)")
    check("llm_query wraps the piece and returns the sub-model's text",
          out.splitlines()[0].startswith("FAKE[") and "where is it?" in out, True)
    rc, out = cell("h", "rs = llm_map('q?', [str(i) for i in range(10)], workers=4)\n"
                        "print(len(rs), all(r.startswith('FAKE') for r in rs))")
    check("llm_map returns one result per piece", out.splitlines()[0], "10 True")
    check("ledger counts the batch", "sub-calls this cell: 10" in out, True)
    rc, out = cell("h", "rs = llm_map('q?', ['a' * 900, 'b', 'c' * 300], workers=3)\n"
                        "n = [int(r[5:r.index(' chars')]) for r in rs]\nprint(n[0] > n[2] > n[1])")
    check("llm_map preserves input order", out.splitlines()[0], "True")
    with open(os.path.join(rlm.session_dir("h"), "calls.jsonl"), encoding="utf-8") as f:
        check("every sub-call is ledgered", sum(1 for _ in f), 14)

    print("caps")
    load("cap", DOC, max_calls=3)
    rc, out = cell("cap", "rs = llm_map('q?', ['a','b','c','d','e'], workers=1)\nprint(rs)")
    check("call cap: the 4th and 5th calls are refused",
          out.count("call cap reached"), 2)
    rc, out = cell("cap", "llm_query('again?')")
    check("cap survives across cells (ledger is on disk)", "BudgetExceeded" in out, True)
    load("usd", DOC, budget=0.0025)
    rc, out = cell("usd", "rs = llm_map('q?', ['a','b','c','d'], workers=1)\nprint(rs)")
    check("dollar budget: refuses the call that would pass the cap",
          out.count("budget would be exceeded"), 2)
    load("usd4", DOC, budget=0.0025)
    rc, out = cell("usd4", "rs = llm_map('q?', ['a','b','c','d'], workers=4)\nprint(rs)")
    check("concurrency cannot overshoot: in-flight calls count against the budget",
          out.count("budget would be exceeded"), 2)
    # Estimates are worst cases; real calls come in under them. Here each call reserves
    # $0.002 and costs $0.001, against $0.004. Refusing on reservations alone runs 2 and
    # refuses 2. Waiting for in-flight calls to settle runs 3 and refuses only the one
    # that spent money genuinely leaves no room for.
    load("wait", DOC, budget=0.004)
    real_est, rlm.estimate_usd = rlm.estimate_usd, (lambda *a, **k: 0.002)
    rc, out = cell("wait", "rs = llm_map('q?', ['a','b','c','d'], workers=4)\nprint(rs)")
    rlm.estimate_usd = real_est
    check("a call blocked only by in-flight reservations waits, not refused",
          (out.count("FAKE["), out.count("budget would be exceeded")), (3, 1))

    print("failure still costs a slot")
    load("fail", DOC, max_calls=2)
    rlm._fake_call, real_fake = (lambda p: (_ for _ in ()).throw(RuntimeError("boom"))), rlm._fake_call
    rc, out = cell("fail", "rs = llm_map('q?', ['a', 'b', 'c'], workers=1)\nprint(rs)")
    rlm._fake_call = real_fake
    check("a raising sub-call is recorded and the batch survives", out.count("RuntimeError: boom"), 2)
    check("...and it consumed its slot", "call cap reached" in out, True)

    print("FINAL_VAR")
    rc, out = cell("h", "answer = {'line': 731}\nFINAL_VAR('answer')")
    check("FINAL_VAR announces itself", "FINAL_VAR written" in out, True)
    with open(os.path.join(rlm.session_dir("h"), "final.txt"), encoding="utf-8") as f:
        check("final.txt holds the value", f.read().replace(" ", "").replace("\n", ""), '{"line":731}')
    rc, out = cell("h", "FINAL_VAR('nope')")
    check("FINAL_VAR on a missing name fails loudly", (rc, "no variable named" in out), (1, True))
    rc, out = rlm.run_cell("never-loaded", "print(1)")
    check("exec without load is refused", rc, 2)
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print()
if FAILURES:
    print("%d FAILED: %s" % (len(FAILURES), ", ".join(FAILURES)))
    sys.exit(1)
print("all passed")
