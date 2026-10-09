#!/usr/bin/env python
"""Carry graph_agents' fleet payload into Orchestra's vendored fleet/ directory.

    python graph_agents/.graph/orchestra-sync/sync.py                 write the target
    python graph_agents/.graph/orchestra-sync/sync.py --dry-run       print the plan, write nothing
    python graph_agents/.graph/orchestra-sync/sync.py --check [--scope md|all]
    python graph_agents/.graph/orchestra-sync/sync.py --verify-upstream <commit>
    python graph_agents/.graph/orchestra-sync/sync.py --verify-source <target>
    python graph_agents/.graph/orchestra-sync/sync.py --target <dir>  default orchestra/fleet beside graph_agents

Run from `repos/`. Stdlib only. README.md in this directory carries the marker grammar and
the workflow; this docstring is only the shape of the thing.

THE RULE EVERYTHING HERE SERVES: graph_agents is tuned in place and the umbrella keeps
running on exactly the bytes it always did. Orchestra gets a render of those same files with
(1) the fleet path replaced by one token, (2) marked umbrella-only spans swapped for pinned
alternates or dropped, (3) a fail-closed leak gate, and (4) self-consistency checks so a
payload that would crash on install is refused here, not there.

Every refusal exits 1 with `REFUSED: ...`. There is no force flag.
"""
import ast
import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TOOL_VERSION = "1"
HERE = os.path.dirname(os.path.realpath(__file__))
DEFAULT_UPSTREAM = os.path.normpath(os.path.join(HERE, "..", ".."))
DEFAULT_TARGET_REL = os.path.join("orchestra", "fleet")  # beside the upstream, not under the cwd
SYNC_DIR_REL = ".graph/orchestra-sync"
UNMANAGED = ["README.md"]

ID = r"[A-Za-z0-9][A-Za-z0-9._-]*"
BEGIN_RE = re.compile(r"^\s*(?:<!--\s*umbrella:begin\s+(%s)\s*-->|#\s*umbrella:begin\s+(%s))\s*$" % (ID, ID))
END_RE = re.compile(r"^\s*(?:<!--\s*umbrella:end\s+(%s)\s*-->|#\s*umbrella:end\s+(%s))\s*$" % (ID, ID))
ALT_HEAD_RE = re.compile(r"^@@@ alt (%s) pin=([0-9a-f]{12})$" % ID)
ALT_END = "@@@ end"


class Refusal(Exception):
    def __init__(self, problems):
        if isinstance(problems, str):
            problems = [problems]
        self.problems = problems
        Exception.__init__(self, "; ".join(problems))


def refuse_if(problems):
    if problems:
        raise Refusal(problems)


# ---------------------------------------------------------------- primitives

def norm(text):
    return text.replace("\r\n", "\n").replace("\r", "\n")


def sha(text):
    return hashlib.sha256(norm(text).encode("utf-8")).hexdigest()


def pin_of(span_lines):
    return hashlib.sha256(("\n".join(span_lines) + "\n").encode("utf-8")).hexdigest()[:12]


def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    try:
        return norm(raw.decode("utf-8"))
    except UnicodeDecodeError:
        raise Refusal("%s is not valid utf-8" % path)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(text.encode("utf-8"))


def git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise Refusal("git %s failed in %s: %s" % (" ".join(args), repo, r.stderr.strip()))
    return r


def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Refusal("%s is missing: %s" % (what, path))
    except ValueError as e:
        raise Refusal("%s is not valid JSON: %s (%s)" % (what, path, e))


# ---------------------------------------------------------------- payload

