#!/usr/bin/env python
"""Verify the one invariant: no app imports, requires, or reaches into another app.

    python graph_agents/.graph/verify-invariant.py              # every registered app
    python graph_agents/.graph/verify-invariant.py <path> ...   # one file or one app dir

Exit 0 clean, 1 if any violation, 2 if the registry cannot be read or parsed.

What counts as a violation is deliberately narrow: a line that is *import syntax* whose
target is a RELATIVE path which, resolved against the importing file's own directory,
lands inside a DIFFERENT registered app or inside `graph_agents/`. That is the mechanical
form of the constitution's test -- if the other directory disappeared, the build breaks.

What deliberately does NOT count, because none of it is an edge:
  - bare package specifiers (`react`, `@huntstack/db`) -- a name, not a path. huntstack's
    pnpm workspaces are internal organisation and stay internal by construction here.
  - relative paths that stay inside the importing app.
  - an app's name appearing in prose, JSON config, or a comment. Only lines matching
    import syntax are examined, so `registry.json`'s own `path` fields and CLAUDE.md's
    layout diagram are invisible to this check.

Python has no relative-path import literal, so `sys.path` insertion of a relative
directory is treated as the Python analogue of `require('../other-app')`: it is the way a
.py file actually reaches into a sibling repo.

This is a checker: pure stdlib, no network, and it never writes.
"""
import json, os, re, sys

FLEET = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UMBRELLA = os.path.dirname(FLEET)
REGISTRY = os.path.join(FLEET, "portfolio", "registry.json")

SOURCE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py")

# Dependency trees, VCS metadata and build output are not the app's own source.
SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "__pycache__",
    ".venv", "venv", "site-packages",
}

_STR = r"""['"]([^'"\n]+)['"]"""
PATTERNS = (
    re.compile(r"""(?:^|[\s;{}])(?:import|export)\b[^;'"\n]*\bfrom\s+""" + _STR),
    re.compile(r"""(?:^|[\s;{}])import\s+""" + _STR),                  # side-effect import
    re.compile(r"""\b(?:require|import)\s*\(\s*""" + _STR),            # require() / import()
    re.compile(r"""\bsys\.path\.(?:insert|append)\s*\([^)\n]*?""" + _STR),
)


def load_registry():
    """The registered apps as [(id, realpath), ...]. Unreadable registry is fatal."""
    try:
        with open(REGISTRY, encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError as exc:
        # UnicodeDecodeError and JSONDecodeError are both ValueError.
        die("malformed JSON in %s: %s" % (REGISTRY, exc))
    except OSError as exc:
        die("cannot read %s: %s" % (REGISTRY, exc))

    apps = data.get("apps") if isinstance(data, dict) else None
    if not isinstance(apps, list) or not apps:
        die("%s has no 'apps' list -- nothing to check" % REGISTRY)

    out = []
    for app in apps:
        if not isinstance(app, dict):
            continue
        app_id = app.get("id")
        path = app.get("path") or app_id
        if not app_id or not path:
            continue
        # Every kind counts, both ways round: a vendor drop or a tool is just as
        # forbidden an import TARGET as a product is.
        out.append((app_id, resolve(os.path.join(UMBRELLA, path))))
    if not out:
        die("%s lists no usable apps -- nothing to check" % REGISTRY)
    return out


def resolve(path):
    """Absolute, forward-slashed, junction/symlink-resolved. Never raises.

    `repos/.claude` is a directory junction into `graph_agents/.claude`, so fleet files
    have two valid absolute paths. Resolve before comparing or the same file is both
    inside and outside the fleet depending on how it was named.
    """
    try:
        real = os.path.realpath(path)
    except Exception:
        real = path
    if not os.path.isabs(str(real)):
        try:
            real = os.path.abspath(real)
        except Exception:
            pass
    return str(real).replace("\\", "/")


def owner(path, boundaries):
    """Which boundary (app id, or 'graph_agents') contains this resolved path."""
    for name, root in boundaries:
        if path == root or path.startswith(root + "/"):
            return name
    return None


def candidates(line):
    """The relative-path targets of any import-like syntax on this line."""
    found = []
    for pattern in PATTERNS:
        for spec in pattern.findall(line):
            if spec.startswith("./") or spec.startswith("../"):
                found.append(spec)
    return found


def check_file(path, boundaries):
    """Violations in one source file, as ["file:line: imports/requires X ...", ...].

    Silent for anything that is not source, or that lives outside every registered app:
    the fleet's own tooling is allowed to name app directories.
    """
    real = resolve(path)
    if not real.endswith(SOURCE_EXT) or not os.path.isfile(real):
        return []
    home = owner(real, boundaries)
    if home is None or home == "graph_agents":
        return []

    here = os.path.dirname(real)
    try:
        with open(real, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return []

    violations = []
    for number, line in enumerate(lines, 1):
        for spec in candidates(line):
            target = owner(resolve(os.path.join(here, spec)), boundaries)
            if target is not None and target != home:
                violations.append("%s:%d: imports/requires %s which resolves into %s"
                                  % (real, number, spec, target))
    return violations


def walk(root, boundaries):
    """Every source file under a directory, checked."""
    violations = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            if name.endswith(SOURCE_EXT):
                violations.extend(check_file(os.path.join(dirpath, name), boundaries))
    return violations


def die(message):
    sys.stderr.write("verify-invariant: %s\n" % message)
    raise SystemExit(2)


def main(argv):
    apps = load_registry()
    boundaries = apps + [("graph_agents", resolve(FLEET))]

    targets = [resolve(a) for a in argv] if argv else [root for _, root in apps]

    violations = []
    for target in targets:
        if os.path.isdir(target):
            violations.extend(walk(target, boundaries))
        elif os.path.isfile(target):
            violations.extend(check_file(target, boundaries))
        elif argv:
            die("no such file or directory: %s" % target)
        # A registered app with no directory on disk is the registry's problem, not
        # this check's: stay silent rather than fail the invariant for it.

    if violations:
        for line in violations:
            print(line)
        print("verify-invariant: %d cross-app import(s) FOUND" % len(violations))
        return 1

    print("verify-invariant: clean -- %d target(s), no cross-app imports"
          % len(targets))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
