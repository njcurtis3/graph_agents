#!/usr/bin/env python
"""Review a finished run the way the 2026-08-28 `archive-adapters` review was done by
hand -- but data-backed, from `activity.jsonl` and `state.json` instead of a memory of
what happened.

    python graph_agents/.graph/postmortem.py            # the run .graph/CURRENT names
    python graph_agents/.graph/postmortem.py <run-id>

Read-only. Prints a report. Never writes, never gates, exit 0 unless the run cannot be
read at all.

**Why this exists.** That manual review is this fleet's single best-attested change: it
is what produced risk tagging (architect tags every slice `risk: high|low`, reviewer
depth follows). `activity.jsonl` now records what a manual review had to reconstruct from
memory -- tool counts, spawn order, which agent_id ran which slice's work -- so the same
review should not need a human rereading transcripts each time.

**What this deliberately does NOT compute, and why.** Gap #20 (`CURRENT-STATE.md`) is
still open: `activity.jsonl` carries `stop` events with no matching `start`, interleaved
with real work rather than clustering at a run's end. Reproduced live on this run,
2026-09-20-fleet-gaps: one scout spawn produced 1 `start` and 6 `stop` events. Exactly one
stop MATCHED the start and carried both `say` and `tokens` -- a real subagent whose
transcript the hook read. The other five carried neither `say` nor `tokens`: no transcript
existed at `~/.claude/projects/<encoded cwd>/<session_id>/subagents/agent-<id>.jsonl` for
the hook to read, so those five are PHANTOM, not merely unstarted.

That MATCHED / ORPHAN-WITH-EVIDENCE / PHANTOM split -- not `parent` -- is the real
discriminator this file uses. `parent` looked like the obvious field (record-activity.py
sets it from a payload's `parent_tool_use_id`) but is dead on arrival: 0 of the events
this fleet has ever collected carry it, because that field is never populated on the
payloads the hook receives. **This file does not read `parent`, on purpose** -- do not
re-add that read; there is nothing in the field to diagnose gap #20 with.

Anything computed from a `start`/`stop` PAIR is still unsound: no per-node wall-clock
duration, no "how long did this run take" number, anywhere below. An orphan-with-evidence
stop is real work, but it is still unattributable to any lane -- it has no `start` to pair
with, so a duration built from it would be no sounder than one built from a phantom.

What survives that pollution, and is all this file uses:
  - **Tool counts.** Every `tool` event carries the spawning node's real `agent_id`
    (record-activity.py tags it on every event, not just start/stop), so counting them
    per lane is unaffected by a phantom lane that contributes no tool events at all.
  - **Lane identity.** A stop is folded into a lane only once it is MATCHED -- its `id`
    also seen on a `start` or `tool` event. Orphan-with-evidence and phantom stops alike
    are excluded from every lane; that removes both without needing to know which real
    lane a stray stop belonged to.
  - **Tool-bounded windows.** A lane's first and last timestamp, taken only from its own
    `start`/`tool` events (never its `stop`), is a real, if slightly early, bound on when
    it was working. Two lanes' windows overlapping is evidence they ran concurrently;
    this does not depend on either lane's `stop` being the right one.

If gap #20 closes, add duration back here rather than trusting `brief.py`'s elapsed()
independently -- one definition of "how long", not two that can drift.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FLEET = os.path.dirname(HERE)
RUNS = os.path.join(HERE, "runs")
CURRENT = os.path.join(HERE, "CURRENT")
VERIFY = os.path.join(HERE, "verify-state.py")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------- activity

def read_lanes(run_dir):
    """(real_lanes, stop_classification). real_lanes: id -> {agent, first, last, tools,
    tool_counts}. stop_classification: {"total", "matched", "orphan", "phantom"} counts
    of every `stop` event in the run -- gap #20's real discriminator (see the top of this
    module for the field this replaced, and why it is not read):

      - **matched**: the stop's `id` also appears on a `start` or `tool` event -- it is
        folded into that lane, exactly as before.
      - **orphan** (orphan-with-evidence): no `start`, but the stop carries `say` or
        `tokens` -- a real subagent whose transcript the hook DID read; it just never got
        a `start` logged under this id. Real work, mis-attributed, not manufactured.
      - **phantom**: no `start` AND neither `say` nor `tokens` -- no subagent transcript
        existed for the hook to read at all.

    Orphan and phantom stops are both excluded from every lane -- unattributable to a
    lane either way, since without a `start` there is no tool-bounded window to hang them
    on.
    """
    path = os.path.join(run_dir, "activity.jsonl")
    lanes, real_ids = {}, set()
    classification = {"total": 0, "matched": 0, "orphan": 0, "phantom": 0}
    try:
        with open(path, encoding="utf-8") as fh:
            events = [json.loads(line) for line in fh if line.strip()]
    except (OSError, ValueError):
        return {}, classification

    for event in events:
        if not isinstance(event, dict):
            continue
        key = str(event.get("id") or event.get("agent") or "?")
        if event.get("ev") in ("start", "tool"):
            real_ids.add(key)

    for event in events:
        if not isinstance(event, dict):
            continue
        stamp = event.get("t")
        if not isinstance(stamp, (int, float)):
            continue
        key = str(event.get("id") or event.get("agent") or "?")
        if event.get("ev") == "stop":
            classification["total"] += 1
            if key in real_ids:
                classification["matched"] += 1
            elif event.get("say") or event.get("tokens"):
                classification["orphan"] += 1
            else:
                classification["phantom"] += 1
            continue
        if event.get("ev") not in ("start", "tool"):
            continue
        lane = lanes.get(key)
        if lane is None:
            lane = lanes[key] = {"agent": str(event.get("agent") or "?"),
                                  "first": stamp, "last": stamp,
                                  "tools": 0, "tool_counts": {}}
        lane["first"] = min(lane["first"], stamp)
        lane["last"] = max(lane["last"], stamp)
        if event.get("ev") == "tool":
            lane["tools"] += 1
            tool = str(event.get("tool") or "?")
            lane["tool_counts"][tool] = lane["tool_counts"].get(tool, 0) + 1

    return lanes, classification


def overlap(a, b):
    return a["first"] <= b["last"] and b["first"] <= a["last"]


# --------------------------------------------------------------------- report

def by_agent(lanes):
    """agent_type -> {lanes: n, tools: n, top_tool: (name, count) or None}."""
    out = {}
    for lane in lanes.values():
        bucket = out.setdefault(lane["agent"], {"lanes": 0, "tools": 0, "counts": {}})
        bucket["lanes"] += 1
        bucket["tools"] += lane["tools"]
        for tool, n in lane["tool_counts"].items():
            bucket["counts"][tool] = bucket["counts"].get(tool, 0) + n
    for bucket in out.values():
        bucket["top_tool"] = (max(bucket["counts"].items(), key=lambda kv: kv[1])
                              if bucket["counts"] else None)
    return out


def report(verify, state, run_id, run_dir):
    lines = []
    template = verify.load_template()
    app = verify.resolve(state, "app")[1] or "?"
    shape = verify.resolve(state, "architect.shape")[1] or "?"
    status = verify.resolve(state, "status")[1] or "?"
    lines.append("postmortem: %s (%s, shape %s, %s)" % (run_id, app, shape, status))
    lines.append("")
    lines.append("Duration/wall-clock omitted: gap #20 is still open, `stop` events are")
    lines.append("unreliable. Everything below is tool counts and tool-bounded windows,")
    lines.append("never a start/stop pair.")
    lines.append("")

    lanes, stops = read_lanes(run_dir)
    if not lanes and not stops["total"]:
        lines.append("No activity.jsonl (or it's empty) -- nothing to measure.")
        return "\n".join(lines)

    lines.append("## Tool activity")
    if stops["phantom"]:
        lines.append("  (%d phantom stop event(s) excluded -- gap #20)" % stops["phantom"])
    agents = by_agent(lanes)
    for agent in sorted(agents):
        b = agents[agent]
        top = " -- top: %s x%d" % b["top_tool"] if b["top_tool"] else ""
        lines.append("  %-12s %d lane(s), %d tool call(s)%s"
                     % (agent, b["lanes"], b["tools"], top))
    lines.append("")

    # ------------------------------------------------------ stop integrity
    lines.append("## Stop-event integrity")
    lines.append("  %d stop event(s): %d matched, %d orphan-with-evidence, %d phantom"
                 % (stops["total"], stops["matched"], stops["orphan"], stops["phantom"]))
    if stops["total"]:
        lines.append("  phantom ratio: %d/%d (%.0f%%)"
                     % (stops["phantom"], stops["total"],
                        100.0 * stops["phantom"] / stops["total"]))
    else:
        lines.append("  phantom ratio: n/a (no stop events)")
    lines.append("")

    # ---------------------------------------------------------- concurrency
    lines.append("## Concurrency")
    if shape != "diamond":
        lines.append("  shape is %s -- concurrency is not claimed, N/A" % shape)
    else:
        builder_lanes = [l for l in lanes.values() if l["agent"] == "builder"]
        if len(builder_lanes) < 2:
            lines.append("  diamond shape, but fewer than 2 builder lanes recorded --"
                         " cannot check overlap")
        else:
            pairs = 0
            overlapping = 0
            for i in range(len(builder_lanes)):
                for j in range(i + 1, len(builder_lanes)):
                    pairs += 1
                    if overlap(builder_lanes[i], builder_lanes[j]):
                        overlapping += 1
            lines.append("  %d builder lane(s), %d/%d pair(s) overlap in their "
                         "tool-bounded windows" % (len(builder_lanes), overlapping, pairs))
            lines.append("  %s" % ("genuinely concurrent" if overlapping
                                   else "spawned together, but no overlap observed -- "
                                        "not proven concurrent"))
    lines.append("")

    # -------------------------------------------------------------- slices
    lines.append("## Slices: round-trips and risk fit")
    slices = verify.real_slices(state, template)
    _, plan = verify.resolve(state, "architect.plan")
    risk_of = {}
    if isinstance(plan, list):
        for entry in plan:
            if isinstance(entry, dict) and isinstance(entry.get("slice"), str):
                risk_of[entry["slice"]] = str(entry.get("risk") or "").strip().lower()

    buckets = {"high": [0, 0], "low": [0, 0], "": [0, 0]}   # [looped, total]
    if not slices:
        lines.append("  no slices to report")
    for sid in slices:
        _, review = verify.resolve(state, "reviews.%s" % sid)
        attempts = verify.review_attempts(review)
        looped = verify.ever_rejected(review)
        verdict = verify.slice_verdict(state, sid) or "unwritten"
        risk = risk_of.get(sid, "")
        bucket = buckets.setdefault(risk, [0, 0])
        bucket[1] += 1
        if looped:
            bucket[0] += 1
        lines.append("  %-6s risk=%-5s %s, attempt %d%s"
                     % (sid, risk or "?", verdict, len(attempts),
                        " (looped)" if looped else ""))
    lines.append("")

    real_buckets = {k: v for k, v in buckets.items() if v[1]}
    if len(real_buckets) > 1:
        lines.append("## Risk-tag fit")
        for risk in ("high", "low", ""):
            if risk not in real_buckets:
                continue
            looped, total = real_buckets[risk]
            lines.append("  risk=%-5s %d/%d slice(s) looped (%.0f%%)"
                         % (risk or "?", looped, total, 100.0 * looped / total))
        high = real_buckets.get("high")
        low = real_buckets.get("low")
        if high and low:
            high_rate = high[0] / high[1]
            low_rate = low[0] / low[1]
            if low_rate > high_rate:
                lines.append("  low-risk slices looped MORE than high-risk ones -- the "
                             "risk tag is not tracking what actually needed the deeper "
                             "review")
            elif high_rate > 0 and low_rate == 0:
                lines.append("  high-risk slices are where the loops are -- the tag is "
                             "earning its cost on this run")

    return "\n".join(lines)


def main(argv):
    run_id = argv[0] if argv else None
    if not run_id:
        try:
            with open(CURRENT, encoding="utf-8") as fh:
                run_id = fh.read().strip()
        except OSError:
            run_id = None
    if not run_id:
        sys.stderr.write("postmortem: no run given, and .graph/CURRENT names none\n")
        return 1

    verify = load_module(VERIFY, "verify_state")
    try:
        state, path = verify.load(run_id)
    except SystemExit:
        return 1
    if not isinstance(state, dict):
        sys.stderr.write("postmortem: %s is not a JSON object\n" % path)
        return 1

    run_dir = os.path.dirname(path)
    print(report(verify, state, run_id, run_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
