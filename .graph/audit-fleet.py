#!/usr/bin/env python
"""Re-verify CURRENT-STATE.md against disk, and report only what drifted.

    python graph_agents/.graph/audit-fleet.py
    python graph_agents/.graph/audit-fleet.py -v      # every claim checked, not just drift

Exit 0 when every checkable claim agrees with disk. Exit 1 naming each one that does not.

**Why this exists.** On 2026-08-26 `CURRENT-STATE.md` still said "no agent in this fleet
has written a line of product code yet", eleven hours after one had. That file is what
every other doc and every fresh session trusts, and its own rule -- "stale entries here
are worse than missing ones" -- was enforced by a hook that can only *nag*: it fires on a
write, says the snapshot is stale, and has no idea whether anyone then re-checked
anything. The obligation was machinery; discharging it was the honour system.

Most of what that file claims is mechanically decidable. A line count is `wc -l`. A
registry id is a directory. A run's status is a field in its own `state.json`. Whether a
node has ever executed is a written key. This turns the honour system into a diff.

**What it deliberately cannot check.** Every narrative claim in that file -- the gap list's
reasoning, the per-run "what happened" sections, the Decisions log -- is prose about
judgment, and no script has an opinion about it. A clean run here means *the checkable
claims agree with disk*, never *this file is true*. Same honesty `verify-state.py` keeps
about its own blind spots: a green check is evidence about what was checked and nothing
else.

**It never writes**, and in particular it never stamps `Last verified:`. That is the one
decision this fleet has already made and marked do-not-revisit (Decisions log,
2026-08-25): a bot bumping the date would assert a verification that never happened, which
is the exact failure the header warns about. This tool discharges the *checking*; a human
still writes the stamp.

Read-only, pure stdlib, and it never raises on a fleet mid-edit.
"""
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FLEET = os.path.dirname(HERE)
UMBRELLA = os.path.dirname(FLEET)
DOC = os.path.join(FLEET, "CURRENT-STATE.md")
RUNS = os.path.join(HERE, "runs")
AGENTS = os.path.join(FLEET, ".claude", "agents")
SKILLS = os.path.join(FLEET, ".claude", "skills")
HOOKS = os.path.join(FLEET, ".claude", "hooks")
SETTINGS = os.path.join(FLEET, ".claude", "settings.json")
REGISTRY = os.path.join(FLEET, "portfolio", "registry.json")
VERIFY = os.path.join(HERE, "verify-state.py")

CLOSED = ("done", "parked", "blocked")
WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


class Report(object):
    """Claims checked, claims that drifted, and the evidence behind both."""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.checked = 0
        self.drift = []
        self.notes = []

    def claim(self, ok, description, detail=""):
        """One checkable claim. `description` is what the doc says; detail is disk."""
        self.checked += 1
        if not ok:
            self.drift.append("%s%s" % (description, (" -- " + detail) if detail else ""))
        elif self.verbose:
            self.notes.append("  ok   %s" % description)

    def note(self, line):
        self.notes.append("  %s" % line)


# ----------------------------------------------------------------- reading disk