def load_payload(up):
    p = load_json(os.path.join(up, SYNC_DIR_REL, "payload.json"), "payload.json")
    problems = []
    for key in ("include", "token", "denylist", "leak_allow"):
        if key not in p:
            problems.append("payload.json lacks %r" % key)
    refuse_if(problems)
    if len(p["token"]) != 1:
        raise Refusal("payload.json token map must hold exactly one entry")
    p.setdefault("prose_ok_prefixes", [])
    p.setdefault("dropped_hooks", [])
    p.setdefault("stem_stoplist", [])
    for rel in p["include"]:
        if (not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel or re.match(r"^[A-Za-z]:", rel)
                or ".." in rel.split("/") or "" in rel.split("/") or os.path.isabs(rel)):
            raise Refusal("payload include entry %r must be a relative forward-slash path with no '..', "
                          "backslash or drive letter" % (rel,))
    if len(set(p["include"])) != len(p["include"]):
        raise Refusal("payload.json include has duplicates")
    for a in p["leak_allow"]:
        if not (a.get("file") and a.get("pattern") and str(a.get("reason", "")).strip()):
            raise Refusal("leak_allow entries need file, pattern and a non-empty reason: %r" % (a,))
    return p


def fleet_token(payload):
    return list(payload["token"].values())[0]


def select_files(payload, scope):
    inc = list(payload["include"])
    if scope == "md":
        inc = [f for f in inc if f.endswith(".md")]
    return inc


# ---------------------------------------------------------------- markers

def parse_spans(rel, text):
    """Return a list of ('t', line) and ('s', id, [lines]). Whole-line markers, no nesting."""
    if rel.endswith(".json"):
        return [("t", ln) for ln in text.split("\n")]
    items, open_id, open_lines, open_at = [], None, [], 0
    problems = []
    for n, ln in enumerate(text.split("\n"), 1):
        b, e = BEGIN_RE.match(ln), END_RE.match(ln)
        if b:
            mid = b.group(1) or b.group(2)
            if open_id is not None:
                problems.append("%s:%d marker %r begins inside open span %r (no nesting)" % (rel, n, mid, open_id))
            else:
                open_id, open_lines, open_at = mid, [], n
        elif e:
            mid = e.group(1) or e.group(2)
            if open_id is None:
                problems.append("%s:%d end marker %r with no begin" % (rel, n, mid))
            elif mid != open_id:
                problems.append("%s:%d end marker %r closes span %r" % (rel, n, mid, open_id))
                open_id = None
            else:
                items.append(("s", open_id, open_lines))
                open_id = None
        elif "umbrella:begin" in ln or "umbrella:end" in ln:
            problems.append("%s:%d marker text is not a whole-line marker" % (rel, n))
        elif open_id is not None:
            open_lines.append(ln)
        else:
            items.append(("t", ln))
    if open_id is not None:
        problems.append("%s:%d span %r is never closed" % (rel, open_at, open_id))
    refuse_if(problems)
    return items


def umbrella_render(items):
    out = []
    for it in items:
        out.extend([it[1]] if it[0] == "t" else it[2])
    return "\n".join(out)


def kind_of(rel):
    if rel.endswith(".py"):
        return "code"
    return "prose"


# ---------------------------------------------------------------- alternates

def parse_alternates(path):
    """alternates/*.md -> {id: (pin, [body lines])}. A missing or empty file is valid and empty."""
    if not os.path.exists(path):
        raise Refusal("alternates file is missing: %s" % path)
    out, cur, problems = {}, None, []
    text = read_text(path)
    lines = text.split("\n")
    for n, ln in enumerate(lines, 1):
        if cur is None:
            m = ALT_HEAD_RE.match(ln)
            if m:
                if m.group(1) in out:
                    problems.append("%s:%d duplicate alternate %r" % (os.path.basename(path), n, m.group(1)))
                cur = (m.group(1), m.group(2), [])
            elif ln.startswith("@@@"):
                problems.append("%s:%d malformed alternate header" % (os.path.basename(path), n))
        elif ln == ALT_END:
            out[cur[0]] = (cur[1], cur[2])
            cur = None
        elif ln.startswith("@@@"):
            problems.append("%s:%d %r inside alternate %r" % (os.path.basename(path), n, ln, cur[0]))
        else:
            cur[2].append(ln)
    if cur is not None:
        problems.append("%s: alternate %r is never closed" % (os.path.basename(path), cur[0]))
    refuse_if(problems)
    return out


