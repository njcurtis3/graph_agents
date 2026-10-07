#!/usr/bin/env python
"""Compute the facts a scout would otherwise re-derive by hand, every run.

    python graph_agents/.graph/scout-facts.py <app-id>
    python graph_agents/.graph/scout-facts.py --all
    python graph_agents/.graph/scout-facts.py <app-id> --json

Run from `repos/`, like everything else in the fleet.

WHY THIS EXISTS, and why it is a script rather than a cache
-----------------------------------------------------------
A per-app fact *store* was designed first and rejected on evidence. Two umbrella
runs' scout keys were checked against reality on 2026-08-28:

  "graph_agents/ is NOT a git repository"     (2026-08-25) — now FALSE, it is one
  "6 app directories: fleetview, huntstack,
   App 1, podcraft-ai, thrml, whoop-med-tracker" (2026-08-26) — now FALSE, there are 8
  "repos/ is NOT a git repository"            (2026-08-25) — still true

So scouts do repeat work, but the facts they repeat most are the ones that rot
fastest. A cache would have handed a later run a confident, wrong answer to
exactly the question that decides the graph's SHAPE — `GRAPH.md` § "No repo, no
diamond" branches on git-repo status, so a stale `false` there produces a
diamond with no isolation and no rollback. That is worse than re-deriving.

These facts are also cheap: one `git rev-parse`, one read of `registry.json`.
Caching a one-command answer to save a one-command call is the expensive path.

So: compute them fresh, every time, deterministically. This script is
structurally incapable of going stale, because it stores nothing.

WHAT THIS DOES NOT DO
---------------------
It does not read source, form judgments, or find the thing that will break the
plan. That is the scout's actual job and the part worth spending a model on.
This only clears the mechanical questions off its desk first — the ones with one
correct answer that a `git` call or a registry lookup already knows.

It reports what IS. Every "missing"/"absent" line is a fact, not a complaint;
the scout decides whether any of them matter to the task at hand.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REGISTRY = Path("graph_agents/portfolio/registry.json")

# Files that answer "how is this app built and tested" without opening any of
# them. Presence is the fact; the scout reads the ones the task touches.
STACK_MARKERS = [
    ("package.json", "node"),
    ("pnpm-workspace.yaml", "pnpm workspace"),
    ("requirements.txt", "python"),
    ("pyproject.toml", "python"),
    ("pytest.ini", "pytest"),
    ("Cargo.toml", "rust"),
    ("go.mod", "go"),
    ("Makefile", "make"),
    ("Dockerfile", "docker"),
    (".github/workflows", "github actions"),
]


# Native-app detection walks the root and two levels down (huntstack keeps its
# Expo app at apps/mobile) and never enters build output or vendored trees.
NATIVE_SKIP = {"node_modules", ".git", "target", "dist", "build", ".expo", "ios", "android"}
NATIVE_MAX_DEPTH = 2


def git(args: list[str], cwd: str | Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.returncode, (proc.stdout or proc.stderr).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, f"git unavailable: {exc}"


def load_registry() -> dict:
    if not REGISTRY.exists():
        sys.exit(
            f"{REGISTRY} not found. Run this from `repos/` - every fleet path "
            "assumes that cwd (graph_agents/CLAUDE.md, Launch rule). If you are "
            "in a fresh clone, the registry is untracked by design and must be "
            "rebuilt before any run (CURRENT-STATE.md says how)."
        )
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def repo_facts(path: Path) -> dict:
    """The git questions, answered now rather than remembered.

    `is_git_repo` is the one that decides graph shape, so it is reported first
    and never inferred from anything but git itself.
    """
    if not path.exists():
        return {"exists": False, "is_git_repo": False}

    code, _ = git(["rev-parse", "--is-inside-work-tree"], path)
    if code != 0:
        return {"exists": True, "is_git_repo": False}

    _, head = git(["rev-parse", "--short", "HEAD"], path)
    _, branch = git(["rev-parse", "--abbrev-ref", "HEAD"], path)
    _, status = git(["status", "--porcelain"], path)
    _, remote = git(["remote", "get-url", "origin"], path)
    _, author = git(["config", "user.name"], path)
    _, email = git(["config", "user.email"], path)

    dirty = [ln for ln in status.splitlines() if ln.strip()]
    return {
        "exists": True,
        "is_git_repo": True,
        "head": head,
        "branch": branch,
        "dirty_files": len(dirty),
        "clean": not dirty,
        "remote": remote if remote and "fatal" not in remote.lower() else None,
        # Identity is per-repo here and has been wrong before, so it is a fact
        # worth surfacing before any node commits under it.
        "commit_identity": f"{author} <{email}>" if author else None,
    }


def _read_json(path: Path):
    """(data, ok). A file that will not parse is evidence, never a crash."""
    try:
        return json.loads(path.read_text(encoding="utf-8")), True
    except (OSError, ValueError):
        return None, False


def _dir_native(d: Path) -> dict:
    """Evidence for one directory, keyed by kind. Only what is in `d` itself."""
    found = {"expo": [], "tauri": []}

    app_json = d / "app.json"
    if app_json.is_file():
        data, ok = _read_json(app_json)
        if not ok:
            found["expo"].append("app.json unparseable")
        elif isinstance(data, dict) and "expo" in data:
            found["expo"].append("app.json has expo key")
        # a bare React Native app.json has no 'expo' key and is not evidence
    for name in ("app.config.js", "app.config.ts", "app.config.json", "eas.json"):
        if (d / name).is_file():
            found["expo"].append(name)

    pkg = d / "package.json"
    if pkg.is_file():
        data, ok = _read_json(pkg)
        if not ok:
            found["expo"].append("package.json unparseable")
            found["tauri"].append("package.json unparseable")
        elif isinstance(data, dict):
            deps = {}
            for key in ("dependencies", "devDependencies"):
                if isinstance(data.get(key), dict):
                    deps.update(data[key])
            if "expo" in deps:
                found["expo"].append(f"package.json dep expo {deps['expo']}")
            for name in sorted(deps):
                if name.startswith("@tauri-apps/"):
                    found["tauri"].append(f"package.json dep {name} {deps[name]}")

    if (d / "src-tauri").is_dir():
        found["tauri"].append("src-tauri/ dir")
    for name in ("tauri.conf.json", "tauri.conf.json5", "Tauri.toml"):
        if (d / name).is_file():
            found["tauri"].append(name)
    return found


def native_facts(path: Path) -> list[dict]:
    """Expo / Tauri evidence under an app: root, then depth <= 2.

    Each hit is {kind, dir, evidence[]}; `dir` is the app path joined with the
    sub-path, so relative to repos/. Read-only: it only lists and reads files.
    """
    path = Path(path)
    hits: list[dict] = []
    if not path.is_dir():
        return hits

    def visit(d: Path, depth: int) -> None:
        found = _dir_native(d)
        for kind in ("expo", "tauri"):
            if found[kind]:
                hits.append({"kind": kind, "dir": d.as_posix(), "evidence": found[kind]})
        if depth >= NATIVE_MAX_DEPTH:
            return
        try:
            children = sorted(c for c in d.iterdir() if c.is_dir())
        except OSError:
            return
        for c in children:
            # src-tauri is already evidence on its parent; its config is not a second app
            if c.name not in NATIVE_SKIP and c.name != "src-tauri":
                visit(c, depth + 1)

    visit(path, 0)
    return hits


def ui_list(ui) -> list[str]:
    """Registry `ui` is a string in older entries and a list in newer ones."""
    if ui is None:
        return []
    if isinstance(ui, str):
        return [ui]
    return [str(u) for u in ui]


def contradictions_for(app_path: str, ui: list[str], native: list[dict]) -> list[str]:
    kinds = {h["kind"] for h in native}
    out = []
    if "expo" in kinds and "native-mobile" not in ui:
        out.append(f"expo detected in {app_path} but registry ui {ui} lacks native-mobile")
    if "tauri" in kinds and "native-desktop" not in ui:
        out.append(f"tauri detected in {app_path} but registry ui {ui} lacks native-desktop")
    return out


def app_facts(app: dict) -> dict:
    path = Path(app["path"])
    facts = {
        "id": app["id"],
        "path": app["path"],
        "kind": app.get("kind"),
        "status": app.get("status"),
        "one_liner": app.get("one_liner"),
        "registry_stack": app.get("stack", []),
        "owns": app.get("owns", []),
        "rules": app.get("rules", []),
        "ui": ui_list(app.get("ui")),
        "git": repo_facts(path),
    }
    facts["native"] = native_facts(path)

    facts["entry_docs"] = [
        {"path": d, "exists": Path(d).exists()} for d in app.get("entry_docs", [])
    ]
    facts["observed_stack"] = [
        label for marker, label in STACK_MARKERS if (path / marker).exists()
    ]

    # A registry that disagrees with the disk is exactly the contradiction
    # scout.md § Rules says to report rather than silently resolve.
    contradictions = []
    if not path.exists():
        contradictions.append(f"registry lists {app['path']}, but that path does not exist")
    for doc in facts["entry_docs"]:
        if not doc["exists"]:
            contradictions.append(f"entry_doc {doc['path']} is listed but missing")
    if path.exists() and not facts["git"]["is_git_repo"]:
        # Output stays ASCII on purpose. This is read off a Windows console by a
        # cheap model; an em-dash arriving as mojibake is noise in the one node
        # whose context budget is tightest.
        contradictions.append(
            f"{app['path']} is NOT a git repo - worktree isolation is unexecutable, "
            "so a diamond here is forced to single-loop (GRAPH.md: No repo, no diamond)"
        )
    contradictions.extend(contradictions_for(app["path"], facts["ui"], facts["native"]))
    facts["contradictions"] = contradictions
    return facts


def render(facts: dict) -> str:
    g = facts["git"]
    lines = [
        f"APP: {facts['id']}  ({facts['kind']}, {facts['status']})",
        f"  path:        {facts['path']}",
        f"  one_liner:   {facts['one_liner']}",
    ]
    if not g["exists"]:
        lines.append("  git:         PATH DOES NOT EXIST")
    elif not g["is_git_repo"]:
        lines.append("  git:         NOT A GIT REPO -> diamond forced to single-loop")
    else:
        state = "clean" if g["clean"] else f"{g['dirty_files']} uncommitted file(s)"
        lines.append(f"  git:         {g['branch']} @ {g['head']}, {state}")
        lines.append(f"  identity:    {g['commit_identity']}")
        if g["remote"]:
            lines.append(f"  remote:      {g['remote']}")
    lines.append(f"  stack:       registry={facts['registry_stack']} observed={facts['observed_stack']}")
    lines.append(f"  ui:          {', '.join(facts['ui']) or 'NOT SET'}")
    if facts["native"]:
        native = "; ".join(
            f"{h['kind']} at {h['dir']} ({', '.join(h['evidence'])})" for h in facts["native"]
        )
    else:
        native = "none detected"
    lines.append(f"  native:      {native}")
    docs = ", ".join(
        f"{d['path']}{'' if d['exists'] else ' (MISSING)'}" for d in facts["entry_docs"]
    )
    # An app with no entry docs is a fact worth saying out loud, not a blank.
    lines.append(f"  entry_docs:  {docs or 'NONE LISTED - the app documents itself nowhere'}")
    if facts["owns"]:
        lines.append(f"  owns:        {', '.join(facts['owns'])}")
    for rule in facts["rules"]:
        lines.append(f"  RULE:        {rule}")
    for c in facts["contradictions"]:
        lines.append(f"  ! {c}")
    return "\n".join(lines)


def main(argv: list[str]) -> None:
    args = [a for a in argv if not a.startswith("--")]
    as_json = "--json" in argv
    do_all = "--all" in argv

    registry = load_registry()
    apps = registry["apps"]

    if do_all:
        selected = apps
    elif args:
        wanted = args[0]
        selected = [a for a in apps if a["id"] == wanted]
        if not selected:
            ids = ", ".join(a["id"] for a in apps)
            sys.exit(f"no app with id {wanted!r}. Registered: {ids}")
    else:
        sys.exit(__doc__.strip().split("\n\n")[1])

    facts = [app_facts(a) for a in selected]

    umbrella = repo_facts(Path("."))
    if as_json:
        print(json.dumps(
            {
                "umbrella": {
                    "path": "repos/",
                    "is_git_repo": umbrella["is_git_repo"],
                    "app_count": len(apps),
                    "app_ids": [a["id"] for a in apps],
                    "registry_updated": registry.get("updated"),
                },
                "apps": facts,
            },
            indent=2,
        ))
        return

    print(
        f"UMBRELLA: repos/ is {'a git repo (UNEXPECTED)' if umbrella['is_git_repo'] else 'NOT a git repo, as designed'}"
        f" | {len(apps)} apps registered | registry updated {registry.get('updated')}"
    )
    print()
    for f in facts:
        print(render(f))
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
