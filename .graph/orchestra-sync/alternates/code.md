@@@ alt gbs-msys-comment pin=dd980592852d
        # Translate before `isabs`: on Python 3.13+ Windows `/c/dir/x` is not absolute,
@@@ end
@@@ alt gbs-base-comment pin=fb02066a289d
    # carries; the project root is the fallback, and it is what the Bash tool
    # actually uses in every run this fleet has executed. Only the MSYS spelling of the
    # base is translated before the join (Git Bash sends `/c/dir/...`, which `realpath`
    # would map to `C:/c/dir/...`); the base is NEVER passed through `norm`, because
@@@ end
@@@ alt gbs-diamond-path pin=0af57281305f
    # somewhere else entirely and can never equal the plan's project-relative path. Match
@@@ end
@@@ alt gbs-glob-incident pin=6fe91b80a6fa
        # EVERY write under an approved directory. That happened once: three
        # slices of one run had `myapp/apps/mobile/**` as their
@@@ end
@@@ alt gbs-glob-example pin=713a8076de86
        # `myapp/apps/mobile/**` to mean "everything under apps/mobile". Reduce a
@@@ end
@@@ alt gbs-msys-doc pin=4bf70f555c37
    """`/c/dir/x` or `/cygdrive/c/dir/x` -> `c:/dir/x`, on Windows only.
@@@ end
@@@ alt gbs-umbrella-comment pin=d57c92809fe9
UMBRELLA = os.path.dirname(FLEET)                             # the project root
@@@ end
@@@ alt gbs-doc-worktree pin=3afc9e9d2775
  worktree's absolute paths are rooted outside the project and can never equal the
  plan's. The repo is the project root (UMBRELLA = dirname(FLEET) assumes the fleet
  directory sits directly under the project root) and a plan entry is a path inside it.
  If that ever stops being true the
@@@ end
@@@ alt bwt-root-example pin=a5e01c7ef3bf
  path that resolves against the session root, so the caller would judge `<root>/GRAPH.md`
@@@ end
@@@ alt ra-readers-2 pin=87f6fa4c8a2c
    locking the log would make `brief.py` and other readers fail to READ it mid-run,
@@@ end
@@@ alt ra-readers-1 pin=5484c1d86c50
    and others) skip unparseable lines, so it cost no crash and left no report; it
    silently subtracted one event from the evidence base they are built on.
@@@ end
@@@ alt ra-encode-cwd pin=b691dbc1ea5b
    Observed, not documented: Claude Code names a project's directory after its launch
    cwd -- every `\\`, `/` and `:` becomes `-`,
@@@ end
@@@ alt ra-board-ref pin=1e3227362028
than to any documented hook field -- accepted deliberately (see the board's token-counter
@@@ end
@@@ alt fsg-junction pin=9e3ea18fd564
The `.claude` directory may be a junction or symlink, so resolve the path before
@@@ end
@@@ alt fsg-reuse pin=957c7bf6de43
The rule lives in `verify-state.py`, not here.
`importlib` rather than `import` because the filename is
@@@ end
@@@ alt fsg-gap7 pin=fae383bf5547
What that turns from convention into machinery:
@@@ end
@@@ alt vs-cap-audit pin=ebb4df26a4e0
                "reviews.%s.%s is past the attempt_%d cap that this audit and the board "
@@@ end
@@@ alt vs-cap-warning pin=09bca9cf3c36
                   "the board both stop at -- it is NOT resolved, and the two readers now "
@@@ end
@@@ alt vs-divergence pin=73e7e4686951
    One documented divergence from the board, which breaks on `!a`: an EMPTY attempt dict
@@@ end
@@@ alt vs-mirrors pin=0373b69c43d4
    """One attempt, flattened to the fields every reader needs. Mirrors the board's."""
