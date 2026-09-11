"""Tests for record-activity.py's token accounting: encode_cwd, subagent_transcript_path,
tokens_used_by, and the main() wiring that attaches "tokens" to tool/stop lines.

Run: python test_record_activity.py
"""
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
MODULE_PATH = os.path.join(HERE, "record-activity.py")

spec = importlib.util.spec_from_file_location("record_activity", MODULE_PATH)
ra = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ra)

checks = []


def check(name, cond):
    checks.append((name, bool(cond)))
    if not cond:
        print("FAIL:", name)


# ---------- encode_cwd ----------

check("encode_cwd matches Claude Code's observed project-dir naming",
      ra.encode_cwd(r"C:\Users\natha\Desktop\repos") == "C--Users-natha-Desktop-repos")
check("encode_cwd leaves alnum runs alone",
      ra.encode_cwd("abcXYZ123") == "abcXYZ123")
check("encode_cwd handles a posix-style path too",
      ra.encode_cwd("/home/nathan/repos") == "-home-nathan-repos")

# ---------- subagent_transcript_path ----------

payload = {"cwd": r"C:\Users\natha\Desktop\repos", "session_id": "sess1", "agent_id": "abc123"}
p = ra.subagent_transcript_path(payload)
check("subagent_transcript_path builds the expected nested layout",
      p is not None and p.endswith(os.path.join("sess1", "subagents", "agent-abc123.jsonl")))
check("subagent_transcript_path returns None when cwd is missing",
      ra.subagent_transcript_path({"session_id": "s", "agent_id": "a"}) is None)
check("subagent_transcript_path returns None when session_id is missing",
      ra.subagent_transcript_path({"cwd": "c", "agent_id": "a"}) is None)
check("subagent_transcript_path returns None when agent_id is missing",
      ra.subagent_transcript_path({"cwd": "c", "session_id": "s"}) is None)

# ---------- tokens_used_by ----------

with tempfile.TemporaryDirectory() as tmp:
    good = os.path.join(tmp, "agent-x.jsonl")
    with open(good, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"message": {"usage": {
            "input_tokens": 2, "output_tokens": 100,
            "cache_creation_input_tokens": 50, "cache_read_input_tokens": 0}}}) + "\n")
        fh.write(json.dumps({"message": {"usage": {
            "input_tokens": 2, "output_tokens": 30,
            "cache_creation_input_tokens": 0, "cache_read_input_tokens": 150}}}) + "\n")
        fh.write("not json at all, a torn final line\n")
        fh.write(json.dumps({"message": {"role": "user"}}) + "\n")   # no usage block
    check("tokens_used_by sums every token field across every real turn",
          ra.tokens_used_by(good) == (2 + 100 + 50 + 0) + (2 + 30 + 0 + 150))

    empty = os.path.join(tmp, "agent-empty.jsonl")
    open(empty, "w").close()
    check("tokens_used_by on an empty file is 0, not None",
          ra.tokens_used_by(empty) == 0)

    check("tokens_used_by on a missing file returns None, never a fabricated 0",
          ra.tokens_used_by(os.path.join(tmp, "does-not-exist.jsonl")) is None)

# ---------- main() end-to-end, via a fake HOME + stdin ----------


def run_main_with(payload_dict, home_dir, fleet_dir):
    """Run main() with HOME redirected and CURRENT/state.json pointed at fleet_dir."""
    import io
    old_home = os.environ.get("HOMEPATH"), os.environ.get("USERPROFILE"), os.environ.get("HOME")
    old_expanduser = os.path.expanduser
    os.path.expanduser = lambda p: home_dir if p == "~" else old_expanduser(p)
    old_current = ra.CURRENT
    old_fleet = ra.FLEET
    ra.CURRENT = os.path.join(fleet_dir, ".graph", "CURRENT")
    ra.FLEET = fleet_dir
    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(json.dumps(payload_dict))
        ra.main()
    finally:
        sys.stdin = old_stdin
        os.path.expanduser = old_expanduser
        ra.CURRENT = old_current
        ra.FLEET = old_fleet


with tempfile.TemporaryDirectory() as tmp:
    fleet = os.path.join(tmp, "graph_agents")
    run_dir = os.path.join(fleet, ".graph", "runs", "r1")
    os.makedirs(run_dir)
    with open(os.path.join(fleet, ".graph", "CURRENT"), "w") as fh:
        fh.write("r1")
    with open(os.path.join(run_dir, "state.json"), "w") as fh:
        json.dump({"status": "building"}, fh)

    home = os.path.join(tmp, "home")
    subagents_dir = os.path.join(home, ".claude", "projects",
                                  ra.encode_cwd(r"C:\Users\test\repos"), "sessA", "subagents")
    os.makedirs(subagents_dir)
    with open(os.path.join(subagents_dir, "agent-b1.jsonl"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"message": {"usage": {
            "input_tokens": 1, "output_tokens": 999,
            "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}}}) + "\n")

    run_main_with({
        "hook_event_name": "PostToolUse", "tool_name": "Edit",
        "agent_type": "builder", "agent_id": "b1",
        "cwd": r"C:\Users\test\repos", "session_id": "sessA",
    }, home, fleet)

    with open(os.path.join(run_dir, "activity.jsonl"), encoding="utf-8") as fh:
        lines = [json.loads(l) for l in fh if l.strip()]
    check("main() wrote exactly one activity line", len(lines) == 1)
    check("main() attached the real token total from the subagent's transcript",
          lines and lines[0].get("tokens") == 1000)
    check("main() still records the tool name alongside tokens",
          lines and lines[0].get("tool") == "Edit")

    # A second tool event for an orchestrator-side call (no agent_id) must never
    # attempt token accounting -- there is no per-instance transcript to sum.
    run_main_with({
        "hook_event_name": "PostToolUse", "tool_name": "Read",
        "cwd": r"C:\Users\test\repos", "session_id": "sessA",
    }, home, fleet)
    with open(os.path.join(run_dir, "activity.jsonl"), encoding="utf-8") as fh:
        lines = [json.loads(l) for l in fh if l.strip()]
    check("an orchestrator-side event (no agent_id) carries no tokens field",
          "tokens" not in lines[-1])

    # A tool event whose subagent transcript does not exist yet must not raise
    # and must simply omit tokens.
    run_main_with({
        "hook_event_name": "PostToolUse", "tool_name": "Edit",
        "agent_type": "builder", "agent_id": "no-such-agent",
        "cwd": r"C:\Users\test\repos", "session_id": "sessA",
    }, home, fleet)
    with open(os.path.join(run_dir, "activity.jsonl"), encoding="utf-8") as fh:
        lines = [json.loads(l) for l in fh if l.strip()]
    check("a missing transcript omits tokens rather than raising or faking 0",
          "tokens" not in lines[-1])


passed = sum(1 for _, ok in checks if ok)
print("%d/%d checks passed" % (passed, len(checks)))
if passed != len(checks):
    sys.exit(1)