def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def load_json(path):
    text = read(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def line_count(path):
    """Newlines, because that is what `wc -l` counts and what the doc's claims used."""
    try:
        with open(path, "rb") as fh:
            return fh.read().count(b"\n")
    except OSError:
        return None


def resolve_path(claimed):
    """A path as the doc writes it -> a real one, or None.

    The doc names paths in three idioms and all three are correct in context: umbrella-
    relative (`graph_agents/GRAPH.md`), fleet-relative (`.claude/hooks/...`, which is how
    `GRAPH.md` tells agents to reach the nodes through the junction), and `repos/`-
    prefixed (`repos/CLAUDE.md`). Resolving all three is not leniency -- refusing two of
    them would report the fleet's own documented spelling as a broken path.
    """
    claimed = claimed.strip().rstrip("/")
    if not claimed or claimed.startswith(("http", "$")):
        return None
    candidates = [os.path.join(UMBRELLA, claimed), os.path.join(FLEET, claimed)]
    if claimed.startswith("repos/"):
        candidates.append(os.path.join(UMBRELLA, claimed[len("repos/"):]))
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def git(repo, *args):
    """(exit code, stdout). Never raises; a missing git is a non-zero code."""
    try:
        proc = subprocess.run(["git", "-C", repo] + list(args),
                              capture_output=True, text=True)
    except OSError:
        return 1, ""
    return proc.returncode, proc.stdout.strip()


def verifier():
    """`verify-state.py` as a module, or None. Hyphenated filename, hence importlib."""
    try:
        spec = importlib.util.spec_from_file_location("verify_state", VERIFY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def run_states():
    """[(run_id, state)] for every run directory carrying a readable state.json."""
    found = []
    try:
        names = sorted(os.listdir(RUNS))
    except OSError:
        return found
    for name in names:
        state = load_json(os.path.join(RUNS, name, "state.json"))
        if isinstance(state, dict):
            found.append((name, state))
    return found


# ------------------------------------------------------------- reading the doc

def cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def table_rows(text, heading=None):
    """Markdown table rows, optionally only those under a given heading."""
    if heading is not None:
        start = text.find(heading)
        if start < 0:
            return []
        rest = text[start + len(heading):]
        end = rest.find("\n## ")
        text = rest if end < 0 else rest[:end]
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and line.endswith("|") and set(line) - set("|-: "):
            rows.append(cells(line))
    return rows


def number(word):
    """`5`, or `five`, or None."""
    word = word.strip().lower()
    if word.isdigit():
        return int(word)
    return WORDS.get(word)


# ------------------------------------------------------------------- the checks

def check_line_counts(text, report):
    """Every `<path>` (N ln) claim in the doc, against `wc -l`."""
    for match in re.finditer(r"`([^`\n]+)`\s*\((\d+)\s*ln\)", text):
        claimed_path, claimed = match.group(1), int(match.group(2))
        path = resolve_path(claimed_path)
        if path is None:
            report.claim(False, "`%s` (%d ln)" % (claimed_path, claimed),
                         "no such file on disk")
            continue
        actual = line_count(path)
        report.claim(actual == claimed, "`%s` is %d ln" % (claimed_path, claimed),
                     "disk has %s" % actual)


def check_skill_line_counts(text, report):
    """The skills row pairs a bare skill NAME with a count, not a path.

    Split on `;` and take each segment's first backticked name with its last count --
    the segments are one skill each, and only the name leads.
    """
    for row in table_rows(text):
        if not row or not re.match(r"^\d+ skills?$", row[0]):
            continue
        for segment in row[1].split(";"):
            name = re.search(r"`([a-z0-9-]+)`", segment)
            count = re.findall(r"\((\d+)\s*ln\)", segment)
            if not name or not count:
                continue
            path = os.path.join(SKILLS, name.group(1), "SKILL.md")
            claimed = int(count[-1])
            if not os.path.isfile(path):
                report.claim(False, "skill `%s` (%d ln)" % (name.group(1), claimed),
                             "no SKILL.md on disk")
                continue
            actual = line_count(path)
            report.claim(actual == claimed,
                         "skill `%s` is %d ln" % (name.group(1), claimed),
                         "disk has %s" % actual)
        return


def frontmatter(path):
    """The `---` block at the top of an agent file, as a dict. Flat keys only."""
    text = read(path) or ""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    block = text[3:end] if end > 0 else ""
    fields = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def executed_nodes():
    """{node: count} -- how much each node has actually done, read from run state.

    From `state.json`, not from `activity.jsonl`: gap #20 says 471 of 503 recorded stop
    events are phantoms, so anything counted from the heartbeat would be wrong. A written
    key is the fleet's own definition of a node having run, and `verify-state.py` owns
    what "written" means -- imported rather than restated, for the reason `brief.py`
    gives: two definitions would eventually disagree.
    """
    verify = verifier()
    if verify is None:
        return None
    template = verify.load_template()
    tally = {"scout": 0, "architect": 0, "builder": 0, "reviewer": 0,
             "integrator": 0, "ops": 0}
    for _, state in run_states():
        for node in ("scout", "architect", "integrator", "ops"):
            if not verify.unwritten(state, template, node):
                tally[node] += 1
        for sid in verify.real_slices(state, template):
            if not verify.unwritten(state, template, "builders.%s" % sid):
                tally["builder"] += 1
            if not verify.unwritten(state, template, "reviews.%s" % sid):
                tally["reviewer"] += 1
    return tally


def check_roster(text, report):
    """The node roster: line count, model, tool grant, and has-it-ever-run."""
    tally = executed_nodes()
    if tally is None:
        report.note("verify-state.py did not import -- execution claims not checked")
    for row in table_rows(text, "### Node roster"):
        name = re.match(r"^`([a-z]+)`$", row[0])
        if not name or len(row) < 5:
            continue
        node = name.group(1)
        path = os.path.join(AGENTS, node + ".md")
        if not os.path.isfile(path):
            report.claim(False, "roster lists `%s`" % node, "no such agent file")
            continue
        fields = frontmatter(path)

        claimed_lines = number(row[3])
        if claimed_lines is not None:
            report.claim(line_count(path) == claimed_lines,
                         "`%s.md` is %d ln" % (node, claimed_lines),
                         "disk has %s" % line_count(path))

        report.claim(fields.get("model", "") == row[1],
                     "`%s` runs on %s" % (node, row[1]),
                     "frontmatter says %r" % fields.get("model"))

        claimed_tools = [t.strip() for t in row[2].split(",") if t.strip()]
        actual_tools = [t.strip() for t in fields.get("tools", "").split(",") if t.strip()]
        report.claim(claimed_tools == actual_tools,
                     "`%s` is granted %s" % (node, row[2]),
                     "frontmatter grants %s" % (", ".join(actual_tools) or "nothing"))

        if tally is None:
            continue
        # The COUNT in this cell is deliberately not checked: the doc scopes it ("counts
        # run through the end of run 3"), so a fresh run legitimately outdates the number
        # without falsifying the claim. The yes/no is unscoped and load-bearing -- gap #2
        # is entirely a claim about which nodes have never run -- so that half is checked
        # and the observed number is reported as evidence instead.
        says_yes = row[4].lower().replace("*", "").strip().startswith("yes")
        report.claim(says_yes == (tally[node] > 0),
                     "`%s` %s" % (node, "has executed" if says_yes
                                  else "has never executed"),
                     "state files show %d" % tally[node])
    if tally:
        report.note("executed: " + ", ".join("%s %d" % (k, v) for k, v in tally.items()))


def check_counts(text, report):
    """The bare counts in the What-is-live table: apps, agent nodes, skills."""
    on_disk = {
        "agents": len([f for f in os.listdir(AGENTS) if f.endswith(".md")])
        if os.path.isdir(AGENTS) else 0,
        "skills": len([d for d in os.listdir(SKILLS)
                       if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))])
        if os.path.isdir(SKILLS) else 0,
    }
    registry = load_json(REGISTRY)
    apps = registry.get("apps") if isinstance(registry, dict) else None

    for row in table_rows(text):
        if not row:
            continue
        agents = re.match(r"^(\d+) agent nodes?$", row[0])
        if agents:
            report.claim(int(agents.group(1)) == on_disk["agents"],
                         "%s agent nodes" % agents.group(1),
                         "%d .md files in .claude/agents/" % on_disk["agents"])
        skills = re.match(r"^(\d+) skills?$", row[0])
        if skills:
            report.claim(int(skills.group(1)) == on_disk["skills"],
                         "%s skills" % skills.group(1),
                         "%d SKILL.md files on disk" % on_disk["skills"])
        if row[0] == "Portfolio index" and isinstance(apps, list) and len(row) > 1:
            nodes = re.search(r"\*\*(\d+) nodes\*\*", row[1])
            if nodes:
                report.claim(int(nodes.group(1)) == len(apps),
                             "portfolio is %s nodes" % nodes.group(1),
                             "registry.json has %d apps" % len(apps))