def load_alternates(up):
    d = os.path.join(up, SYNC_DIR_REL, "alternates")
    return {
        "prose": parse_alternates(os.path.join(d, "prose.md")),
        "code": parse_alternates(os.path.join(d, "code.md")),
        "json": (load_json(os.path.join(d, "json.json"), "alternates/json.json")),
    }


# ---------------------------------------------------------------- json patches

def _ptr_parts(ptr):
    if ptr == "":
        return []
    if not ptr.startswith("/"):
        raise Refusal("bad JSON pointer %r" % ptr)
    return [p.replace("~1", "/").replace("~0", "~") for p in ptr[1:].split("/")]


def _canon(v):
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def json_pin(v):
    return hashlib.sha256(_canon(v).encode("utf-8")).hexdigest()[:12]


def _walk(doc, parts, ptr):
    cur = doc
    for p in parts:
        try:
            cur = cur[int(p)] if isinstance(cur, list) else cur[p]
        except (KeyError, IndexError, ValueError, TypeError):
            raise Refusal("json patch target not found: %s" % ptr)
    return cur


def apply_patches(rel, text, patches, used):
    doc = json.loads(text)
    for i, pa in enumerate(patches):
        ptr, op = pa.get("path"), pa.get("op")
        if op not in ("remove", "replace") or ptr is None or not pa.get("pin"):
            raise Refusal("json patch %d for %s needs op remove|replace, path and pin" % (i, rel))
        parts = _ptr_parts(ptr)
        if not parts:
            raise Refusal("json patch %d for %s may not target the document root" % (i, rel))
        old = _walk(doc, parts, ptr)
        got = json_pin(old)
        if got != pa["pin"]:
            raise Refusal("json patch pin mismatch: %s %s pinned %s but the value now hashes %s; "
                          "re-read the patch and re-pin" % (rel, ptr, pa["pin"], got))
        parent = _walk(doc, parts[:-1], ptr)
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        if op == "remove":
            del parent[key]
        else:
            if "value" not in pa:
                raise Refusal("json replace patch %d for %s has no value" % (i, rel))
            parent[key] = pa["value"]
        used.add(i)
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------- render

def render_all(up, payload, alts, files, scope_all):
    """Return ({rel: orchestra text}, {rel: umbrella text}) or raise Refusal."""
    problems, orch, umb = [], {}, {}
    used_alt = {"prose": set(), "code": set()}
    seen_ids = {"prose": {}, "code": {}}
    patches = alts["json"].get("patches", []) if isinstance(alts["json"], dict) else None
    if patches is None:
        raise Refusal("alternates/json.json must be an object with a 'patches' list")
    used_patch = set()
    for rel in files:
        path = os.path.join(up, *rel.split("/"))
        if not os.path.isfile(path):
            problems.append("payload file missing upstream: %s" % rel)
            continue
        text = read_text(path)
        try:
            items = parse_spans(rel, text)
        except Refusal as r:
            problems.extend(r.problems)
            continue
        umb[rel] = umbrella_render(items)
        kind = kind_of(rel)
        out = []
        for it in items:
            if it[0] == "t":
                out.append(it[1])
                continue
            mid, span = it[1], it[2]
            if mid in seen_ids[kind]:
                problems.append("duplicate marker id %r (%s and %s)" % (mid, seen_ids[kind][mid], rel))
                continue
            seen_ids[kind][mid] = rel
            ent = alts[kind].get(mid)
            if ent is None:
                problems.append("marker %r in %s has no alternate (an empty entry drops it)" % (mid, rel))
                continue
            used_alt[kind].add(mid)
            if ent[0] != pin_of(span):
                problems.append("pin mismatch for %r in %s: alternate pinned %s but the umbrella span now hashes %s; "
                                "re-read the alternate against the tuned span and re-pin"
                                % (mid, rel, ent[0], pin_of(span)))
                continue
            out.extend(ent[1])
        body = "\n".join(out)
        mine = [(i, p) for i, p in enumerate(patches) if p.get("file") == rel]
        if mine:
            try:
                body = apply_patches(rel, body, [p for _, p in mine], set())
                used_patch.update(i for i, _ in mine)
            except (Refusal, ValueError) as e:
                problems.append(str(e) if isinstance(e, Refusal) else "json patch target %s is not JSON" % rel)
                continue
        for src, dst in payload["token"].items():
            body = body.replace(src, dst)
        orch[rel] = body
    # orphans: only judge the kinds in play (md scope renders no code or json)
    kinds = {kind_of(r) for r in files}
    for kind in ("prose", "code"):
        if kind in kinds:
            for mid in alts[kind]:
                if mid not in used_alt[kind]:
                    problems.append("orphan alternate %r in alternates/%s.md has no marker" % (mid, kind))
    if scope_all:
        for i, p in enumerate(patches):
            if i not in used_patch:
                problems.append("orphan json patch %d (%s %s): its file is not rendered" % (i, p.get("file"), p.get("path")))
    refuse_if(problems)
    return orch, umb


