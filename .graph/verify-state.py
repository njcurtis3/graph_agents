#!/usr/bin/env python
"""Verify that a node actually wrote its key in a run's state.json.

    python graph_agents/.graph/verify-state.py <run-id> <key> [<key> ...]
    python graph_agents/.graph/verify-state.py --audit <run-id>

Exit 0 only if EVERY named key exists and is non-empty. Anything else exits 1 and
names the offending key on stderr. Dotted keys walk nested objects: `reviews.s1`,
`builders.s2`.

`--audit` is the hook-firable half, added 2026-08-26. The named-key mode above can
only run when someone already knows WHICH node just finished, so it can only ever be
called by hand. A PostToolUse hook sees a file path and nothing else, so it cannot ask
that question at all. `--audit` asks the one a lone state.json can answer instead:
given everything written so far, did the graph's EDGES hold? Builders before the human
gate, a review with no build behind it, a fan-in over a slice that never passed, a run
closed with a slice still unreviewed, a key filled in around template text still left
in place. It names no node and needs no argument beyond the run.

The two modes are complementary, not redundant: `--audit` never reports a key as
merely unwritten mid-run (that is what a run in progress looks like), and the named-key
mode never notices ordering. Keep both.

"Non-empty" is the whole point. A node that wrote `{}`, `[]`, `""`, or a dict whose
values are all empty did NOT do its job. Presence alone is not evidence of work.

Neither is a non-empty PLACEHOLDER. `feature-graph` step 1 opens a run by copying
`_schema.json`, whose values are all descriptive strings, so an untouched key is
non-empty and would sail through. A value byte-identical to the one in the template
is therefore treated as unwritten too. Without this the check is green in exactly
the situation it exists to catch: a run where no node has executed.

This is a checker: pure stdlib, no network, and it never writes.
"""
import json, os, sys

RUNS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
SCHEMA = os.path.join(RUNS, "_schema.json")