def check_registry(report):
    """Every registered app: a directory, a git repo, and its entry docs present."""
    registry = load_json(REGISTRY)
    if not isinstance(registry, dict) or not isinstance(registry.get("apps"), list):
        report.claim(False, "portfolio/registry.json is readable",
                     "missing or malformed -- routing is broken until it is rebuilt")
        return
    apps = registry["apps"]
    registered = set()
    for entry in apps:
        if not isinstance(entry, dict):
            continue
        app_id = str(entry.get("id") or "?")
        rel = str(entry.get("path") or app_id)
        registered.add(rel.strip("/"))
        path = os.path.join(UMBRELLA, rel)
        if not os.path.isdir(path):
            report.claim(False, "app `%s` is at `%s`" % (app_id, rel),
                         "no such directory")
            continue
        report.claim(True, "app `%s` is at `%s`" % (app_id, rel))
        report.claim(os.path.exists(os.path.join(path, ".git")),
                     "app `%s` has its own git repo" % app_id,
                     "no .git in %s -- the constitution says every app has one" % rel)
        for doc in entry.get("entry_docs") or []:
            report.claim(resolve_path(str(doc)) is not None,
                         "`%s` exists" % doc, "entry doc missing")

    # The registry is gitignored on purpose -- its `path` fields name real directories,
    # personal names among them. If it ever becomes tracked, that is a privacy
    # regression, not a bookkeeping one, so it is checked rather than assumed.
    code, out = git(FLEET, "ls-files", "--error-unmatch", "portfolio/registry.json")
    report.claim(code != 0, "registry.json is untracked",
                 "it is now tracked by git: %s" % (out or "staged"))

    siblings = []
    for name in sorted(os.listdir(UMBRELLA)):
        path = os.path.join(UMBRELLA, name)
        if (os.path.isdir(path) and not name.startswith(".")
                and name != "graph_agents" and name not in registered):
            siblings.append(name)
    if siblings:
        # A note, never drift: four of these were deregistered on purpose 2026-08-31.
        # An unregistered directory is only a defect if it was MEANT to be routed to,
        # and no file on disk records that intent.
        report.note("unregistered sibling dirs: %s" % ", ".join(siblings))