# ---------------------------------------------------------------- leak gate

def registry_terms(up):
    reg_path = os.path.join(up, "portfolio", "registry.json")
    if not os.path.isfile(reg_path):
        raise Refusal("registry absent (%s): the leak denylist would be silently weaker, so nothing syncs" % reg_path)
    reg = load_json(reg_path, "registry.json")
    apps = reg.get("apps") if isinstance(reg, dict) else None
    if not isinstance(apps, list) or not apps:
        raise Refusal("registry has no apps list: refusing, the denylist would be empty")
    terms, seen = [], set()
    for a in apps:
        for key in ("id", "path"):
            v = a.get(key)
            if isinstance(v, str) and len(v) >= 2 and v.lower() not in seen:
                seen.add(v.lower())
                terms.append(("app-id:%s" % v, re.compile(
                    r"(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])" % re.escape(v), re.I)))
    for key in ("org", "org_domain", "org_github"):
        v = reg.get(key)
        if isinstance(v, str) and len(v) >= 3:
            terms.append(("registry:%s" % key, re.compile(re.escape(v), re.I)))
    return terms


def sibling_terms(up, payload, exclude):
    """Names of every sibling directory of the upstream under the umbrella root, read live.

    The registry omits repos on purpose (personal, vendor), so it cannot be the only source of
    names. Excludes the upstream itself and the sync target's own repo (`exclude`). Each whole
    name is a term, plus hyphen/dot/underscore stems of length >= 5 that are not in the
    payload's stem_stoplist (so 's1-whoop' is caught by 'whoop', 'tracker' is not a term).
    """
    root = os.path.dirname(os.path.abspath(up))
    try:
        names = sorted(os.listdir(root))
        dirs = [n for n in names if os.path.isdir(os.path.join(root, n))]
    except OSError as e:
        raise Refusal("cannot read the umbrella root %s (%s): the sibling-name denylist would be silently weaker" % (root, e))
    skip = {os.path.basename(os.path.abspath(up)).lower()} | {e.lower() for e in exclude}
    stop = {w.lower() for w in payload.get("stem_stoplist", [])}
    terms, seen = [], set()

    def add(label, word, loose):
        if word.lower() in seen:
            return
        seen.add(word.lower())
        b = r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" if loose else r"(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])"
        terms.append((label, re.compile(b % re.escape(word), re.I)))
    for n in dirs:
        if n.startswith(".") or len(n) < 3 or n.lower() in skip:
            continue
        add("sibling-repo:%s" % n, n, False)
        for stem in re.split(r"[-_.]", n):
            if len(stem) >= 5 and stem.lower() not in stop and stem.lower() not in skip:
                add("sibling-stem:%s" % stem, stem, True)
    return terms


