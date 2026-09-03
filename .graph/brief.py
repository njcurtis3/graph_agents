#!/usr/bin/env python
"""Render one run's state.json as a board a human can read in one glance.

    python graph_agents/.graph/brief.py             # the open run (.graph/CURRENT)
    python graph_agents/.graph/brief.py <run-id>
    python graph_agents/.graph/brief.py --ascii <run-id>

    2026-09-02-date-accuracy | huntstack | building | gate ok
      goal   Fix the UTC off-by-one so season dates render the day the regulation says
      scout      ok  9 facts | 2 unknowns | 1 risk
      architect  ok  single-loop | 3 slices
      s1  build done       review PASS
      s2  build done       review .. waiting
      s3  build --         review --
      now  builder | 7m | 88 tools | last Edit
      detail  graph_agents/.graph/runs/2026-09-02-date-accuracy/state.json

Why this exists. `GRAPH.md` §3 splits a run into two channels and this fills the second
one. `state.json` is the MACHINE channel -- the edge between nodes that cannot see each
other -- and it is deliberately unbudgeted: a builder's `changed` entry runs to a
paragraph per file because the reviewer needs that. The HUMAN channel is the main tab,
and until now it was fed by pasting the machine channel into it. A run then reads as
several thousand words of correct, necessary, unreadable detail.

Nothing here is new information. Every line is DERIVED from `state.json` plus
`activity.jsonl`, both of which the fleet already writes. That is the whole design: a
board no node authors cannot drift from the run, cannot be forged, and costs no node a
single token. The moment a node is asked to write the summary too, it can lie about it
-- the same argument `verify-state.py --audit` makes against trusting a node's own
account of whether it wrote its key.

The placeholder rules live in `verify-state.py` and are imported, not restated: a run
opened from `_schema.json` has non-empty template text in every key, and a board that
read that as work would show a run where nothing has happened as fully built.
`importlib` rather than `import` because the filename is hyphenated -- same reuse as
`.claude/hooks/flag-state-gap.py`.

Read-only, pure stdlib, and it never raises on a partial run: mid-flight, with most keys
still unwritten, is the case it exists for.
"""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
UMBRELLA = os.path.dirname(os.path.dirname(HERE))
RUNS = os.path.join(HERE, "runs")
CURRENT = os.path.join(HERE, "CURRENT")
VERIFY = os.path.join(HERE, "verify-state.py")

GOAL_WIDTH = 76
CLOSED = ("done", "blocked", "parked")

UNICODE = {"sep": "·", "ok": "✓", "no": "⛔",
           "none": "—", "run": "…"}
ASCII = {"sep": "|", "ok": "ok", "no": "!!", "none": "--", "run": ".."}


def glyphs(force_ascii):
    """Unicode where the console can take it. Windows consoles often cannot."""
    if force_ascii:
        return ASCII
    encoding = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        "".join(UNICODE.values()).encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return ASCII
    return UNICODE


# ------------------------------------------------------------------- state

