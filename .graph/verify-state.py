#!/usr/bin/env python
"""Verify that a node actually wrote its key in a run's state.json.

    python graph_agents/.graph/verify-state.py <run-id> <key> [<key> ...]

Exit 0 only if EVERY named key exists and is non-empty. Anything else exits 1 and
names the offending key on stderr. Dotted keys walk nested objects: `reviews.s1`,
`builders.s2`.

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


def main(argv):
    if len(argv) < 2:
        die("usage: verify-state.py <run-id> <key> [<key> ...]")

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
        elif placeheld and value == placeholder:
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