def leak_scan(up, payload, orch, exclude=()):
    terms = []
    for d in payload["denylist"]:
        terms.append((d["name"], re.compile(d["regex"], re.I if d.get("ignore_case") else 0)))
    terms += registry_terms(up)
    terms += sibling_terms(up, payload, exclude)
    hits, allowed = [], 0
    for rel, text in orch.items():
        for n, ln in enumerate(text.split("\n"), 1):
            for name, rx in terms:
                for m in rx.finditer(ln):
                    ok = any(a["file"] == rel and a["pattern"] == name
                             and a.get("match", m.group(0)) == m.group(0)
                             for a in payload["leak_allow"])
                    if ok:
                        allowed += 1
                    else:
                        hits.append("%s:%d [%s] %r" % (rel, n, name, m.group(0)))
    return hits, allowed


# ---------------------------------------------------------------- self-consistency

def settings_commands(orch):
    rel = ".claude/settings.json"
    if rel not in orch:
        return []
    cmds = []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k == "command" and isinstance(x, str):
                    cmds.append(x)
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(json.loads(orch[rel]))
    return cmds


def strip_true(cmd):
    return re.sub(r"\s*\|\|\s*true\s*$", "", cmd)


def hook_script(cmd, token):
    m = re.search(r"\$\{CLAUDE_PROJECT_DIR:-\.\}/" + re.escape(token) + r"/([^\"\s]+\.py)", strip_true(cmd))
    return m.group(1) if m else None


def check_hooks(orch, payload):
    token, problems, n = fleet_token(payload), [], 0
    cmds = settings_commands(orch)
    for c in cmds:
        s = hook_script(c, token)
        if s is None:
            problems.append("settings hook command names no script under %s: %s" % (token, c))
        elif s not in orch:
            problems.append("settings hook points at an unshipped script: %s (command %s)" % (s, strip_true(c)))
        else:
            n += 1
    return problems, n, len(cmds)


def check_siblings(up, orch):
    problems = []
    for rel, text in orch.items():
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue  # py_compile reports it
        d, base = os.path.dirname(rel), os.path.basename(rel)
        want = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                want.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                want.add(node.module.split(".")[0])
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and re.match(r"^[\w.-]+\.py$", node.value):
                want.add(node.value[:-3])
        for name in sorted(want):
            if name + ".py" == base:
                continue
            cands = [(d + "/" if d else "") + name + ".py", ".graph/" + name + ".py",
                     ".claude/hooks/" + name + ".py"]
            exists = [c for c in cands if os.path.isfile(os.path.join(up, *c.split("/")))]
            if exists and not any(c in orch for c in exists):
                problems.append("%s loads %s.py (upstream %s) which is not in the payload" % (rel, name, exists[0]))
    return problems


def check_compile(orch):
    problems = []
    for rel, text in orch.items():
        if rel.endswith(".py"):
            try:
                compile(text, rel, "exec")
            except (SyntaxError, ValueError) as e:
                problems.append("py_compile failed: %s (%s)" % (rel, e))
    return problems


def check_prose(orch, payload):
    token = fleet_token(payload)
    files = set(payload["include"])  # resolve against the whole payload, even in md scope
    problems, n = [], 0
    for rel, text in orch.items():
        if not rel.endswith(".md"):
            continue
        for ln_no, ln in enumerate(text.split("\n"), 1):
            for span in re.findall(r"`([^`\n]+)`", ln):
                for tok in span.split():
                    tok = tok.lstrip("\"'(").rstrip("\"'),;.")
                    tok = re.sub(r":\d+(?:-\d+)?$", "", tok)
                    bare = tok.replace("${CLAUDE_PROJECT_DIR:-.}/", "")
                    if bare.startswith(token + "/"):
                        bare = bare[len(token) + 1:]
                    elif not (bare.startswith(".claude/") or bare.startswith(".graph/")):
                        continue
                    if not bare:
                        continue
                    n += 1
                    if any(bare.startswith(p) for p in payload["prose_ok_prefixes"]) or bare in files:
                        continue
                    static = re.split(r"[<*{$\[]", bare)[0]
                    stem = static if static != bare else bare.rstrip("/") + "/"
                    if any(f.startswith(stem) for f in files):
                        continue
                    problems.append("%s:%d dangling path `%s`" % (rel, ln_no, tok))
    return problems, n