def _verifier():
    """`verify-state.py` as a module, or None. A missing one degrades, never dies."""
    try:
        spec = importlib.util.spec_from_file_location("verify_state", VERIFY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def _empty(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, dict):
        return all(_empty(v) for v in value.values())
    if isinstance(value, list):
        return all(_empty(v) for v in value)
    return False


def _fallback_resolve(state, key):
    node = state
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


class Reader(object):
    """The three questions this board asks of a state file, however it can answer them.

    With `verify-state.py` present these ARE its rules, which is the point: two
    definitions of "written" would eventually disagree, and then the board would show a
    slice as built that the audit calls unwritten. Without it, an empty-check alone --
    degraded and saying so, rather than absent.
    """

    def __init__(self):
        self.verify = _verifier()
        self.template = self.verify.load_template() if self.verify else {}

    def resolve(self, state, key):
        if self.verify:
            return self.verify.resolve(state, key)
        return _fallback_resolve(state, key)

    def get(self, state, key, default=None):
        found, value = self.resolve(state, key)
        return value if found else default

    def written(self, state, key):
        """True when a node actually wrote this key -- not empty, not template text."""
        if self.verify:
            return not self.verify.unwritten(state, self.template, key)
        found, value = self.resolve(state, key)
        return bool(found) and not _empty(value)

    def slices(self, state):
        """Every slice this run knows about: planned, or written by some node."""
        if self.verify:
            return self.verify.real_slices(state, self.template)
        ordered, seen = [], set()
        plan = self.get(state, "architect.plan")
        if isinstance(plan, list):
            for entry in plan:
                if isinstance(entry, dict) and isinstance(entry.get("slice"), str):
                    if entry["slice"] not in seen:
                        seen.add(entry["slice"])
                        ordered.append(entry["slice"])
        for group in ("builders", "reviews"):
            node = self.get(state, group)
            if isinstance(node, dict):
                for key in node:
                    if key not in seen:
                        seen.add(key)
                        ordered.append(key)
        return ordered


def open_run():
    """The run `.graph/CURRENT` names, closed or not.

    Unlike `record-activity.py`, which goes silent on a closed run because there is
    nothing left to record, a board for a run that just finished is exactly what someone
    asks for when it finishes.
    """
    try:
        with open(CURRENT, encoding="utf-8") as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def load_state(run_id):
    path = run_id if run_id.endswith(".json") else os.path.join(RUNS, run_id, "state.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh), path


# ----------------------------------------------------------------- activity

def read_activity(run_dir):
    """`activity.jsonl` grouped per node instance. Absent or broken -> nothing shown.

    Grouped by `agent_id`, which is what makes a re-review's fresh reviewer its own lane
    rather than folded into the one it replaced. Orchestrator events carry no id and
    group under their own name.
    """
    path = os.path.join(run_dir, "activity.jsonl")
    lanes, order, total = {}, [], 0
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(event, dict):
                    continue
                stamp = event.get("t")
                if not isinstance(stamp, (int, float)):
                    continue
                agent = str(event.get("agent") or "?")
                key = str(event.get("id") or agent)
                total += 1
                lane = lanes.get(key)
                if lane is None:
                    lane = lanes[key] = {"agent": agent, "first": stamp, "last": stamp,
                                         "tools": 0, "tool": "", "stopped": False}
                    order.append(key)
                lane["last"] = stamp
                if event.get("ev") == "tool":
                    lane["tools"] += 1
                    lane["tool"] = str(event.get("tool") or "")
                elif event.get("ev") == "stop":
                    lane["stopped"] = True
    except OSError:
        return [], 0
    return [lanes[k] for k in order], total


def elapsed(seconds):
    seconds = int(max(0, seconds))
    if seconds < 90:
        return "%ds" % seconds
    if seconds < 5400:
        return "%dm" % round(seconds / 60.0)
    return "%dh%02dm" % (seconds // 3600, (seconds % 3600) // 60)


# -------------------------------------------------------------------- board

def count(value, noun, plural=None):
    """`2 facts`, `1 fact`. This is the human channel; "1 unknowns" reads as sloppy."""
    n = len(value) if isinstance(value, (list, dict)) else 0
    return "%d %s" % (n, noun if n == 1 else (plural or noun + "s"))


def relative(path):
    """Umbrella-relative where possible.

    Against `repos/`, never against cwd. Every path this fleet writes is relative to the
    umbrella root (`CLAUDE.md` § launch rule), and cwd is not reliably that: a hook
    inherits whatever directory the session happens to sit in, so a cwd-relative line
    renders differently depending on who is printing it and pastes back into nothing.
    An absolute `C:\\Users\\...` line is the fallback, for a run that genuinely lives
    outside the umbrella.
    """
    try:
        rel = os.path.relpath(path, UMBRELLA)
    except ValueError:                     # different drive on Windows
        rel = path
    if rel.startswith(".." + os.sep) or os.path.isabs(rel):
        rel = path
    return rel.replace("\\", "/")


def clip(text, width=GOAL_WIDTH, tail="..."):
    text = " ".join(str(text or "").split())
    return text if len(text) <= width else text[:width - len(tail)].rstrip() + tail


def slice_row(reader, state, sid, plan, g, width):
    """One slice: what its builder did, and what its reviewer said about it."""
    built = reader.written(state, "builders.%s" % sid)
    reviewed = reader.written(state, "reviews.%s" % sid)

    build = ""
    if built:
        build = str(reader.get(state, "builders.%s.status" % sid) or "").strip() or "done"
        attempt = reader.get(state, "builders.%s.attempt" % sid)
        if isinstance(attempt, int) and attempt > 1:
            build += " (try %d)" % attempt
    else:
        build = g["none"]

    if reviewed:
        review = str(reader.get(state, "reviews.%s.verdict" % sid) or "?").strip().upper()
        tries = reader.get(state, "reviews.%s.attempt" % sid)
        if isinstance(tries, int) and tries > 1:
            review += " (try %d)" % tries
    elif built:
        review = "%s waiting" % g["run"]
    else:
        review = g["none"]

    tail = ""
    entry = plan.get(sid)
    if isinstance(entry, dict):
        if str(entry.get("risk") or "").strip().lower() == "high":
            tail = "  [high risk]"
    elif built or reviewed:
        # A slice no approved plan contains. `builders.closing_fix` in
        # 2026-08-25-fleet-hardening is the case: real work, off the gate.
        tail = "  [off-plan]"

    return "  %-*s  build %-13s review %s%s" % (width, sid, build, review, tail)


def board(state, path, g):
    """The whole board, as lines. A half-written run is the normal case, not an error."""
    reader = Reader()
    lines = []

    status = str(reader.get(state, "status") or "?").strip()
    gate = reader.get(state, "approved_by_human") is True
    lines.append("%s %s %s %s %s %s gate %s" % (
        reader.get(state, "run_id") or os.path.basename(os.path.dirname(path)),
        g["sep"], reader.get(state, "app") or "?",
        g["sep"], status,
        g["sep"], g["ok"] if gate else "%s NOT APPROVED" % g["no"]))
    lines.append("  goal   %s" % clip(reader.get(state, "goal")))

    if reader.written(state, "scout"):
        lines.append("  scout      %s  %s %s %s %s %s" % (
            g["ok"], count(reader.get(state, "scout.facts"), "fact"), g["sep"],
            count(reader.get(state, "scout.unknowns"), "unknown"), g["sep"],
            count(reader.get(state, "scout.risks"), "risk")))
    else:
        lines.append("  scout      %s" % g["none"])

    plan = {}
    entries = reader.get(state, "architect.plan")
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("slice"), str):
                plan[entry["slice"]] = entry
    if reader.written(state, "architect"):
        lines.append("  architect  %s  %s %s %s" % (
            g["ok"], str(reader.get(state, "architect.shape") or "?").strip(),
            g["sep"], count(plan, "slice")))
    else:
        lines.append("  architect  %s" % g["none"])

    ids = reader.slices(state)
    width = max([len(s) for s in ids] + [9])
    for sid in ids:
        lines.append(slice_row(reader, state, sid, plan, g, width))

    if reader.written(state, "integrator"):
        lines.append("  integrator %s  %s merged %s %s" % (
            g["ok"], count(reader.get(state, "integrator.merged"), "branch", "branches"),
            g["sep"],
            count(reader.get(state, "integrator.conflicts"), "conflict")))
    if reader.written(state, "ops"):
        lines.append("  ops        %s  %s" % (
            g["ok"], count(reader.get(state, "ops.actions"), "action")))

    # The live lane. `state.json` moves only when a node FINISHES, so a run in flight is
    # invisible in it; this is the half that shows the run is still moving.
    lanes, total = read_activity(os.path.dirname(path))
    if lanes:
        now = time.time()
        if status.lower() not in CLOSED:
            running = [l for l in lanes
                       if not l["stopped"] and l["agent"] != "orchestrator"]
            for lane in running[-4:]:
                lines.append("  now  %s %s %s %s %d tools %s last %s" % (
                    lane["agent"], g["sep"], elapsed(now - lane["first"]),
                    g["sep"], lane["tools"], g["sep"], lane["tool"] or "?"))
        span = max(l["last"] for l in lanes) - min(l["first"] for l in lanes)
        nodes = [l for l in lanes if l["agent"] != "orchestrator"]
        lines.append("  activity   %d events %s %s %s %s" % (
            total, g["sep"], count(nodes, "node"), g["sep"], elapsed(span)))

    lines.append("  detail  %s" % relative(path))
    return lines


def main(argv):
    force_ascii = "--ascii" in argv
    argv = [a for a in argv if a != "--ascii"]
    g = glyphs(force_ascii)

    run_id = argv[0] if argv else open_run()
    if not run_id:
        sys.stderr.write("brief: no run given, and .graph/CURRENT names none\n")
        return 1
    try:
        state, path = load_state(run_id)
    except (OSError, ValueError) as exc:
        sys.stderr.write("brief: cannot read run %s (%s)\n" % (run_id, exc))
        return 1
    if not isinstance(state, dict):
        sys.stderr.write("brief: %s is not a JSON object\n" % path)
        return 1

    for line in board(state, path, g):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