def check_runs(text, report):
    """The Runs table and the Status headline, against the run directories."""
    on_disk = dict(run_states())
    listed = {}
    for row in table_rows(text, "\n## Runs"):
        name = re.match(r"^`([^`]+)`$", row[0])
        if name:
            listed[name.group(1)] = row

    headline = re.search(r"^## Status: (\w+) runs?", text, re.M)
    if headline:
        claimed = number(headline.group(1))
        report.claim(claimed == len(on_disk), "status headline says %s runs"
                     % headline.group(1), "%d run directories on disk" % len(on_disk))

    for run_id, row in listed.items():
        if run_id not in on_disk:
            report.claim(False, "Runs table lists `%s`" % run_id,
                         "no such run directory")
            continue
        status = str(on_disk[run_id].get("status") or "").strip().lower()
        cell = " ".join(row).lower()
        # `done` reads as "executed" in that table's prose, and always has.
        wanted = ("executed", "done") if status == "done" else (status,)
        report.claim(any(w in cell for w in wanted),
                     "`%s` is recorded as %s" % (run_id, status or "?"),
                     "state.json says %r, the table's row does not say so" % status)

    for run_id, state in sorted(on_disk.items()):
        if run_id in listed:
            continue
        status = str(state.get("status") or "").strip().lower()
        if status in CLOSED:
            # This is the drift that actually happened: run 3 merged product code and
            # this file went on claiming zero for eleven hours. A CLOSED run absent from
            # the table is the single event that changes what the fleet has done.
            report.claim(False, "closed run `%s` is in the Runs table" % run_id,
                         "it is `%s` and the table does not list it" % status)
        else:
            report.note("`%s` is %s and not yet in the Runs table -- in flight, not drift"
                        % (run_id, status or "?"))


def check_git(text, report):
    """The fleet repo's own row: branch and remote."""
    for row in table_rows(text):
        if not row or row[0] != "Fleet git repo" or len(row) < 2:
            continue
        branch = re.search(r"branch `([^`]+)`", row[1])
        if branch:
            code, actual = git(FLEET, "rev-parse", "--abbrev-ref", "HEAD")
            report.claim(code == 0 and actual == branch.group(1),
                         "fleet is on branch `%s`" % branch.group(1),
                         "git says %r" % actual)
        remote = re.search(r"github\.com/[\w.\-]+/[\w.\-]+", row[1])
        if remote:
            code, actual = git(FLEET, "remote", "get-url", "origin")
            report.claim(code == 0 and remote.group(0) in actual,
                         "fleet remote is %s" % remote.group(0),
                         "origin is %r" % (actual or "unset"))
        return


