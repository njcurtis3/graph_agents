#!/usr/bin/env python
"""Self-test for check-return-cap.py. Stdlib only, no pytest.

    python graph_agents/.graph/test_check_return_cap.py

Two layers, mirroring the two precedents this slice was told to follow:
  - the pure helpers (`encode_cwd`, `line_count`, `last_return_text`, `find_transcript`,
    `agent_types`, `check`) are exercised in-process, one import, the
    `test_record_activity.py` style -- fast, and each failure names the exact function.
  - `main()`'s own CLI wiring is exercised via subprocess against a COPIED fleet in a
    temp dir and a temp HOME, the `test_show_board.py` precedent -- never the live tree,
    never the live `.graph/CURRENT`, and never this run's own real transcripts.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
MODULE_PATH = os.path.join(HERE, "check-return-cap.py")
VERIFY_PATH = os.path.join(HERE, "verify-state.py")
SCHEMA_PATH = os.path.join(HERE, "runs", "_schema.json")

spec = importlib.util.spec_from_file_location("check_return_cap", MODULE_PATH)
crc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crc)

checks = []


def check(name, cond):
    checks.append((name, bool(cond)))
    if not cond:
        print("FAIL:", name)


# ---------------------------------------------------------------------- encode_cwd

check("encode_cwd matches Claude Code's observed project-dir naming",
      crc.encode_cwd(r"C:\Users\natha\Desktop\repos") == "C--Users-natha-Desktop-repos")
check("encode_cwd leaves alnum runs alone",
      crc.encode_cwd("abcXYZ123") == "abcXYZ123")
check("encode_cwd handles a posix-style path too",
      crc.encode_cwd("/home/nathan/repos") == "-home-nathan-repos")

# ------------------------------------------------------------------------ line_count

check("line_count: exactly 3 non-empty lines is 3",
      crc.line_count("line one\nline two\nline three") == 3)
check("line_count: 3 lines plus trailing blank lines is still 3, not 4",
      crc.line_count("line one\nline two\nline three\n\n\n") == 3)
check("line_count: 4 non-empty lines is 4",
      crc.line_count("l1\nl2\nl3\nl4") == 4)
check("line_count: blank lines between real lines are not counted",
      crc.line_count("l1\n\nl2\n   \nl3") == 3)
check("line_count: a single line with no newline is 1",
      crc.line_count("just one line") == 1)

# -------------------------------------------------------------------- last_return_text

with tempfile.TemporaryDirectory() as tmp:
    good = os.path.join(tmp, "agent-x.jsonl")
    with open(good, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"message": {"content": [
            {"type": "text", "text": "First turn.\nStill first turn."}]}}) + "\n")
        fh.write(json.dumps({"message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {}}]}}) + "\n")
        fh.write("not json at all, a torn final line\n")   # RULING: skipped, no raise
        fh.write(json.dumps({"message": {"content": [
            {"type": "text", "text": "line one\nline two\nline three\nline four"},
            {"type": "tool_use", "name": "Edit", "input": {}}]}}) + "\n")
    got = crc.last_return_text(good)
    check("last_return_text keeps only the NEWEST text block across turns",
          got == "line one\nline two\nline three\nline four")
    check("last_return_text is UNCAPPED and NOT collapsed to one line -- unlike "
          "record-activity.py's last_said_by, which this deliberately does not copy "
          "that behaviour from",
          got is not None and "\n" in got)
    check("a torn line mid-transcript is skipped, not raised -- the later valid turn "
          "still wins",
          got == "line one\nline two\nline three\nline four")

    toolonly = os.path.join(tmp, "agent-tool-only.jsonl")
    with open(toolonly, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {}}]}}) + "\n")
    check("last_return_text is None when a transcript has tool_use but no text block",
          crc.last_return_text(toolonly) is None)

    empty = os.path.join(tmp, "agent-empty.jsonl")
    open(empty, "w").close()
    check("last_return_text on an empty file is None, not a fabricated return",
          crc.last_return_text(empty) is None)

    check("last_return_text on a missing file returns None, never raises",
          crc.last_return_text(os.path.join(tmp, "does-not-exist.jsonl")) is None)

# ---------------------------------------------------------------------- find_transcript

with tempfile.TemporaryDirectory() as tmp:
    sess_a = os.path.join(tmp, "sessA", "subagents")
    sess_b = os.path.join(tmp, "sessB", "subagents")
    os.makedirs(sess_a)
    os.makedirs(sess_b)
    open(os.path.join(sess_a, "agent-xyz.jsonl"), "w").close()
    open(os.path.join(sess_b, "agent-abc.jsonl"), "w").close()

    found = crc.find_transcript("xyz", tmp)
    check("find_transcript locates the one matching agent id across session dirs",
          found is not None and found.endswith(os.path.join("sessA", "subagents",
                                                              "agent-xyz.jsonl")))
    check("find_transcript returns None for an agent id with no session anywhere",
          crc.find_transcript("no-such-agent", tmp) is None)
    check("find_transcript returns None for an empty agent id",
          crc.find_transcript("", tmp) is None)
    check("find_transcript returns None when the projects root itself is missing",
          crc.find_transcript("xyz", os.path.join(tmp, "does-not-exist")) is None)

# ------------------------------------------------------------------------ agent_types

with tempfile.TemporaryDirectory() as tmp:
    run_dir = os.path.join(tmp, "a-run")
    os.makedirs(run_dir)
    with open(os.path.join(run_dir, "activity.jsonl"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"t": 1, "ev": "start", "agent": "builder", "id": "b1"}) + "\n")
        fh.write(json.dumps({"t": 2, "ev": "tool", "agent": "builder", "id": "b1",
                              "tool": "Edit"}) + "\n")
        fh.write(json.dumps({"t": 3, "ev": "stop", "agent": "builder", "id": "b1"}) + "\n")
        # gap #20's phantom: a lone stop with a fresh id, no start/tool ever seen for it.
        fh.write(json.dumps({"t": 4, "ev": "stop", "agent": "orchestrator",
                              "id": "phantom1"}) + "\n")
        fh.write(json.dumps({"t": 5, "ev": "start", "agent": "reviewer", "id": "r1"}) + "\n")
    types = crc.agent_types(run_dir)
    check("agent_types maps every real lane's id to its agent type",
          types.get("b1") == "builder" and types.get("r1") == "reviewer")
    check("agent_types excludes a phantom lane (lone stop, gap #20)",
          "phantom1" not in types)
    check("agent_types has exactly the two real lanes, nothing extra",
          sorted(types) == ["b1", "r1"])

    no_file_dir = os.path.join(tmp, "no-activity-run")
    os.makedirs(no_file_dir)
    check("agent_types on a run with no activity.jsonl is {}, not a traceback",
          crc.agent_types(no_file_dir) == {})

    torn_dir = os.path.join(tmp, "torn-run")
    os.makedirs(torn_dir)
    with open(os.path.join(torn_dir, "activity.jsonl"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"t": 1, "ev": "start", "agent": "builder", "id": "b1"}) + "\n")
        fh.write("not json at all\n")
    check("agent_types on activity.jsonl with a torn line degrades to {}, not a "
          "traceback -- copied from postmortem.py's read_lanes, same whole-file "
          "discard on any unparseable line",
          crc.agent_types(torn_dir) == {})

# ------------------------------------------------------------------------------ check()


def write_transcript(root, session, agent_id, text):
    d = os.path.join(root, session, "subagents")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "agent-%s.jsonl" % agent_id), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"message": {"content": [{"type": "text", "text": text}]}}) + "\n")


LAUNCH_CWD = r"C:\fake\launch\cwd"

with tempfile.TemporaryDirectory() as tmp:
    run_dir = os.path.join(tmp, "a-run")
    os.makedirs(run_dir)
    lanes = [
        ("b_ok", "builder"), ("b_blank", "builder"), ("b_bad", "builder"),
        ("a_ok", "architect"), ("o_ok", "ops"), ("r_missing", "reviewer"),
    ]
    with open(os.path.join(run_dir, "activity.jsonl"), "w", encoding="utf-8") as fh:
        for agent_id, agent_type in lanes:
            fh.write(json.dumps({"t": 1, "ev": "start", "agent": agent_type,
                                  "id": agent_id}) + "\n")

    home = os.path.join(tmp, "home")
    projects_root = os.path.join(home, ".claude", "projects", crc.encode_cwd(LAUNCH_CWD))
    write_transcript(projects_root, "sess1", "b_ok", "line one\nline two\nline three")
    write_transcript(projects_root, "sess1", "b_blank",
                      "line one\nline two\nline three\n\n\n")
    write_transcript(projects_root, "sess1", "b_bad",
                      "line one\nline two\nline three\nline four")
    write_transcript(projects_root, "sess1", "a_ok",
                      "l1\nl2\nl3\nl4\nl5\nl6 -- architect's plan is gate material")
    write_transcript(projects_root, "sess1", "o_ok",
                      "l1\nl2\nl3\nl4\nl5\nl6 -- ops's deploy is gate material")
    # r_missing intentionally gets no transcript file at all.

    old_expanduser = os.path.expanduser
    os.path.expanduser = lambda p: home if p == "~" else old_expanduser(p)
    try:
        violations, unverifiable, checked = crc.check(run_dir, LAUNCH_CWD)
    finally:
        os.path.expanduser = old_expanduser

    check("check(): a 4-line return by a non-exempt node is a violation",
          any("b_bad" in v for v in violations))
    check("check(): an exactly-3-line return is not a violation",
          not any("b_ok" in v for v in violations))
    check("check(): a 3-line return with trailing blank lines is not a violation",
          not any("b_blank" in v for v in violations))
    check("check(): a 6-line architect return is exempt, not a violation",
          not any("a_ok" in v for v in violations))
    check("check(): a 6-line ops return is exempt, not a violation",
          not any("o_ok" in v for v in violations))
    check("check(): exactly one violation total (only b_bad)", len(violations) == 1)
    check("check(): an agent id with no transcript on disk is reported unverifiable",
          any("unverifiable" in u and "r_missing" in u for u in unverifiable))
    check("check(): exactly one unverifiable node (only r_missing)",
          len(unverifiable) == 1)
    check("check(): compliant/exempt returns are all in the checked list",
          len(checked) == 5)   # b_ok, b_blank, b_bad, a_ok, o_ok -- not r_missing

    joined = "\n".join(violations + unverifiable + checked)
    check("check() never echoes the checked transcript text verbatim into its report",
          "architect's plan is gate material" not in joined
          and "ops's deploy is gate material" not in joined)

    empty_run = os.path.join(tmp, "empty-run")
    os.makedirs(empty_run)
    v2, u2, c2 = crc.check(empty_run, LAUNCH_CWD)
    check("check() on a run with no activity.jsonl reports nothing, no traceback",
          v2 == [] and u2 == [] and c2 == [])


# ------------------------------------------------------------------ main() end-to-end
#
# Subprocess against a COPIED fleet in a temp dir and a temp HOME -- the
# `test_show_board.py` precedent. Never the live tree, never the live `.graph/CURRENT`,
# never this run's own real transcripts.

def build_fleet(tmp, run_id, state, activity_events=None):
    """A minimal copy of the fleet: the script under test, verify-state.py, one run."""
    graph = os.path.join(tmp, ".graph")
    runs = os.path.join(graph, "runs")
    os.makedirs(runs)
    shutil.copy(VERIFY_PATH, os.path.join(graph, "verify-state.py"))
    shutil.copy(MODULE_PATH, os.path.join(graph, "check-return-cap.py"))
    if os.path.isfile(SCHEMA_PATH):
        shutil.copy(SCHEMA_PATH, os.path.join(runs, "_schema.json"))
    run_dir = os.path.join(runs, run_id)
    os.makedirs(run_dir)
    with open(os.path.join(run_dir, "state.json"), "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    if activity_events is not None:
        with open(os.path.join(run_dir, "activity.jsonl"), "w", encoding="utf-8") as fh:
            for event in activity_events:
                fh.write(json.dumps(event) + "\n")
    return os.path.join(graph, "check-return-cap.py")


def run_cli(script, run_id, cwd, home):
    """(stdout, stderr, exit code), mirroring a real CLI invocation with HOME redirected.

    `os.path.expanduser` reads `USERPROFILE` on this platform (checked: `HOME` alone is
    NOT honoured here), so the child process's env is what carries the fake HOME across
    the subprocess boundary -- an in-process monkeypatch of `os.path.expanduser` cannot
    reach into a separate `python` process at all.
    """
    env = dict(os.environ)
    env["USERPROFILE"] = home
    env["HOME"] = home
    proc = subprocess.run([sys.executable, script, run_id], cwd=cwd,
                           capture_output=True, text=True, env=env)
    return proc.stdout, proc.stderr, proc.returncode


STATE = {"status": "building"}

with tempfile.TemporaryDirectory() as tmp:
    launch_cwd = os.path.join(tmp, "launch-cwd")
    os.makedirs(launch_cwd)
    # The exact string a child process reports for its own cwd is platform-decided;
    # ask a real python process rather than assume this script's own tmp path string
    # survives unchanged, so the fixture and the code under test agree on cwd's spelling.
    probe = subprocess.run([sys.executable, "-c",
                             "import os,sys; sys.stdout.write(os.getcwd())"],
                            cwd=launch_cwd, capture_output=True, text=True)
    real_cwd = probe.stdout

    home = os.path.join(tmp, "home")
    projects_root = os.path.join(home, ".claude", "projects", crc.encode_cwd(real_cwd))

    # -- a run with no activity.jsonl at all
    fleet1 = os.path.join(tmp, "fleet1")
    os.makedirs(fleet1)
    script = build_fleet(fleet1, "r-empty", STATE, activity_events=None)
    out, err, code = run_cli(script, "r-empty", launch_cwd, home)
    check("main(): a run with no activity.jsonl exits 0", code == 0)
    check("main(): a run with no activity.jsonl prints no traceback",
          "Traceback" not in err)
    check("main(): a run with no activity.jsonl says there is nothing to check",
          "nothing to check" in out)

    # -- a run whose id does not exist at all
    fleet2 = os.path.join(tmp, "fleet2")
    os.makedirs(fleet2)
    script = build_fleet(fleet2, "r-real", STATE, activity_events=None)
    out, err, code = run_cli(script, "no-such-run-id", launch_cwd, home)
    check("main(): an unknown run id exits 0, never a violation", code == 0)
    check("main(): an unknown run id prints no traceback", "Traceback" not in err)

    # -- a mixed run: one compliant builder, one over-cap builder, one unverifiable
    fleet3 = os.path.join(tmp, "fleet3")
    os.makedirs(fleet3)
    events = [
        {"t": 1, "ev": "start", "agent": "builder", "id": "ok1"},
        {"t": 2, "ev": "start", "agent": "builder", "id": "bad1"},
        {"t": 3, "ev": "start", "agent": "reviewer", "id": "ghost1"},
    ]
    script = build_fleet(fleet3, "r-mixed", STATE, activity_events=events)
    write_transcript(projects_root, "sessM", "ok1", "l1\nl2\nl3")
    write_transcript(projects_root, "sessM", "bad1", "l1\nl2\nl3\nl4")
    # ghost1 gets no transcript -- unverifiable.
    out, err, code = run_cli(script, "r-mixed", launch_cwd, home)
    check("main(): an over-cap return in the mix makes the CLI exit 1", code == 1)
    check("main(): the CLI reports the word 'unverifiable' for the missing transcript",
          "unverifiable" in out)
    check("main(): the CLI never prints a traceback even with a real violation present",
          "Traceback" not in err)
    check("main(): the CLI never echoes the checked transcript text",
          "l1\nl2\nl3\nl4" not in out)

    # -- an all-compliant run
    fleet4 = os.path.join(tmp, "fleet4")
    os.makedirs(fleet4)
    events2 = [{"t": 1, "ev": "start", "agent": "builder", "id": "ok2"}]
    script = build_fleet(fleet4, "r-clean", STATE, activity_events=events2)
    write_transcript(projects_root, "sessC", "ok2", "l1\nl2\nl3")
    out, err, code = run_cli(script, "r-clean", launch_cwd, home)
    check("main(): an all-compliant run exits 0", code == 0)
    check("main(): an all-compliant run reports no traceback", "Traceback" not in err)


passed = sum(1 for _, ok in checks if ok)
print("%d/%d checks passed" % (passed, len(checks)))
if passed != len(checks):
    sys.exit(1)