def run_smoke(orch, payload, tmp):
    """Render into <tmp>/proj/fleet, run every settings hook with stdin {} and no || true."""
    token = fleet_token(payload)
    proj = os.path.join(tmp, "proj")
    fleet = os.path.join(proj, "fleet")
    for rel, text in orch.items():
        write_text(os.path.join(fleet, *rel.split("/")), text.replace(token, "fleet"))
    subprocess.run(["git", "-C", tmp, "init", "-q", "proj"], capture_output=True)
    env = dict(os.environ, CLAUDE_PROJECT_DIR=proj, PYTHONDONTWRITEBYTECODE="1")
    problems, ok, total = [], 0, 0
    for c in settings_commands(orch):
        s = hook_script(c, token)
        if s is None or s not in orch:
            continue
        total += 1
        script = os.path.join(fleet, *s.split("/"))
        try:
            r = subprocess.run([sys.executable, script], input="{}", capture_output=True, text=True,
                               cwd=proj, env=env, timeout=60)
        except subprocess.TimeoutExpired:
            problems.append("smoke: %s timed out" % s)
            continue
        if r.returncode == 0:
            ok += 1
        else:
            problems.append("smoke: %s exited %d: %s" % (s, r.returncode, (r.stderr or r.stdout).strip()[:200]))
    sf = ".graph/scout-facts.py"
    sf_ok = None
    if sf in orch:
        r = subprocess.run([sys.executable, os.path.join(fleet, *sf.split("/")), "--all"], capture_output=True,
                           text=True, cwd=proj, env=env, timeout=60)
        sf_ok = r.returncode == 0
        if not sf_ok:
            problems.append("smoke: scout-facts in a registry-less repo exited %d: %s"
                            % (r.returncode, (r.stderr or r.stdout).strip()[:200]))
    return problems, ok, total, sf_ok


def run_gates(up, payload, orch, scope, exclude=()):
    """Print one line per gate; raise Refusal listing everything that failed."""
    problems = []
    hits, allowed = leak_scan(up, payload, orch, exclude)
    print("leak hits: %d%s" % (len(hits), " (%d allowed with a reason)" % allowed if allowed else ""))
    problems += ["leak: " + h for h in hits]
    print("alternates: all pinned, 0 orphans")  # render_all already refused otherwise
    pp, n = check_prose(orch, payload)
    print("prose refs: %s" % ("all resolved" if not pp else "%d dangling" % len(pp)))
    problems += pp
    if scope == "all":
        hp, ok, total = check_hooks(orch, payload)
        print("hooks: %d of %d resolve" % (ok, total))
        problems += hp
        sp = check_siblings(up, orch)
        print("sibling imports: %s" % ("resolved" if not sp else "%d unresolved" % len(sp)))
        problems += sp
        cp = check_compile(orch)
        print("py_compile: %s" % ("ok" if not cp else "%d failed" % len(cp)))
        problems += cp
        if not (hp or sp or cp):
            tmp = tempfile.mkdtemp(prefix="orchestra-smoke-")
            try:
                smp, sok, stotal, sf_ok = run_smoke(orch, payload, tmp)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            print("smoke: %d of %d hooks exit 0" % (sok, stotal))
            if sf_ok is not None:
                print("scout-facts registry-less: %s" % ("ok" if sf_ok else "FAILED"))
            problems += smp
    refuse_if(problems)


# ---------------------------------------------------------------- upstream + target state

