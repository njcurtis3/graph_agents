#!/usr/bin/env python
"""Self-test for scout-facts.py native detection. Stdlib only, no pytest.

    python graph_agents/.graph/test_scout_facts.py

Fixtures are built in a tempdir; the module under test is read-only, and this test
asserts nothing is written into the fixture tree.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.realpath(__file__))
FAILURES = []

spec = importlib.util.spec_from_file_location("scout_facts", os.path.join(HERE, "scout-facts.py"))
sf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sf)


def check(label, got, want):
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %r, got %r" % (label, want, got))
        FAILURES.append(label)


def snapshot(root):
    return sorted(str(p) for p in Path(root).rglob("*"))


def fixture(files):
    root = Path(tempfile.mkdtemp(prefix="scoutfacts_"))
    for rel, content in files.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
    return root


def kinds(root):
    return sorted((h["kind"], Path(h["dir"]).relative_to(root).as_posix()) for h in sf.native_facts(root))


def run(label, files, want):
    root = fixture(files)
    try:
        before = snapshot(root)
        check(label, kinds(root), want)
        check(label + " (read-only)", snapshot(root), before)
    finally:
        shutil.rmtree(root, ignore_errors=True)


print("native_facts")
d = Path(tempfile.mkdtemp(prefix="scoutfacts_"))
try:
    check("empty dir", sf.native_facts(d), [])
finally:
    shutil.rmtree(d, ignore_errors=True)
check("missing dir", sf.native_facts(Path("no-such-dir-xyz")), [])

run("expo via app.json", {"app.json": {"expo": {"name": "x"}}}, [("expo", ".")])
run("bare RN app.json is not expo", {"app.json": {"name": "x", "displayName": "x"}}, [])
run("eas.json only", {"eas.json": {"build": {}}}, [("expo", ".")])
run("expo nested at apps/mobile", {"apps/mobile/app.json": {"expo": {}}}, [("expo", "apps/mobile")])
run("node_modules ignored", {"node_modules/expo/app.json": {"expo": {}},
                             "node_modules/expo/eas.json": {}}, [])
run("too deep is ignored", {"a/b/c/eas.json": {}}, [])
run("tauri via src-tauri/tauri.conf.json", {"src-tauri/tauri.conf.json": {}}, [("tauri", ".")])
run("tauri via @tauri-apps/api dep",
    {"package.json": {"dependencies": {"@tauri-apps/api": "^2.0.0"}}}, [("tauri", ".")])
run("both in one repo",
    {"apps/mobile/app.json": {"expo": {}}, "apps/desktop/src-tauri/tauri.conf.json": {}},
    [("expo", "apps/mobile"), ("tauri", "apps/desktop")])
run("expo via package.json dep", {"package.json": {"dependencies": {"expo": "~52.0.0"}}},
    [("expo", ".")])

root = fixture({"package.json": "{ not json"})
try:
    hits = sf.native_facts(root)
    check("malformed package.json does not crash", len(hits) > 0, True)
    check("malformed package.json reported unparseable",
          all("package.json unparseable" in h["evidence"] for h in hits), True)
finally:
    shutil.rmtree(root, ignore_errors=True)

root = fixture({"package.json": {"dependencies": {"expo": "~52.0.0"}}})
try:
    ev = sf.native_facts(root)[0]["evidence"]
    check("expo version captured", ev, ["package.json dep expo ~52.0.0"])
finally:
    shutil.rmtree(root, ignore_errors=True)

print("ui and contradictions")
expo = [{"kind": "expo", "dir": "x", "evidence": ["eas.json"]}]
tauri = [{"kind": "tauri", "dir": "x", "evidence": ["src-tauri/ dir"]}]
check("ui string", sf.ui_list("responsive-web"), ["responsive-web"])
check("ui list", sf.ui_list(["a", "b"]), ["a", "b"])
check("ui missing", sf.ui_list(None), [])
check("expo, ui string lacking native-mobile",
      len(sf.contradictions_for("x", sf.ui_list("responsive-web"), expo)), 1)
check("expo, ui list lacking native-mobile",
      len(sf.contradictions_for("x", sf.ui_list(["responsive-web"]), expo)), 1)
check("expo, ui list with native-mobile",
      sf.contradictions_for("x", sf.ui_list(["responsive-web", "native-mobile"]), expo), [])
check("expo, ui string native-mobile",
      sf.contradictions_for("x", sf.ui_list("native-mobile"), expo), [])
check("tauri, ui lacking native-desktop",
      len(sf.contradictions_for("x", ["native-mobile"], tauri)), 1)
check("tauri, ui with native-desktop",
      sf.contradictions_for("x", ["native-desktop"], tauri), [])
check("nothing detected, no contradiction", sf.contradictions_for("x", [], []), [])

print("render")
facts = {"id": "a", "kind": "app", "status": "active", "path": "a", "one_liner": "o",
         "ui": [], "native": [], "git": {"exists": False, "is_git_repo": False},
         "registry_stack": [], "observed_stack": [], "entry_docs": [], "owns": [],
         "rules": [], "contradictions": []}
out = sf.render(facts)
check("render: none detected", "native:      none detected" in out, True)
facts["native"] = [{"kind": "expo", "dir": "a/apps/mobile", "evidence": ["eas.json"]}]
facts["ui"] = ["native-mobile"]
out = sf.render(facts)
check("render: names expo and dir", "expo at a/apps/mobile" in out, True)
check("render: ui line", "ui:          native-mobile" in out, True)
check("render: ASCII", out.isascii(), True)

if FAILURES:
    print("\n%d FAIL" % len(FAILURES))
    sys.exit(1)
print("\nall ok")
