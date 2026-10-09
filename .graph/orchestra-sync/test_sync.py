#!/usr/bin/env python
"""Self-test for sync.py. Stdlib only, no pytest.

    python graph_agents/.graph/orchestra-sync/test_sync.py

Every case builds a THROWAWAY upstream repo and a throwaway target in a temp dir and runs
sync.py against them with --upstream/--target. Nothing here reads or writes the real
orchestra/ or mutates graph_agents' working tree; the done_when ends with
`git -C orchestra status --porcelain` to prove it.

The property under test is the barrier, not the copy: the sync must REFUSE, loudly and
for the stated reason, in each way a tuned payload could leak or break Orchestra. So each
refusal case asserts the exit code AND the reason text, and a refusal case that exits 1
for the wrong reason fails. The cases that must succeed are asserted to leave bytes
exactly as claimed (README untouched, re-run identical).
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
SYNC = os.path.join(HERE, "sync.py")
spec = importlib.util.spec_from_file_location("sync_under_test", SYNC)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

REAL_PAYLOAD = json.load(open(os.path.join(HERE, "payload.json"), encoding="utf-8"))
FAILURES = []


def check(label, cond, detail=""):
    if cond:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s %s" % (label, detail))
        FAILURES.append(label)


def put(root, rel, text):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(text.encode("utf-8"))


def snapshot(root):
    snap = {}
    for r, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            with open(p, "rb") as fh:
                snap[os.path.relpath(p, root)] = fh.read()
    return snap


SCOUT = """# scout
Step one.
<!-- umbrella:begin reg -->
Read the portfolio registry first.
<!-- umbrella:end reg -->
Run `graph_agents/.graph/brief.py` for facts, see `.claude/agents/scout.md`.
"""
SCOUT_SPAN = ["Read the portfolio registry first."]
GUARD = """import os
import sys
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
import bash_write_targets
sys.exit(0)
"""
SETTINGS = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{
    "type": "command",
    "command": 'python "${CLAUDE_PROJECT_DIR:-.}/graph_agents/.claude/hooks/guard.py" || true'}]}]}}
BASE = {
    ".claude/agents/scout.md": SCOUT,
    ".claude/hooks/guard.py": GUARD,
    ".claude/hooks/bash_write_targets.py": "def classify(c):\n    return c\n",
    ".claude/settings.json": json.dumps(SETTINGS, indent=2) + "\n",
    ".graph/brief.py": "print('brief')\n",
    "GRAPH.md": "# graph\nSee `graph_agents/.claude/agents/scout.md`.\n",
}
README = "# fleet\nOrchestra-owned — stays empty until the first sync.\n"


def alt(mid, span, body):
    return "@@@ alt %s pin=%s\n%s@@@ end\n" % (mid, S.pin_of(span), "".join(b + "\n" for b in body))


class Fx:
    """A throwaway upstream repo + target dir."""

    def __init__(self, files=None, include=None, prose="", code="", patches=None,
                 registry=True, leak_allow=None, readme=True):
        self.tmp = tempfile.mkdtemp(prefix="sync-test-")
        self.up = os.path.join(self.tmp, "up")
        self.tgt = os.path.join(self.tmp, "orch", "fleet")
        files = dict(BASE if files is None else files)
        for rel, text in files.items():
            put(self.up, rel, text)
        pl = {"include": include if include is not None else sorted(files),
              "token": {"graph_agents": "@FLEET@"}, "denylist": REAL_PAYLOAD["denylist"],
              "leak_allow": leak_allow or [], "prose_ok_prefixes": [".graph/CURRENT", ".graph/runs/"],
              "dropped_hooks": [], "stem_stoplist": REAL_PAYLOAD["stem_stoplist"]}
        put(self.up, ".graph/orchestra-sync/payload.json", json.dumps(pl, indent=2))
        put(self.up, ".graph/orchestra-sync/alternates/prose.md", prose)
        put(self.up, ".graph/orchestra-sync/alternates/code.md", code)
        put(self.up, ".graph/orchestra-sync/alternates/json.json", json.dumps({"patches": patches or []}))
        if registry:
            put(self.up, "portfolio/registry.json", json.dumps(
                {"org": "Acme Holdings", "apps": [{"id": "huntstack", "path": "huntstack"},
                                                   {"id": "zebra-app", "path": "zebra-app"}]}))
        self.g("init", "-q")
        self.g("config", "user.name", "t")
        self.g("config", "user.email", "t@example.invalid")
        self.g("config", "core.autocrlf", "false")
        self.commit("base")
        os.makedirs(self.tgt)
        if readme:
            put(self.tgt, "README.md", README)

    def g(self, *a):
        r = subprocess.run(["git", "-C", self.up] + list(a), capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    def commit(self, msg):
        self.g("add", "-A")
        self.g("commit", "-q", "-m", msg)
        return self.g("rev-parse", "HEAD")

    def edit(self, rel, text, commit=True):
        put(self.up, rel, text)
        return self.commit("edit " + rel) if commit else None

    def run(self, *args):
        r = subprocess.run([sys.executable, SYNC, "--upstream", self.up, "--target", self.tgt] + list(args),
                           capture_output=True, text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr

    def good(self, **kw):
        """Same fixture, but with the alternate that makes it valid."""
        return self

    def done(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


GOOD_PROSE = alt("reg", SCOUT_SPAN, [])


def refuses(label, fx, args, needle):
    rc, out = fx.run(*args)
    check(label, rc == 1 and "REFUSED" in out and needle in out, "rc=%s out=%r" % (rc, out[-400:]))
    return out


def main():
    # ---- the refusals that guard marking and pinning
    fx = Fx()
    refuses("marker without alternate refuses", fx, [], "has no alternate")
    fx.done()

    fx = Fx(prose=GOOD_PROSE + alt("ghost", ["x"], []))
    refuses("orphan alternate refuses", fx, [], "orphan alternate 'ghost'")
    fx.done()

    fx = Fx(prose=alt("reg", ["Read the registry (stale pin)."], []))
    out = refuses("pin mismatch refuses", fx, [], "pin mismatch")
    check("pin mismatch prints the new hash to re-pin", S.pin_of(SCOUT_SPAN) in out)
    fx.done()

    nested = SCOUT.replace("Step one.\n", "Step one.\n<!-- umbrella:begin outer -->\n")
    fx = Fx(files=dict(BASE, **{".claude/agents/scout.md": nested}), prose=GOOD_PROSE)
    refuses("nested marker refuses", fx, [], "no nesting")
    fx.done()

    midline = SCOUT.replace("Step one.", "Step one. <!-- umbrella:begin zz -->")
    fx = Fx(files=dict(BASE, **{".claude/agents/scout.md": midline}), prose=GOOD_PROSE)
    refuses("mid-line marker refuses", fx, [], "not a whole-line marker")
    fx.done()

    # ---- the leak gate
    leaky = SCOUT.replace("Step one.", "Step one. The umbrella decides.")
    fx = Fx(files=dict(BASE, **{".claude/agents/scout.md": leaky}), prose=GOOD_PROSE)
    refuses("leak hit refuses", fx, [], "[umbrella]")
    fx.done()

    appy = SCOUT.replace("Step one.", "Step one for huntstack.")
    fx = Fx(files=dict(BASE, **{".claude/agents/scout.md": appy}), prose=GOOD_PROSE)
    refuses("registry-app-id leak refuses", fx, [], "app-id:huntstack")
    fx.done()

    fx = Fx(prose=GOOD_PROSE, registry=False)
    refuses("registry absent refuses", fx, [], "registry absent")
    fx.done()

    fx = Fx(files=dict(BASE, **{".claude/agents/scout.md": leaky}), prose=GOOD_PROSE,
            leak_allow=[{"file": ".claude/agents/scout.md", "pattern": "umbrella", "reason": "test"}])
    rc, out = fx.run("--check")
    check("leak_allow with a reason lets a hit through", rc == 0 and "(1 allowed" in out, out)
    fx.done()

    fx = Fx(prose=GOOD_PROSE, leak_allow=[{"file": "x", "pattern": "umbrella", "reason": " "}])
    refuses("leak_allow without a reason refuses", fx, [], "non-empty reason")
    fx.done()

    # ---- path-shaped leaks (the owner's own home path, in every spelling it takes)
    BS = chr(92)
    for label, text in (
            ("single-backslash Windows path", "C:" + BS + "Users" + BS + "someone" + BS + "Desktop"),
            ("doubled-backslash Windows path (as inside a Python string or JSON)",
             "C:" + BS * 2 + "Users" + BS * 2 + "someone" + BS * 2 + "Desktop"),
            ("forward-slash Windows path", "C:/Users/someone/Desktop"),
            ("Git Bash /<drive>/Users path", "/c/Users/someone/Desktop"),
            ("unix home path", "/home/someone/code"),
            ("Claude project-slug path", "C--Users-someone-Desktop-repos"),
            ("owner username", "natha")):
        fx = Fx(files=dict(BASE, **{".graph/brief.py": "# " + text + "\nprint('brief')\n"}), prose=GOOD_PROSE)
        refuses("leak: %s refuses" % label, fx, [], "REFUSED: leak: .graph/brief.py:1")
        fx.done()

    # ---- sibling repos under the umbrella root (unregistered ones included)
    for label, text, needle in (
            ("unregistered sibling repo name", "see whoop-med-tracker", "sibling-repo:whoop-med-tracker"),
            ("distinctive stem of a sibling name (s1-whoop)", "the s1-whoop slice", "sibling-stem:whoop"),
            ("dotted sibling name", "koenrane.xyz", "sibling-repo:koenrane.xyz")):
        fx = Fx(files=dict(BASE, **{".graph/brief.py": "# " + text + "\nprint('brief')\n"}), prose=GOOD_PROSE)
        os.makedirs(os.path.join(fx.tmp, "whoop-med-tracker"))
        os.makedirs(os.path.join(fx.tmp, "koenrane.xyz"))
        refuses("leak: %s refuses" % label, fx, [], needle)
        fx.done()

    fx = Fx(files=dict(BASE, **{".graph/brief.py": "# a tracker and an archive; orch is the target\nprint('brief')\n"}),
            prose=GOOD_PROSE)
    os.makedirs(os.path.join(fx.tmp, "whoop-med-tracker"))
    os.makedirs(os.path.join(fx.tmp, "personal-archive"))
    rc, out = fx.run("--check")
    check("common-word stems and the target's own repo name are not leaks", rc == 0, out)
    fx.done()

    # ---- paths in the payload and under the target
    for bad in ("../escape.md", "/abs.md", "a" + BS + "b.md", "C:/x.md", "a/../b.md"):
        fx = Fx(prose=GOOD_PROSE)
        pl = json.load(open(os.path.join(fx.up, ".graph/orchestra-sync/payload.json")))
        pl["include"].append(bad)
        fx.edit(".graph/orchestra-sync/payload.json", json.dumps(pl))
        put(fx.tmp, "escape.md", "outside\n")
        refuses("include %r refuses" % bad, fx, [], "payload include entry")
        check("include %r wrote nothing outside fleet/" % bad, not os.path.exists(os.path.join(fx.tgt, "..", "escape.md")))
        fx.done()

    fx = Fx(prose=GOOD_PROSE)
    link = os.path.join(fx.tgt, "link")
    try:
        os.symlink(fx.up, link, target_is_directory=True)
        made = True
    except (OSError, NotImplementedError):
        made = False
    if made:
        refuses("symlink under the target refuses", fx, [], "symlink under target")
    else:
        print("  skip symlink under the target refuses (cannot create symlinks here)")
    fx.done()

    # ---- self-consistency
    bad = json.loads(BASE[".claude/settings.json"])
    bad["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = \
        'python "${CLAUDE_PROJECT_DIR:-.}/graph_agents/.claude/hooks/ghost.py" || true'
    fx = Fx(files=dict(BASE, **{".claude/settings.json": json.dumps(bad)}), prose=GOOD_PROSE)
    refuses("settings hook pointing at an unshipped script refuses (|| true present)", fx, [],
            "unshipped script: .claude/hooks/ghost.py")
    fx.done()

    inc = [k for k in BASE if k != ".claude/hooks/bash_write_targets.py"]
    fx = Fx(include=inc, prose=GOOD_PROSE)
    refuses("missing sibling import refuses (bash_write_targets-shaped fixture)", fx, [],
            "bash_write_targets.py")
    fx.done()

    fx = Fx(files=dict(BASE, **{"GRAPH.md": "# graph\nSee `.graph/missing.py`.\n"}), prose=GOOD_PROSE)
    refuses("dangling prose path refuses", fx, [], "dangling path `.graph/missing.py`")
    fx.done()

    fx = Fx(files=dict(BASE, **{".graph/brief.py": "def f(:\n"}), prose=GOOD_PROSE)
    refuses("py_compile failure refuses", fx, [], "py_compile failed")
    fx.done()

    fx = Fx(files=dict(BASE, **{".claude/hooks/guard.py": "import sys\nsys.exit(3)\n"}), prose=GOOD_PROSE)
    refuses("smoke: a hook that exits non-zero refuses", fx, [], "smoke: .claude/hooks/guard.py exited 3")
    fx.done()

    # ---- upstream cleanliness
    fx = Fx(prose=GOOD_PROSE)
    put(fx.up, "GRAPH.md", "# graph\nUncommitted.\n")
    refuses("dirty upstream refuses", fx, [], "upstream is dirty")
    rc, out = fx.run("--check")
    check("--check does not require a clean upstream", rc == 0, out)
    fx.done()

    # ---- the sync itself
    fx = Fx(prose=GOOD_PROSE)
    readme_before = open(os.path.join(fx.tgt, "README.md"), "rb").read()
    rc, out = fx.run()
    check("first sync into README-only target succeeds", rc == 0 and "wrote" in out, out)
    check("README byte-identical after sync", open(os.path.join(fx.tgt, "README.md"), "rb").read() == readme_before)
    scout = open(os.path.join(fx.tgt, ".claude/agents/scout.md"), encoding="utf-8").read()
    check("span dropped by its empty alternate", "registry first" not in scout and "Step one.\nRun" in scout, scout)
    check("path token rendered", "`@FLEET@/.graph/brief.py`" in scout and "graph_agents" not in scout, scout)
    src = json.load(open(os.path.join(fx.tgt, "SOURCE")))
    check("SOURCE names HEAD and every file", src["upstream_commit"] == fx.g("rev-parse", "HEAD")
          and set(src["files"]) == set(BASE) and src["unmanaged"] == ["README.md"])

    before = snapshot(fx.tgt)
    rc, out = fx.run()
    check("second run reports no changes", rc == 0 and "no changes" in out, out)
    check("second run leaves target bytes identical", snapshot(fx.tgt) == before)

    rc, out = fx.run("--verify-source", fx.tgt)
    check("--verify-source passes after a sync", rc == 0 and "SOURCE matches HEAD" in out, out)

    # CRLF from another machine's autocrlf is not a hand-edit
    p = os.path.join(fx.tgt, "GRAPH.md")
    raw = open(p, "rb").read()
    open(p, "wb").write(raw.replace(b"\n", b"\r\n"))
    rc, out = fx.run("--verify-source", fx.tgt)
    check("CRLF-only change is not a hand-edit (LF-normalized hashing)", rc == 0, out)
    open(p, "wb").write(raw)

    # the plan modes write nothing
    fx.edit("GRAPH.md", "# graph\nTuned.\nSee `graph_agents/.claude/agents/scout.md`.\n")
    before = snapshot(fx.tgt)
    rc, out = fx.run("--dry-run")
    check("--dry-run prints a plan and writes nothing", rc == 0 and "change" in out and "GRAPH.md" in out
          and "nothing written" in out and snapshot(fx.tgt) == before, out)
    rc, out = fx.run("--check")
    check("--check writes nothing", rc == 0 and "leak hits: 0" in out and "alternates: all pinned, 0 orphans" in out
          and "prose refs: all resolved" in out and "hooks: 1 of 1 resolve" in out
          and "sibling imports: resolved" in out and "py_compile: ok" in out
          and "smoke: 1 of 1 hooks exit 0" in out and snapshot(fx.tgt) == before, out)
    rc, out = fx.run("--check", "--scope", "md")
    check("--check --scope md checks only the md payload", rc == 0 and "hooks:" not in out
          and snapshot(fx.tgt) == before, out)
    rc, out = fx.run("--verify-source", fx.tgt)
    check("--verify-source fails when SOURCE is behind HEAD", rc == 1 and "HEAD is" in out, out)

    rc, out = fx.run()
    check("a tuned upstream file syncs through", rc == 0 and "change " in out and "Tuned." in
          open(os.path.join(fx.tgt, "GRAPH.md"), encoding="utf-8").read(), out)

    # hand-edits
    gp = os.path.join(fx.tgt, "GRAPH.md")
    orig = open(gp, "rb").read()
    open(gp, "ab").write(b"hand edit\n")
    refuses("hand-edited target file refuses", fx, [], "hand-edited target file")
    rc, out = fx.run("--verify-source", fx.tgt)
    check("--verify-source fails after a hand-edit", rc == 1 and "hand-edited" in out, out)
    open(gp, "wb").write(orig)

    put(fx.tgt, "stray.md", "mine\n")
    refuses("extra file in target refuses", fx, [], "extra file in target")
    os.remove(os.path.join(fx.tgt, "stray.md"))

    # a file dropped from the allowlist is deleted from the target
    pl = json.load(open(os.path.join(fx.up, ".graph/orchestra-sync/payload.json")))
    pl["include"].remove("GRAPH.md")
    fx.edit(".graph/orchestra-sync/payload.json", json.dumps(pl, indent=2))
    rc, out = fx.run()
    check("file dropped from the allowlist is deleted", rc == 0 and "delete " in out
          and not os.path.exists(gp), out)
    fx.done()

    fx = Fx(prose=GOOD_PROSE)
    put(fx.tgt, "stray.md", "mine\n")
    refuses("first sync refuses a target holding more than README", fx, [], "no SOURCE manifest")
    fx.done()

    # ---- json patches
    old = SETTINGS["hooks"]["PreToolUse"]
    patch = {"file": ".claude/settings.json", "op": "remove", "path": "/hooks/PreToolUse/0", "pin": S.json_pin(old[0])}
    inc = [k for k in BASE if k not in (".claude/hooks/guard.py", ".claude/hooks/bash_write_targets.py")]
    fx = Fx(include=inc, prose=GOOD_PROSE, patches=[patch])
    rc, out = fx.run()
    got = json.load(open(os.path.join(fx.tgt, ".claude/settings.json"), encoding="utf-8"))
    check("pinned json patch removes the hook entry", rc == 0 and got["hooks"]["PreToolUse"] == [], out)
    fx.done()

    fx = Fx(include=inc, prose=GOOD_PROSE, patches=[dict(patch, pin="000000000000")])
    refuses("json patch pin mismatch refuses", fx, [], "json patch pin mismatch")
    fx.done()

    fx = Fx(include=inc, prose=GOOD_PROSE, patches=[dict(patch, file="GRAPH.md")])
    refuses("json patch on a non-JSON file refuses", fx, [], "not JSON")
    fx.done()

    # ---- umbrella render identity
    fx = Fx(files=dict(BASE, **{".claude/agents/scout.md": SCOUT.replace(
        "<!-- umbrella:begin reg -->\n", "").replace("<!-- umbrella:end reg -->\n", "")}),
        prose="")
    unmarked = fx.g("rev-parse", "HEAD")
    fx.edit(".claude/agents/scout.md", SCOUT)
    fx.edit(".graph/orchestra-sync/alternates/prose.md", GOOD_PROSE)
    rc, out = fx.run("--verify-upstream", unmarked)
    check("umbrella render identity holds for a marked fixture",
          rc == 0 and "umbrella render identical: .claude/agents/scout.md" in out, out)
    fx.edit(".claude/agents/scout.md", SCOUT.replace("Step one.", "Step 1."))
    rc, out = fx.run("--verify-upstream", unmarked)
    check("umbrella render identity fails when marking changed real text", rc == 1 and "differs" in out, out)
    fx.done()

    if FAILURES:
        print("\n%d FAILED: %s" % (len(FAILURES), ", ".join(FAILURES)))
        sys.exit(1)
    print("\nall checks passed")


if __name__ == "__main__":
    main()