def upstream_head(up):
    r = git(up, "rev-parse", "HEAD")
    return r.stdout.strip()


def refuse_dirty_upstream(up, payload):
    r = git(up, "status", "--porcelain", "-uall")
    mine = set(payload["include"])
    bad = []
    for ln in r.stdout.splitlines():
        p = ln[3:].strip().strip('"')
        if " -> " in p:
            p = p.split(" -> ")[-1]
        if p in mine or p.startswith(SYNC_DIR_REL + "/"):
            bad.append(ln.strip())
    if bad:
        raise Refusal("upstream is dirty in payload paths (SOURCE names a commit, a dirty tree would make that "
                      "a lie): " + ", ".join(bad))


def target_files(target):
    out = {}
    if os.path.islink(target):
        raise Refusal("target %s is a symlink" % target)
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d != ".git"]
        links = [os.path.join(root, n) for n in dirs + files if os.path.islink(os.path.join(root, n))]
        if links:
            raise Refusal("symlink under target (never followed, never written through): " + ", ".join(links))
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, target).replace(os.sep, "/")
            out[rel] = full
    return out


def check_target(target):
    """The SOURCE-based refusal rule. Returns the parsed SOURCE (or None for a first sync)."""
    have = target_files(target) if os.path.isdir(target) else {}
    have.pop("README.md", None)
    src_path = have.pop("SOURCE", None)
    if src_path is None:
        if have:
            raise Refusal("target holds files but no SOURCE manifest (not an empty README-only target): "
                          + ", ".join(sorted(have)))
        return None
    src = load_json(src_path, "SOURCE")
    listed = src.get("files", {})
    problems = []
    for rel, full in sorted(have.items()):
        if rel not in listed:
            problems.append("extra file in target not in SOURCE: %s" % rel)
        elif sha(read_text(full)) != listed[rel]:
            problems.append("hand-edited target file (hash differs from SOURCE): %s" % rel)
    for rel in sorted(listed):
        if rel not in have:
            problems.append("target file listed in SOURCE is missing: %s" % rel)
    refuse_if(problems)
    return src


def build_source(up, payload, orch):
    head = upstream_head(up)
    date = git(up, "show", "-s", "--format=%cI", head).stdout.strip()
    src = {
        "upstream_repo": "graph_agents",
        "upstream_commit": head,
        "upstream_commit_date": date,
        "sync_tool_version": TOOL_VERSION,
        "token": {fleet_token(payload): "fleet root, render at install"},
        "files": {rel: sha(orch[rel]) for rel in sorted(orch)},
        "dropped_hooks": list(payload["dropped_hooks"]),
        "unmanaged": list(UNMANAGED),
    }
    return json.dumps(src, indent=2) + "\n"


# ---------------------------------------------------------------- modes

def target_repo_name(up, target):
    """First path component of the target below the umbrella root (e.g. 'orchestra'), else ''."""
    rel = os.path.relpath(os.path.abspath(target), os.path.dirname(os.path.abspath(up)))
    first = rel.replace(os.sep, "/").split("/")[0]
    return "" if first in ("", ".", "..") else first


def mode_check(up, scope, target):
    payload = load_payload(up)
    alts = load_alternates(up)
    files = select_files(payload, scope)
    orch, _ = render_all(up, payload, alts, files, scope == "all")
    run_gates(up, payload, orch, scope, [target_repo_name(up, target)])
    print("check ok: %d files rendered, nothing written" % len(orch))