@@@ end
@@@ alt vs-walk pin=a67d40d0dd3b
# The board's walk is `for (var i = 2; i < 10; i++)`, so it stops after attempt_9. This
@@@ end
@@@ alt vs-board-ref pin=ca5e42cba3f0
# The fleet board's `reviewAttempts`/`finalVerdict`/`everRejected` is the reference this
# mirrors, read and copied, never imported.
@@@ end
@@@ alt brief-old-reviews pin=4acb07853b84
    (a couple of early runs are such cases). Taking the larger keeps those loops visible
    instead of demoting
@@@ end
@@@ alt brief-relative-doc pin=8ef6a1dfd7c9
    """Project-relative where possible.

    Against the project root, never against cwd. Every path this fleet writes is relative to
    the project root, and cwd is not reliably that: a hook
    inherits whatever directory the session happens to sit in, so a cwd-relative line
    renders differently depending on who is printing it and pastes back into nothing.
    An absolute line is the fallback, for a run that genuinely lives
    outside the project.
@@@ end
@@@ alt brief-example-app pin=b4699ce6fc17
    <run-id> | myapp | building | gate ok
@@@ end
@@@ alt cr-target-repo pin=59642a012fa8
def target_repo(app):
    """The directory this run's work landed in: the project root, or None if no app is named."""
    if not app:
        return None
    return UMBRELLA
@@@ end
@@@ alt cr-registry-const pin=623c93490863
@@@ end
@@@ alt crc-lane-origin pin=6dd6a8165bb7
# (a lone `stop` event with
@@@ end
@@@ alt crc-encode-cwd pin=b691dbc1ea5b
    Observed, not documented: Claude Code names a project's directory after its launch
    cwd -- every `\\`, `/` and `:` becomes `-`,
@@@ end
@@@ alt rlm-state-root pin=19fee99d05ba
disposable -- nothing under the project root is written, so there is nothing to gitignore.
@@@ end
@@@ alt rlm-must-not pin=2aaec1e484a9
  - In `.claude/hooks/**`. A sub-call is a network call, and no hook may depend on one.
  - By `reviewer`, `architect` or `integrator`. An RLM hands the reading to haiku, and
    those are the nodes GRAPH.md § Model tiering says are never downgraded. A reviewer
    reading a diff through haiku summaries is a laundered review.