def hook_commands():
    """[(event, script path as written)] for every command in settings.json."""
    settings = load_json(SETTINGS)
    found = []
    if not isinstance(settings, dict):
        return found
    for event, groups in (settings.get("hooks") or {}).items():
        for group in groups if isinstance(groups, list) else []:
            for hook in (group or {}).get("hooks") or []:
                command = str((hook or {}).get("command") or "")
                script = re.search(r"[\w./\-${}:]*\.py", command)
                if script:
                    found.append((event, script.group(0)))
    return found


def check_hooks(report):
    """Every registered hook resolves to a file, and every hook file is registered."""
    referenced = set()
    for event, script in hook_commands():
        clean = script.replace("${CLAUDE_PROJECT_DIR:-.}/", "").strip('"')
        path = resolve_path(clean)
        report.claim(path is not None, "%s hook `%s`" % (event, clean),
                     "command names a script that is not on disk")
        if path:
            referenced.add(os.path.realpath(path))

    if not os.path.isdir(HOOKS):
        return
    for name in sorted(os.listdir(HOOKS)):
        if not name.endswith(".py") or name.startswith("test_"):
            continue
        path = os.path.realpath(os.path.join(HOOKS, name))
        # An unregistered hook is a script that looks live and runs never. Same class of
        # silence as gap #18, where six hooks could have been dead indefinitely with
        # nothing to show for it.
        report.claim(path in referenced, "`.claude/hooks/%s` is registered" % name,
                     "no settings.json entry runs it")


def check_freshness(text, report):
    """`Last verified:` against the fleet definition files committed since.

    Commit dates rather than mtimes: a checkout rewrites every mtime on disk, so mtime
    answers "when did this arrive here", which is not the question.
    """
    stamp = re.search(r"Last verified: (\d{4}-\d{2}-\d{2})", text)
    if not stamp:
        report.claim(False, "the doc carries a `Last verified:` stamp", "none found")
        return
    verified = stamp.group(1)
    report.note("last verified %s" % verified)

    code, out = git(FLEET, "log", "--format=@%cs", "--name-only", "-n", "80")
    if code != 0:
        return
    newest = {}
    date = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("@"):
            date = line[1:]
        elif line and date and line not in newest:
            newest[line] = date

    stale = []
    for rel, date in sorted(newest.items()):
        if date <= verified or not rel.endswith((".md", ".json", ".py")):
            continue
        if rel.endswith("CURRENT-STATE.md") or rel.startswith(".graph/runs/"):
            continue
        stale.append("%s (%s)" % (rel, date))
    report.claim(not stale, "the stamp covers every fleet definition file",
                 "changed after %s: %s" % (verified, ", ".join(stale)))


# ------------------------------------------------------------------------ main

def main(argv):
    verbose = "-v" in argv or "--verbose" in argv
    text = read(DOC)
    if text is None:
        sys.stderr.write("audit-fleet: cannot read %s\n" % DOC)
        return 1

    report = Report(verbose)
    for check in (check_line_counts, check_skill_line_counts, check_roster,
                  check_counts, check_runs, check_git, check_freshness):
        try:
            check(text, report)
        except Exception as exc:
            report.claim(False, "%s ran" % check.__name__, "raised %r" % exc)
    for check in (check_registry, check_hooks):
        try:
            check(report)
        except Exception as exc:
            report.claim(False, "%s ran" % check.__name__, "raised %r" % exc)

    print("audit-fleet: CURRENT-STATE.md vs disk")
    for line in report.notes:
        print(line)
    sys.stdout.flush()      # or the evidence lands after the drift that cites it

    for line in report.drift:
        sys.stderr.write("audit-fleet: DRIFT: %s\n" % line)
    if report.drift:
        sys.stderr.write("audit-fleet: %d claims checked, %d drifted -- "
                         "re-verify and update CURRENT-STATE.md\n"
                         % (report.checked, len(report.drift)))
        return 1
    print("audit-fleet: %d claims checked, none drifted. Prose claims are NOT checked -- "
          "see the module docstring." % report.checked)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