def mode_sync(up, target, dry):
    payload = load_payload(up)
    alts = load_alternates(up)
    refuse_dirty_upstream(up, payload)
    old_src = check_target(target)
    orch, _ = render_all(up, payload, alts, select_files(payload, "all"), True)
    base = os.path.realpath(target)
    for rel in orch:
        if os.path.commonpath([base, os.path.realpath(os.path.join(target, *rel.split("/")))]) != base:
            raise Refusal("write target for %s resolves outside the target dir" % rel)
    run_gates(up, payload, orch, "all", [target_repo_name(up, target)])
    new_src = build_source(up, payload, orch)
    plan = []  # (verb, rel, text|None)
    for rel in sorted(orch):
        full = os.path.join(target, *rel.split("/"))
        if not os.path.isfile(full):
            plan.append(("add", rel, orch[rel]))
        elif read_text(full) != orch[rel]:
            plan.append(("change", rel, orch[rel]))
    for rel in sorted(old_src.get("files", {}) if old_src else []):
        if rel not in orch:
            plan.append(("delete", rel, None))
    sp = os.path.join(target, "SOURCE")
    if not os.path.isfile(sp) or read_text(sp) != new_src:
        plan.append(("change" if os.path.isfile(sp) else "add", "SOURCE", new_src))
    if not plan:
        print("no changes")
        return
    for verb, rel, _ in plan:
        print("  %-6s %s" % (verb, rel))
    if dry:
        print("dry run: %d changes planned, nothing written" % len(plan))
        return
    wrote = deleted = 0
    for verb, rel, text in plan:
        full = os.path.join(target, *rel.split("/"))
        if verb == "delete":
            os.remove(full)
            deleted += 1
            d = os.path.dirname(full)
            while os.path.abspath(d) != os.path.abspath(target) and os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
                d = os.path.dirname(d)
        else:
            write_text(full, text)
            wrote += 1
    print("wrote %d files, deleted %d" % (wrote, deleted))


def mode_verify_upstream(up, commit):
    payload = load_payload(up)
    alts = load_alternates(up)
    files = select_files(payload, "all")
    problems = []
    for rel in files:
        path = os.path.join(up, *rel.split("/"))
        if not os.path.isfile(path):
            problems.append("payload file missing upstream: %s" % rel)
            continue
        try:
            umb = umbrella_render(parse_spans(rel, read_text(path)))
        except Refusal as r:
            problems.extend(r.problems)
            continue
        old = git(up, "show", "%s:%s" % (commit, rel), check=False)
        if old.returncode != 0:
            problems.append("%s does not exist at %s" % (rel, commit))
        elif norm(old.stdout) != umb:
            problems.append("umbrella render differs from %s: %s" % (commit, rel))
        else:
            print("umbrella render identical: %s" % rel)
    refuse_if(problems)
    print("umbrella render identical for all %d payload files" % len(files))


def mode_verify_source(up, target):
    problems = []
    sp = os.path.join(target, "SOURCE")
    if not os.path.isfile(sp):
        raise Refusal("no SOURCE in %s" % target)
    src = load_json(sp, "SOURCE")
    head = upstream_head(up)
    if src.get("upstream_commit") != head:
        problems.append("SOURCE names %s but graph_agents HEAD is %s" % (src.get("upstream_commit"), head))
    try:
        check_target(target)
    except Refusal as r:
        problems.extend(r.problems)
    refuse_if(problems)
    print("SOURCE matches HEAD")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--scope", choices=("md", "all"), default="all")
    ap.add_argument("--verify-upstream", metavar="COMMIT")
    ap.add_argument("--verify-source", metavar="TARGET")
    ap.add_argument("--target", default=None, help="default: orchestra/fleet beside the upstream")
    ap.add_argument("--upstream", default=DEFAULT_UPSTREAM, help=argparse.SUPPRESS)  # fixtures only
    a = ap.parse_args(argv)
    up = os.path.abspath(a.upstream)
    if a.target is None:
        a.target = os.path.join(os.path.dirname(up), DEFAULT_TARGET_REL)
    try:
        if a.verify_upstream:
            mode_verify_upstream(up, a.verify_upstream)
        elif a.verify_source:
            mode_verify_source(up, a.verify_source)
        elif a.check:
            mode_check(up, a.scope, a.target)
        else:
            mode_sync(up, a.target, a.dry_run)
    except Refusal as r:
        for p in r.problems:
            print("REFUSED: %s" % p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