@@@ end
@@@ alt rlm-cwd-outside pin=b886758efd57
--no-session-persistence`, a minimal `--system-prompt`, and a cwd OUTSIDE the project (the
@@@ end
@@@ alt rlm-launched-from pin=065d0046de6b
`claude -p` launched from the project root would load the fleet's hooks and CLAUDE.md: every
@@@ end
@@@ alt rlm-measured-on pin=29bfb2eec88d
THINKING AND CACHING, measured 2026-10-06 on one 30KB chunk of a long state document
@@@ end
@@@ alt rlm-root-model pin=8e391f5355b4
    root model      the node already running (scout, an orchestrator)
@@@ end
@@@ alt rlm-run-from pin=5fc1f220cd02
Run from the project root, like everything else in the fleet.
@@@ end
@@@ alt sf-report pin=a26e03632e32
NATIVE_LABEL = {"expo": "native-mobile", "tauri": "native-desktop"}


def project_root() -> tuple[Path, bool]:
    """(root, is_git_repo): the repo containing the cwd, else the cwd itself."""
    cwd = Path.cwd()
    code, top = git(["rev-parse", "--show-toplevel"], cwd)
    if code == 0 and top:
        return Path(top), True
    return cwd, False


def observed_stack(root: Path) -> list[str]:
    return [label for marker, label in STACK_MARKERS if (root / marker).exists()]


def render(root: Path, is_repo: bool) -> str:
    # Output stays ASCII on purpose: it is read off a console by a cheap model.
    lines = [f"PROJECT: {root.as_posix()}"]
    if not is_repo:
        # Quoted verbatim by the feature-graph skill; keep the text exact.
        lines.append("NOT A GIT REPO -> diamond forced to single-loop")
    else:
        g = repo_facts(root)
        head, branch = g["head"], g["branch"]
        if not head or head.lower().startswith("fatal"):
            head = "no commits yet"
            code, name = git(["symbolic-ref", "--short", "HEAD"], root)
            if code == 0 and name:
                branch = name
        state = "clean" if g["clean"] else f"{g['dirty_files']} uncommitted file(s)"
        lines.append(f"  git:         {branch} @ {head}, {state}")
        lines.append(f"  identity:    {g['commit_identity']}")
        if g["remote"] and not g["remote"].lower().startswith(("error", "fatal")):
            lines.append(f"  remote:      {g['remote']}")
    lines.append(f"  stack:       observed={observed_stack(root)}")
    hits = native_facts(root)
    native = [
        f"{NATIVE_LABEL[h['kind']]} at {Path(h['dir']).relative_to(root).as_posix()} "
        f"({', '.join(h['evidence'])})"
        for h in hits
        if h["kind"] in NATIVE_LABEL
    ]
    if native:
        lines.append(f"  native:      {'; '.join(native)}")
    for h in hits:
        if h["kind"] == "unparseable":
            lines.append(f"  ! {', '.join(h['evidence'])} at {Path(h['dir']).relative_to(root).as_posix()}")
    return "\n".join(lines)


def main(argv: list[str]) -> None:
    """The arguments are accepted and ignored: the target is always the project root."""
    root, is_repo = project_root()
    print(render(root, is_repo))
@@@ end
@@@ alt sf-native-doc pin=37ad4536b9ba
    Each hit is {kind, dir, evidence[]}; `dir` is the project root joined with the
    sub-path. Read-only: it only lists and reads files.
@@@ end
@@@ alt sf-load-registry pin=55d4c12d4040
@@@ end
@@@ alt sf-native-comment pin=02fe556e3b56
# Native-app detection walks the root and two levels down (a monorepo may keep its
@@@ end
@@@ alt sf-registry-const pin=3e3cd0575753
@@@ end
@@@ alt sf-doc pin=9079f4b11ccf
"""Compute the facts a scout would otherwise re-derive by hand, every run.

    python @FLEET@/.graph/scout-facts.py

Reports on the project root: the git repository that contains the current directory, or
the current directory itself when it is not inside one. An optional positional argument is
accepted and ignored. It reads nothing but the project itself.

What it prints: whether the target is a git repository (the fact that decides the graph's
shape), the branch, HEAD, how many files are uncommitted, the commit identity, the stack
observed on disk, and a `native:` line only when native-app evidence is found on disk
(Expo -> native-mobile, Tauri -> native-desktop). When the target is not a git repository
it prints exactly `NOT A GIT REPO -> diamond forced to single-loop`.

WHY THIS EXISTS, and why it is a script rather than a cache
-----------------------------------------------------------
A per-project fact *store* was designed first and rejected on evidence. Scout facts rot:
two that a scout had recorded were checked against reality after the run and had become
false.

  "this directory is NOT a git repository"   - someone ran `git init` afterwards
  "the project has N top-level directories"  - N changed

So scouts do repeat work, but the facts they repeat most are the ones that rot fastest. A
cache would have handed a later run a confident, wrong answer to exactly the question that
decides the graph's SHAPE: git-repo status picks single-loop or diamond, so a stale
`false` there produces a diamond with no isolation and no rollback. That is worse than
re-deriving.

These facts are also cheap: one `git rev-parse` and a handful of file-existence checks.
Caching a one-command answer to save a one-command call is the expensive path.

So: compute them fresh, every time, deterministically. This script is structurally
incapable of going stale, because it stores nothing.

WHAT THIS DOES NOT DO
---------------------
It does not read source, form judgments, or find the thing that will break the plan. That
is the scout's actual job and the part worth spending a model on. This only clears the
mechanical questions off its desk first - the ones with one correct answer that a `git`
call or a file-existence check already knows.

It reports what IS. Every "missing"/"absent" line is a fact, not a complaint; the scout
decides whether any of them matter to the task at hand.
"""
@@@ end
@@@ alt gbs-fix-hook-msg pin=e7ce1a49edff
            "Orchestrator: fix the hook before resuming the run." % traceback.format_exc(limit=4).strip()
@@@ end
@@@ alt bwt-measure-tool pin=40d7879e3d9b
  * A write flag the parser reads but a MEASUREMENT could not have shown: this list is
    kept honest by the spelling sweep in the suite, which asks the parser about every
    command it has in five spellings each rather than in the one it was written in.
@@@ end
@@@ alt rlm-test-ref pin=2b44fddeb7b6
$0.001 a call. The test suite runs entirely under it.
@@@ end
@@@ alt crc-copy-comment pin=016189e296db
# .claude/hooks/record-activity.py -- copied, not imported)
@@@ end
@@@ alt crc-copy-rule pin=f577c3c34bf9
The path derivation below is COPIED
@@@ end
@@@ alt gbs-rel-map pin=d3c745e48f33
        # Same entry, expressed as (repo root, path within that repo). In a project the
        # repo is the project root, so the whole entry is the path within it. This is what
        # lets a builder in a linked worktree be matched: same repo-relative path, different
        # root. A write that matches no entry here is still judged by the absolute rule above.
        if not os.path.isabs(entry_path):
            root = norm(UMBRELLA)
            rel = entry_path.strip("/")
            rel_map.setdefault(root, {})[rel.lower() if os.name == "nt" else rel] = entry
@@@ end
@@@ alt gbs-gap14-origin pin=fafee5d37a54
    #14, worked around once by setting that run's `scope_exceptions` to `[]`).
@@@ end
@@@ alt gbs-closed-note pin=813d006a0953
# `parked` added to match `show-board.py`. A pointer left on a parked run must no more
# constrain a later builder than a pointer left on a closed one.
@@@ end
@@@ alt ra-parked-example pin=b3a685fa6dda
# run -- one run has sat parked since the day it opened -- kept
@@@ end
@@@ alt ra-torn-example pin=6242e93b46bf
    That is not hypothetical here. one run's log line 1225 reads
@@@ end
@@@ alt vs-closing-fix pin=9479d4efc201
        unaudited. That is exactly `builders.closing_fix` in an early run,
@@@ end
@@@ alt vs-payload-split pin=e6e1545963df
# why `close-run.py` could not close such a run and why the audit had been
# misreporting it since the day it closed.
@@@ end
@@@ alt brief-off-plan pin=170cda3bd57c
        # A slice no approved plan contains. `builders.closing_fix` in an early run
        # is the case: real work, off the gate.
@@@ end
@@@ alt brief-detail-example pin=cf40bc0a814f
      detail  graph_agents/.graph/runs/<run-id>/state.json
@@@ end
@@@ alt cr-payload-split pin=eb2857490ad6
    #    an early run could not close. The rule is imported from
@@@ end
@@@ alt cr-fleet-hardening pin=9956d0fd1474
    #    point: `builders.closing_fix` in an early run was real work with no reviewer.
@@@ end
@@@ alt cr-prose-branch pin=82b10585b155
        # written prose into this field -- one run's s1 records
@@@ end
@@@ alt cr-commit-field pin=812924bb9f87
    fall back to the commit the builder recorded; a past run wrote that field as
@@@ end
@@@ alt cr-why-exists pin=00adb20cca1d
**Why this exists.** An early run closed with its `log` reading
@@@ end
@@@ alt vs-fanin-origin pin=89e3f23984f1
    Found by an early run, the first to reach fan-in.
@@@ end
@@@ alt brief-example-goal pin=73c66d2c8e7a
      goal   Fix the date shown on the settings page
@@@ end