def is_empty(value):
    """True when the value carries no work. Recurses: all-empty children == empty."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, dict):
        return all(is_empty(v) for v in value.values())
    if isinstance(value, list):
        return all(is_empty(v) for v in value)
    return False  # numbers and booleans are real values


def state_path(run_id):
    """A run id, or a direct path to a state.json."""
    if run_id.endswith(".json"):
        return run_id
    return os.path.join(RUNS, run_id, "state.json")


def load(run_id):
    path = state_path(run_id)
    if not os.path.isfile(path):
        die("no such run: %s (looked for %s)" % (run_id, path))
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), path
    except ValueError as exc:
        # UnicodeDecodeError and JSONDecodeError are both ValueError. PowerShell
        # redirection writes UTF-16-with-BOM, which is the former, not the latter.
        die("malformed JSON in %s: %s" % (path, exc))
    except OSError as exc:
        die("cannot read %s: %s" % (path, exc))


def load_template():
    """The run template. A missing or broken one degrades to the empty-check alone."""
    try:
        with open(SCHEMA, encoding="utf-8") as fh:
            template = json.load(fh)
    except (OSError, ValueError) as exc:
        sys.stderr.write("verify-state: WARNING: cannot read %s (%s) -- checking for "
                         "empty values only, untouched placeholders will pass\n"
                         % (SCHEMA, exc))
        return {}
    if not isinstance(template, dict):
        sys.stderr.write("verify-state: WARNING: %s is not a JSON object -- checking for "
                         "empty values only, untouched placeholders will pass\n" % SCHEMA)
        return {}
    return template


def resolve(state, key):
    """Walk a dotted key. Returns (found, value)."""
    node = state
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def die(message):
    sys.stderr.write("verify-state: %s\n" % message)
    raise SystemExit(1)


# ---------------------------------------------------------------- audit mode

# `_schema.json` describes ONE generic slice, `s1`. A real run has s1..sN, all of the
# same shape, so placeholder identity for `builders.s7` is judged against `builders.s1`.
GENERIC = {"builders": "s1", "reviews": "s1"}

# Which node is allowed to write which key. `written_by` (added 2026-08-26) is the only
# authorship this file has ever recorded; before it, "never rewrite another node's key"
# was unverifiable by construction -- an orchestrator hand-writing all six keys read
# exactly like six nodes doing their jobs.
OWNER = {"scout": "scout", "architect": "architect", "integrator": "integrator",
         "ops": "ops", "builders": "builder", "reviews": "reviewer"}


def owner_of(key):
    """The node that must have written this key, or None if nobody owns it."""
    head = key.split(".")[0]
    return OWNER.get(head)


def template_slot(template, key):
    """The template value a real key should be compared against. (found, value)."""
    parts = key.split(".")
    if len(parts) == 2 and parts[0] in GENERIC:
        parts[1] = GENERIC[parts[0]]
    return resolve(template, ".".join(parts))


def is_untouched(value, tpl):
    """True when nothing in `value` is evidence that a node wrote it.

    Byte-equality against the template is not enough, and 2026-08-26 proved it: adding
    `written_by` to `_schema.json` made every OLD run's untouched `integrator` key stop
    matching the new template, so the audit called it written and then complained about
    the template text inside it. A template that may grow cannot be compared whole.

    So: evidence of writing is a string leaf that differs from the template's, a key the
    template does not have, or content in a list the template left empty. Numbers and
    booleans are no evidence either way -- that is blind spot (5), still open.
    """
    if isinstance(value, dict):
        if not isinstance(tpl, dict):
            return False
        return all(k in tpl and is_untouched(v, tpl[k]) for k, v in value.items())
    if isinstance(value, list):
        if not isinstance(tpl, list):
            return False
        if not tpl:
            return not value            # no exemplar to match, so any content is writing
        return all(is_untouched(item, tpl[0]) for item in value)
    if isinstance(value, str):
        return isinstance(tpl, str) and value == tpl
    return True


def unwritten(state, template, key):
    """True when a key is absent, empty, or still nothing but template text."""
    found, value = resolve(state, key)
    if not found or is_empty(value):
        return True
    placeheld, placeholder = template_slot(template, key)
    return bool(placeheld and is_untouched(value, placeholder))


def _leftover_placeholders(value, tpl, path, out):
    """Template STRINGS still sitting inside an otherwise-written key.

    Strings only, on purpose. A real `attempt: 1` or `gated: true` is byte-identical to
    the template's and always will be, so comparing numbers or booleans would report
    correct work as unfinished. `slice` is excluded for the same reason: the architect
    legitimately writes `"slice": "s1"`, which is exactly what the template says.
    """
    if isinstance(value, dict) and isinstance(tpl, dict):
        for k, v in value.items():
            # `written_by` is excluded because the authorship check below judges it
            # strictly harder -- it must equal the OWNING NODE's name, so leaving the
            # template's description there is already reported, once, as a wrong owner.
            if k in tpl and k not in ("slice", "$comment", "written_by"):
                _leftover_placeholders(v, tpl[k], "%s.%s" % (path, k) if path else k, out)
    elif isinstance(value, list) and isinstance(tpl, list) and tpl:
        for i, item in enumerate(value):
            _leftover_placeholders(item, tpl[0], "%s[%d]" % (path, i), out)
    elif isinstance(value, str) and isinstance(tpl, str):
        if value.strip() and value == tpl:
            out.append(path)


def slices(state):
    """Every slice id this run knows about, from the plan and from what nodes wrote."""
    found = []
    _, plan = resolve(state, "architect.plan")
    if isinstance(plan, list):
        for entry in plan:
            if isinstance(entry, dict) and isinstance(entry.get("slice"), str):
                found.append(entry["slice"])
    for group in ("builders", "reviews"):
        _, node = resolve(state, group)
        if isinstance(node, dict):
            found.extend(k for k in node)
    seen, ordered = set(), []
    for s in found:
        if s not in seen:
            seen.add(s)
            ordered.append(s)
    return ordered


def audit(state, template):
    """Edge violations visible in the state file alone. Empty list == nothing wrong.

    Only VIOLATIONS. A half-filled run is what work in progress looks like, so a key
    that is merely not written yet is never reported -- a hook that cried at every
    intermediate write would be turned off within a day, and then it checks nothing.
    """
    problems = []
    approved = resolve(state, "approved_by_human")[1] is True
    status = str(resolve(state, "status")[1] or "").strip().lower()
    known = slices(state)

    for s in known:
        built = not unwritten(state, template, "builders.%s" % s)
        reviewed = not unwritten(state, template, "reviews.%s" % s)
        verdict = str(resolve(state, "reviews.%s.verdict" % s)[1] or "").strip().upper()

        # The human gate is the one edge in this graph that exists to be blocking.
        if built and not approved:
            problems.append(
                "builders.%s is written but approved_by_human is not true -- the human "
                "gate (feature-graph step 4) was skipped or is recorded wrongly" % s)
        if reviewed and not built:
            problems.append(
                "reviews.%s is written but builders.%s is not -- a review with no build "
                "behind it reviews nothing" % (s, s))
        if status == "done" and not built:
            problems.append(
                "run is status 'done' but builders.%s was never written -- a planned "
                "slice was dropped, or the run closed early" % s)
        elif status == "done" and verdict != "PASS":
            problems.append(
                "run is status 'done' but reviews.%s is %s -- only PASS closes a slice"
                % (s, verdict or "unwritten"))

    if not unwritten(state, template, "integrator"):
        for s in known:
            v = str(resolve(state, "reviews.%s.verdict" % s)[1] or "").strip().upper()
            if v != "PASS":
                problems.append(
                    "integrator is written but reviews.%s is %s -- fan-in (step 6) runs "
                    "only when EVERY slice has passed" % (s, v or "unwritten"))

    # -- authorship. Every written node key must name the node that wrote it.
    node_keys = ["scout", "architect", "integrator", "ops"] + \
                ["builders.%s" % s for s in known] + ["reviews.%s" % s for s in known]
    written = [k for k in node_keys if not unwritten(state, template, k)]
    stamped = [k for k in written
               if isinstance(resolve(state, "%s.written_by" % k)[1], str)
               and resolve(state, "%s.written_by" % k)[1].strip()]

    if written and not stamped:
        # A run from before `written_by` existed, or one where nobody stamped anything.
        # ONE line, not one per key: the finding is "this run has no authorship at all",
        # and repeating it six times would bury the violations that differ.
        problems.append(
            "no key in this run is authorship-stamped -- `written_by` was added to "
            "_schema.json on 2026-08-26; runs opened before that are unverifiable on "
            "the never-rewrite-another-node's-key contract and stay that way")
    else:
        for key in written:
            expected = owner_of(key)
            actual = resolve(state, "%s.written_by" % key)[1]
            if key not in stamped:
                problems.append(
                    "%s is written but has no `written_by` -- an unstamped key in a run "
                    "that stamps the others is the shape of a key written by the wrong "
                    "node" % key)
            elif expected and str(actual).strip() != expected:
                problems.append(
                    "%s.written_by is %r but only `%s` may write that key -- this is the "
                    "contract violation `state.json` exists to prevent"
                    % (key, str(actual).strip(), expected))

    _, ops_actions = resolve(state, "ops.actions")
    if not is_empty(ops_actions) and not approved:
        problems.append(
            "ops.actions is non-empty but approved_by_human is not true -- ops always "
            "runs behind its own gate (feature-graph step 7)")

    # Blind spot (6) from the list below: a key filled in AROUND template text.
    for key in ["scout", "architect", "integrator", "ops"] + \
               ["builders.%s" % s for s in known] + ["reviews.%s" % s for s in known]:
        if unwritten(state, template, key):
            continue
        found, value = resolve(state, key)
        placeheld, tpl = template_slot(template, key)
        if not (found and placeheld):
            continue
        leftovers = []
        _leftover_placeholders(value, tpl, key, leftovers)
        for path in leftovers:
            problems.append(
                "%s is still verbatim template text inside an otherwise-written key -- "
                "the node filled in around it" % path)

    for key in ("run_id", "goal", "app", "status"):
        if unwritten(state, template, key):
            problems.append("%s is unwritten or still the template's -- step 1 fills "
                            "these when the run is opened" % key)

    return problems


def main(argv):
    if argv and argv[0] == "--audit":
        if len(argv) != 2:
            die("usage: verify-state.py --audit <run-id>")
        run_id = argv[1]
        state, path = load(run_id)
        if not isinstance(state, dict):
            die("%s is not a JSON object" % path)
        problems = audit(state, load_template())
        if problems:
            for line in problems:
                sys.stderr.write("verify-state: %s\n" % line)
            sys.stderr.write("verify-state: %s -- %d edge violation(s)\n"
                             % (run_id, len(problems)))
            return 1
        print("verify-state: %s -- audit clean" % run_id)
        return 0

    if len(argv) < 2:
        die("usage: verify-state.py <run-id> <key> [<key> ...]\n"
            "       verify-state.py --audit <run-id>")

    run_id, keys = argv[0], argv[1:]
    state, path = load(run_id)
    if not isinstance(state, dict):
        die("%s is not a JSON object" % path)

    template = load_template()

    failures = []
    for key in keys:
        found, value = resolve(state, key)
        placeheld, placeholder = resolve(template, key)
        if not found:
            failures.append("%s: key not present" % key)
        elif is_empty(value):
            failures.append("%s: present but empty -- the node did not write it" % key)
        elif placeheld and is_untouched(value, placeholder):
            # Not `value == placeholder`: the template can gain fields (it gained
            # `written_by` on 2026-08-26), and whole-value equality silently passes
            # every key copied from an older version of it.
            failures.append("%s: still the schema placeholder -- the node did not "
                            "write it" % key)

    if failures:
        for line in failures:
            sys.stderr.write("verify-state: %s\n" % line)
        sys.stderr.write("verify-state: %s -- %d of %d key(s) FAILED\n"
                         % (run_id, len(failures), len(keys)))
        return 1

    print("verify-state: %s -- %d key(s) OK: %s" % (run_id, len(keys), ", ".join(keys)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
