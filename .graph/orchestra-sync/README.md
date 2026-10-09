# orchestra-sync

Carries graph_agents' fleet (agents, skills, hooks, scripts, `GRAPH.md`) into Orchestra's
vendored `orchestra/fleet/`. One-way, run by the owner, from `repos/`. Stdlib Python.

Tune the fleet here, test it here, then sync. Orchestra's copy is a render, never an
edit surface: a hand-edit in `orchestra/fleet/` makes the next sync refuse.

## Usage

```
python graph_agents/.graph/orchestra-sync/sync.py                  # write orchestra/fleet (default target sits beside graph_agents)
python graph_agents/.graph/orchestra-sync/sync.py --dry-run        # plan + refusals, write nothing
python graph_agents/.graph/orchestra-sync/sync.py --check          # every gate, write nothing
python graph_agents/.graph/orchestra-sync/sync.py --check --scope md
python graph_agents/.graph/orchestra-sync/sync.py --verify-upstream <commit>
python graph_agents/.graph/orchestra-sync/sync.py --verify-source orchestra/fleet
python graph_agents/.graph/orchestra-sync/sync.py --target <dir>   # default orchestra/fleet
```

- `--check` is the one to run while tuning. It does not need a clean tree.
- The write and `--dry-run` modes refuse a dirty upstream in any payload path (or in this
  directory): SOURCE names a commit, so commit first.
- `--verify-upstream <commit>` proves that marking changed nothing the umbrella runs:
  each payload file with its marker lines deleted must equal `git show <commit>:<file>`.
- `--verify-source <target>` proves SOURCE equals graph_agents HEAD and every file hash
  matches. Prints `SOURCE matches HEAD`.
- There is no force flag. Resolve a refusal by fixing upstream or reverting the hand-edit.

## What travels

`payload.json` `include` is an allowlist; anything unlisted never travels. `token` rewrites
every literal `graph_agents` to `@FLEET@` (rendered by Orchestra at install time).
`denylist` + the app ids read live from `portfolio/registry.json` form the leak gate: any
hit not covered by a `leak_allow` entry (file + pattern name + a reason) refuses. A missing
registry refuses. The gate also reads the name of every sibling directory of graph_agents under
the umbrella root live from disk (minus graph_agents and the target's own repo), plus their
hyphen/dot stems of 5+ letters not in `stem_stoplist`, so unregistered repos are covered; an
unreadable root refuses. Include entries must be relative forward-slash paths (no `..`,
backslash, drive letter); symlinks under the target refuse. Files dropped from `include` are deleted from the target on the next sync.
`README.md` in the target is Orchestra's: never read as payload, never written.

## Marking umbrella-only spans

Wrap a span in whole-line markers in the upstream file. Both forms are accepted anywhere;
use the comment form that is safe for the file:

```
<!-- umbrella:begin scout-registry -->      Markdown prose
...span...
<!-- umbrella:end scout-registry -->

# umbrella:begin guard-fallback             Python, YAML frontmatter, fenced bash
...span...
# umbrella:end guard-fallback
```

Rules: the marker is the whole line (indentation allowed); ids match
`[A-Za-z0-9][A-Za-z0-9._-]*`; no nesting; no mid-line spans; ids unique per kind (prose or
code) across the payload. The umbrella keeps running on the file with only the marker lines
deleted (`--verify-upstream` checks this).

## Alternates

Every marker needs an entry in `alternates/prose.md` (for `.md` files) or
`alternates/code.md` (for `.py`), keyed by marker id:

```
@@@ alt scout-registry pin=0123456789ab
Replacement lines, inserted where the span was. Empty body = drop the span.
@@@ end
```

`pin` is the first 12 hex of sha256 over the umbrella span (its lines, each ending `\n`).
Sync refuses on a marker with no entry, an entry with no marker (orphan), or a pin that no
longer matches, and prints the new hash. A pin mismatch means the span was tuned: re-read
the alternate against the new text, then re-pin. Drift is detected, not prevented.

JSON cannot carry markers. `alternates/json.json` holds pinned RFC 6901 patches instead:

```
{"patches": [{"file": ".claude/settings.json", "op": "remove|replace",
              "path": "/hooks/PreToolUse/1", "pin": "<12 hex of the old value>", "value": ...}]}
```

The pin is sha256 over the old value serialized with sorted keys and compact separators.
Patches apply in listed order, so remove higher list indexes first.

## Gates (all fail closed)

leak gate; every alternate pinned with no orphans; backticked `.claude/`, `.graph/` and
`@FLEET@/` paths in rendered prose resolve inside the payload; every settings hook
command (with `|| true` stripped) names a shipped script; sibling imports and
`<name>.py` literals resolve inside the payload; every `.py` compiles; smoke: the render
is placed in a temp project and each hook runs with stdin `{}` and must exit 0.

## SOURCE

`<target>/SOURCE` (JSON): upstream commit and date, tool version, the token, a sha256 per
file (LF-normalized, so another machine's autocrlf is not a hand-edit), dropped hooks,
unmanaged files. It is the authority for the refusal rule: sync refuses when a target file
is missing from it, differs from its hash, or a listed file is gone. The sync's own
uncommitted output matches SOURCE, which is why a re-run is idempotent before the owner commits.

## Tests

`python graph_agents/.graph/orchestra-sync/test_sync.py` builds throwaway repos in a temp
dir and never touches `orchestra/`.
