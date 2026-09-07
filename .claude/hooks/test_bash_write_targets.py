#!/usr/bin/env python
"""Self-test for bash_write_targets.py. Stdlib only, no pytest.

    python graph_agents/.claude/hooks/test_bash_write_targets.py

WHAT A TEST LIKE THIS CANNOT DO, SAID FIRST

A suite of hand-written cases proves the classifier catches the mechanisms someone
thought of. It cannot prove the list is complete, and that is precisely the failure
`guard-commit-trailers.py` had twice -- a matcher that passed its own examples and then
met a real one. So this file has three halves and they do different jobs:

  * The MECHANISM cases are written here, because a mechanism has to be exercised with a
    target that can be asserted exactly, and the corpus does not oblige by containing a
    clean example of each. They prove detection.

  * The READ-ONLY fixture is LIFTED FROM THE CORPUS -- real commands this fleet actually
    ran, chosen for being ordinary rather than for being easy. They prove the absence of
    false positives, which is the half imagination is worst at. `git status`, `git add`,
    `python -m pytest`, `node test.js`, `awk 'NR>=322 ...'` with a `>` inside quotes, and
    a `grep` whose pattern literally contains the words `copy` and `shutil`. Every one of
    them must classify as not-a-write. Any command carrying an absolute owner path was
    excluded when they were selected; the transcripts stay in the transcripts.

  * The PRE-FILTER SUPERSET SWEEP at the end asks one question of every command in this
    file, and of a matrix of spellings besides: if `has_write_signature` says no, does
    the parser AGREE that there is nothing here? It is the only check in the file that
    is about a property rather than a case, and it exists because the first version of
    this classifier failed exactly there. `sed --in-place` and `node --eval` resolved
    their targets exactly and the pre-filter could not see either one, so `classify`
    short-circuited to clean and the guard was blind to them -- while `-i` and `-e` were
    denied. The corpus tool's soundness counter printed 0 the whole time, because a
    corpus can only say the blind spot is empty today. This sweep says it is not there.

The corpus half is also why `measure_bash_corpus.py` exists beside this file. This suite
says "the cases pass"; that one says what the classifier does to all 2078 of them.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from bash_write_targets import (classify, has_write_signature,      # noqa: E402
                                MAX_COMMAND, _walk)

FAILURES = []
CASES = 0
READ_ONLY_CASES = 0
CORPUS_CASES = 0

# Every command any case in this file classifies, so the pre-filter's superset property
# can be checked over all of them at the end rather than trusted one case at a time.
ALL_COMMANDS = []

# The plan's floor, asserted rather than counted by hand at review time. The second one
# counts CORPUS-DERIVED cases only, which is what `done_when` asks for -- "at least 30
# real read-only corpus commands classified as not-a-write". Counting every `clean()`
# call instead let hand-written near-misses pay for the fixture: 31 of them were added in
# one attempt, and after that `READ_ONLY_CORPUS` could be cut to five entries with the
# suite still green. A floor that a shrinking fixture cannot turn red is not enforcing
# anything, and this one is the human's approved gate rather than the file's own idea.
MINIMUM_CASES = 45
MINIMUM_READ_ONLY = 30


def check(label, got, want):
    global CASES
    CASES += 1
    if got == want:
        print("  ok   %s" % label)
    else:
        print("  FAIL %s -- expected %r, got %r" % (label, want, got))
        FAILURES.append(label)


def writes(label, command, *expected):
    """The command writes exactly these targets, and nothing was left unresolved."""
    ALL_COMMANDS.append(command)
    targets, unresolved = classify(command)
    check(label, (targets, unresolved), (list(expected), False))
    if not has_write_signature(command):
        FAILURES.append("%s -- pre-filter missed a write it can resolve" % label)
        print("  FAIL %s -- the pre-filter said no to a command that writes" % label)


def unresolved(label, command, *expected):
    """A write is present; these targets resolved and something else did not."""
    ALL_COMMANDS.append(command)
    check(label, classify(command), (list(expected), True))


def clean(label, command):
    """Not a write. Nothing to report and nothing to warn about."""
    global READ_ONLY_CASES
    READ_ONLY_CASES += 1
    ALL_COMMANDS.append(command)
    check(label, classify(command), ([], False))


def corpus_clean(label, command):
    """`clean()`, but the case came from the corpus fixture and the floor may count it."""
    global CORPUS_CASES
    CORPUS_CASES += 1
    clean(label, command)


# Words that stop being keywords the moment they are quoted, so a rewritten spelling of
# one is not a spelling of the same command. Mirrors `_COMPOUND_KEYWORDS` in the module.
KEYWORDS = frozenset(("{", "}", "!", "if", "then", "elif", "else", "while", "until", "do"))


def spellings(command):
    """The same command written the ways the shell allows its FIRST WORD to be written.

    Attempt 2's sweep asked the superset question of 178 commands, one spelling each, and
    a fresh reviewer then found 52 leaks in 713 spellings -- because the pre-filter is a
    raw-string anchor while the parser lexes, so `\\rm`, `'rm'` and `FOO="a b" rm` are one
    command word to the parser and three different strings to the anchor. A sample of
    spellings is the same kind of evidence the corpus counter is: it says the blind spot
    is empty today. Generating the families instead makes the sweep say the families are
    not there, which is the question worth asking.
    """
    first = command.split(" ", 1)[0]
    # Only a PLAIN first word gets rewritten. Quoting `FOO="a b"` or `do` produces a
    # string the shell would not run the way the parser reads it -- bash decides
    # assignment-ness and keyword-ness on the UNQUOTED word, so `\FOO=x rm y` and `'do'
    # rm y` are attempts to run a command named `FOO=x` or `do`, and the `rm` never
    # happens. Sweeping those would be asking the pre-filter to cover a write the shell
    # does not perform, which is a different complaint (the parser over-reporting) and
    # points the wrong way: over-reporting fails toward a denial, and the anchor cannot
    # fix it.
    if not re.match(r"^[A-Za-z][A-Za-z0-9_.-]*$", first) or first in KEYWORDS:
        return []
    rest = command[len(first):]
    return [
        "\\" + command,                     # escaped: `\rm -rf build`
        "'" + first + "'" + rest,           # single-quoted verb
        '"' + first + '"' + rest,           # double-quoted verb
        'FOO="a b" ' + command,             # an assignment whose value contains a space
        "{ " + command + "; }",             # a brace group, which does not scope a cd
    ]


def prefilter_is_sound(command):
    """The pre-filter may cost a wasted disk read. It may never HIDE a write.

    Asked of the parser directly, past the short-circuit `classify` does, which is the
    only way to see the disagreement: when the pre-filter says no, `classify` returns
    ([], False) whatever the parser would have said.
    """
    if has_write_signature(command):
        return True
    try:
        return _walk(command, "", {}, 0) == ([], False)
    except Exception:
        return False


# Spellings that are not otherwise a case here, swept for the superset property below.
# The first two are the pair that made the property FALSE on attempt 1: the parser
# resolved `sed --in-place` and `node --eval` exactly while the pre-filter, which needed
# a single-dash flag, said the command could not write at all. The rest are the same
# question asked of every other spelling the parser implements.
PRE_FILTER_MATRIX = (
    "sed --in-place 's/x/y/' graph_agents/CURRENT-STATE.md",
    "sed --in-place=.bak 's/x/y/' notes.md",
    "sed -ni 's/x/y/p' notes.md",
    "sed -i.bak -e 's/x/y/' notes.md",
    "node --eval \"require('fs').writeFileSync('a.js','x')\"",
    "python3 -c \"open('a.txt','w').write('x')\"",
    "py -3 -c \"open('a.txt','w').write('x')\"",
    "perl -e 'open(FH, \">o.txt\");'",
    "curl --output out.json https://example.invalid/a",
    "curl --output=out.json https://example.invalid/a",
    "curl -sSo out.json https://example.invalid/a",
    "curl -O https://example.invalid/a/z.tar",
    "curl --remote-name https://example.invalid/a/z.tar",
    "wget https://example.invalid/a/z.tar",
    "wget --output-document=out.html https://example.invalid/a",
    "sudo rm -rf build",
    "doas rm -rf build",
    "env FOO=1 rm -rf build",
    "nice -n 5 rm -rf build",
    "nohup mkdir -p out/reports",
    "timeout 30 rm -rf build",
    "/usr/bin/rm -rf build",
    "ls *.md | xargs sed -i 's/a/b/'",
    "eval \"$CMD\"",
    "echo $(rm -rf build)",
    "echo `rm -rf build`",
    "echo \"$(rm -rf build)\"",
    "python t.py >& all.log",
    "git restore --source=HEAD notes.md",
    "git apply fix.patch",
    "perl -i -pe 's/a/b/' notes.md",
    "perl -pi -e 's/a/b/' notes.md",
    "perl -i.bak -pe 's/a/b/' notes.md",
    "node --eval=\"require('fs').writeFileSync('a.js','x')\"",
    "python -c\"open('a.txt','w').write('x')\"",
    "ls | xargs -i rm {}",
    "ls | xargs -I{} rm {}",
    "{ rm -rf build; }",
    "do rm -rf build",
    "if cd graph_agents; then echo x > f.md; fi",
    "\\rm -rf build",
    "'rm' -rf build",
    "\"rm\" -rf build",
    "FOO=\"a b\" rm -rf build",
    "FOO=\"a b\" sudo rm -rf build",
    "/bin/'rm' -rf build",
)


# Real commands, lifted verbatim from this fleet's own session transcripts. None of them
# carries an absolute path or anything resembling a credential; that was the selection
# rule. Several are here for a specific trap, noted where it is not obvious.
READ_ONLY_CORPUS = (
    "git status --short",
    "git remote -v",
    "git add -A && git status --short",
    "git branch --show-current && git log --oneline -3 --all | cat",
    "git config user.name && git config user.email && git diff --stat",
    "git fetch origin master 2>&1 && git log origin/master..HEAD --oneline",
    "git log --follow --oneline -- docs/viewer.png",
    "git push origin main 2>&1",
    "git show 6c7cdc2 --stat; echo \"---\"; git status --short",
    "git status && echo --- && git diff -- web/index.html | head -200",
    "git -C fleetview diff master s2-scope-exceptions-member-guard -- index.html | head -80",
    "cat CLAUDE.md",
    "cat GRAPH.md",
    "cat -n graph_agents/.claude/settings.json",
    "cat graph_agents/.graph/runs/_schema.json",
    "cat graph_agents/portfolio/registry.json && echo \"=== SETTINGS ===\" && cat graph_agents/.claude/settings.json",
    "cat graph_agents/GRAPH.md 2>/dev/null | head -200",
    "cd graph_agents && cat GRAPH.md",
    "ls -d fleetview 2>/dev/null && ls fleetview",
    "ls -la && echo \"--- REGISTRY ---\" && cat graph_agents/portfolio/registry.json",
    "wc -l \"web/index.html\"",
    "pwd && ls .graph/runs 2>/dev/null | head -3",
    # The pattern contains the words `copy` and `shutil`; the interpreter-body inspector
    # must not see a grep argument as source it is meant to read.
    "grep -n \"CURRENT\\|tempfile\\|copy\\|shutil\" .claude/hooks/test_guard_builder_scope.py | head -30",
    "grep -rniE \"commit\" graph_agents/.claude/agents/*.md | head -60",
    "grep -rl \"improvement review\\|improvement-review\" graph_agents/ fleetview/ 2>/dev/null | head -20",
    # `>=` inside single quotes is arithmetic, not a redirect.
    "awk 'NR>=322 && NR<=625' graph_agents/CURRENT-STATE.md | grep -n \"^[0-9]\\+\\.\" | tail -6",
    "sed -n '/In Progress \\/ Next/,/^---/p' CLAUDE.md | head -60",
    "python -m pytest -q 2>&1 | tail -10",
    "python graph_agents/.claude/hooks/test_guard_builder_scope.py; echo \"EXIT=$?\"",
    "python graph_agents/.graph/audit-fleet.py; echo \"EXIT=$?\"",
    "python graph_agents/.graph/verify-state.py --audit 2026-09-01-huntstack-mobile; echo \"exit=$?\"",
    "python graph_agents/.graph/brief.py --ascii 2026-08-26-archive-adapters | grep integrator",
    "node test.js 2>&1 | tail -3",
    "npm test 2>&1 | tail -10",
    "npm run check 2>&1 | tail -20",
    # `install` is not the coreutil here, and it is not in a command position either.
    "pip3 install --quiet pymupdf 2>&1 | tail -15",
    "cd fleetview && git remote -v && echo \"--- test suite ---\" && node test.js 2>&1 | tail -5",
    # A `for` loop whose body redirects nothing; `<` is input and `ln)` is prose.
    "cd graph_agents/.claude/agents && for f in *.md; do echo \"--- $f ($(wc -l < $f) ln)\"; sed -n '1,8p' $f; done",
    "netstat -ano | grep 8790",
    "ps -ef 2>/dev/null | grep -i python | grep -v grep",
    "date",
    "pwd",
)


def main():
    print("bash_write_targets self-test\n")

    # --- The ten mechanisms this fleet has actually used, each with its target. ---
    print("the ten evidenced mechanisms:")
    writes("1. redirect writes its target",
           "echo hello > notes.txt", "notes.txt")
    writes("2. append writes its target",
           "echo hello >> notes.txt", "notes.txt")
    writes("3. heredoc to a file writes the redirect's target",
           "cat > graph_agents/GRAPH.md <<'EOF'\nnew body\nEOF", "graph_agents/GRAPH.md")
    writes("4. tee writes every file operand",
           "echo x | tee -a first.log second.log", "first.log", "second.log")
    writes("5. install writes its destination",
           "install -m 644 src.txt dist/out.txt", "dist/out.txt")
    writes("6. dd writes of=",
           "dd if=/dev/zero of=build/disk.img bs=1M count=4", "build/disk.img")
    writes("7. git checkout writes the pathspec after --",
           "git checkout HEAD -- graph_agents/GRAPH.md", "graph_agents/GRAPH.md")
    writes("8. truncate writes its file operand",
           "truncate -s 0 run.log", "run.log")
    writes("9. mv writes destination and source both",
           "mv old/name.md new/name.md", "old/name.md", "new/name.md")
    writes("10. cp writes its destination, not its source",
           "cp template.json config.json", "config.json")

    # --- The four named beside them, and the interpreter bodies. ---
    print("\nthe rest of the plan's list:")
    writes("sed -i writes its file operands",
           "sed -i 's/old/new/' graph_agents/GRAPH.md", "graph_agents/GRAPH.md")
    writes("sed -i with -e still writes its file",
           "sed -i -e 's/a/b/' notes.md", "notes.md")
    writes("rm writes (removes) its operands",
           "rm -rf build dist", "build", "dist")
    writes("touch writes its operands",
           "touch a.txt b.txt", "a.txt", "b.txt")
    writes("mkdir writes its operands",
           "mkdir -p out/reports", "out/reports")
    writes("ln writes its destination",
           "ln -s ../real.json link.json", "link.json")
    writes("python -c writing through open()",
           "python -c \"open('state.json','w').write('{}')\"", "state.json")
    writes("python -c writing through pathlib",
           "python -c \"from pathlib import Path; Path('out/report.md').write_text('x')\"",
           "out/report.md")
    writes("python -c through a variable assigned in the body",
           "python -c \"p='graph_agents/GRAPH.md'; open(p,'w').write('x')\"",
           "graph_agents/GRAPH.md")
    writes("python -c through os.path.join of literals",
           "python -c \"import os; open(os.path.join('a','b.json'),'w').write('{}')\"",
           "a/b.json")
    writes("python -c calling os.remove",
           "python -c \"import os; os.remove('stale.json')\"", "stale.json")
    writes("python -c calling shutil.copy",
           "python -c \"import shutil; shutil.copy('a.txt','b.txt')\"", "b.txt")
    writes("node -e writing through fs",
           "node -e \"require('fs').writeFileSync('dist/app.js','x')\"", "dist/app.js")
    writes("perl -e writing through a two-arg open",
           "perl -e 'open(FH, \">out.txt\"); print FH \"x\";'", "out.txt")
    writes("python - fed by a heredoc",
           "python - <<'PY'\nfrom pathlib import Path\nPath('out.md').write_text('hi')\nPY",
           "out.md")
    writes("bash -c is re-classified as shell",
           "bash -c 'echo x > inner.txt'", "inner.txt")

    # --- Interpreter bodies are INSPECTED, not flagged for being interpreter bodies. ---
    # 356 corpus commands use this shape and 57 write. Flagging the shape invents 299
    # denials, which is the single biggest false-positive risk in the design.
    print("\ninterpreter bodies are inspected, not flagged wholesale:")
    clean("python -c that only reads a file",
          "python -c \"import json; print(json.load(open('state.json')))\"")
    clean("python -c that opens for reading explicitly",
          "python -c \"print(open('a.txt','r').read())\"")
    clean("python -c that only imports and prints",
          "python -c \"import sys; print(sys.version)\"")
    clean("python -c calling .replace on a string",
          "python -c \"print('a-b'.replace('-','+'))\"")
    clean("python -c calling .remove on a list",
          "python -c \"x=[1,2]; x.remove(1); print(x)\"")
    clean("node -e that only reads",
          "node -e \"console.log(require('fs').readFileSync('a.js','utf8'))\"")
    clean("a heredoc-fed body that only reads",
          "python - <<'PY'\nimport json\nprint(json.load(open('a.json')))\nPY")
    writes("json.dump resolves through the open() that made the handle",
           "python -c \"import json; json.dump({}, open('out.json','w'))\"", "out.json")

    # --- A heredoc body is DATA. It must not be parsed as shell. ---
    print("\na heredoc body is data, not shell:")
    clean("prose in a heredoc that names rm is not a delete",
          "cat <<'EOF' | wc -l\nthe guard should not read rm -rf build as a command\nEOF")
    clean("prose in a heredoc containing a redirect is not a redirect",
          "cat <<'EOF' | wc -l\nwrite it with echo x > somewhere.txt\nEOF")
    writes("but the redirect on the heredoc's own line still counts",
           "cat >> log.md <<'EOF'\nrm -rf build\nEOF", "log.md")

    # --- Quoting, /dev/null, fd dups: the shapes that make a naive matcher wrong. ---
    print("\nredirect shapes that are not writes to a file:")
    clean("> /dev/null is not a write worth reporting",
          "curl -s http://localhost:8790/ > /dev/null")
    clean("2> /dev/null is not a write worth reporting",
          "python tool.py 2> /dev/null")
    clean("&> /dev/null is not a write worth reporting",
          "make check &> /dev/null")
    clean("2>&1 is an fd dup, not a file called 1",
          "python tool.py 2>&1 | tail -5")
    clean("a > inside single quotes is not a redirect",
          "grep -n 'a > b' notes.md")
    clean("a > inside double quotes is not a redirect",
          "echo \"a > b\"")
    writes("a numbered fd redirect still names its file",
           "python tool.py 2> errors.log", "errors.log")
    writes("stdout to a file and stderr to /dev/null reports only the file",
           "python tool.py > out.log 2>/dev/null", "out.log")

    # --- cd and variables: the two things that decide the unresolved rate. ---
    print("\ncd and variable resolution:")
    writes("a cd is applied to a later relative target",
           "cd graph_agents && echo x > GRAPH.md", "graph_agents/GRAPH.md")
    writes("a cd does not touch an absolute target",
           "cd graph_agents && echo x > /tmp/out.log", "/tmp/out.log")
    writes("a same-command assignment resolves the target",
           "SP=/tmp/scratch && echo x > \"$SP/run.log\"", "/tmp/scratch/run.log")
    writes("an assignment prefixing the command resolves too",
           "RUN=r1 python -c \"import os\" ; echo x > runs/$RUN/state.json",
           "runs/r1/state.json")
    writes("git -C is applied like a cd, for that command only",
           "git -C graph_agents checkout -- GRAPH.md", "graph_agents/GRAPH.md")
    writes("a single-quoted $ is four literal characters, not a variable",
           "echo '$HOME' > literal.txt", "literal.txt")
    unresolved("a variable never assigned here is a write shape, not a target",
               "echo x > \"$CLAUDE_JOB_DIR/tmp/out.json\"")
    unresolved("a command substitution is a write shape, not a target",
               "echo x > \"run-$(date +%s).log\"")
    unresolved("one resolved target and one unresolved shape are both reported",
               "echo a > kept.txt && echo b > \"$SOMEWHERE/lost.txt\"", "kept.txt")
    unresolved("a relative target under an unresolvable cd cannot be placed",
               "cd \"$SOMEWHERE\" && echo x > out.log")
    unresolved("git apply writes files named inside the patch, not on the line",
               "git apply fix.patch")
    # The safety net under the heredoc-interpolation narrowing, and the ONE branch in
    # `_Result.add` no other case reaches: every unresolved() case above short-circuits
    # earlier on `not resolved`. An UNQUOTED heredoc delimiter means the shell would have
    # interpolated `$SP` into the body, so the body must not be read literally -- but
    # with no assignment to interpolate there is no path either, and handing the caller
    # `$SP/o.json` would be handing it a filename no process will ever open. Inverting
    # `if "$" in target:` in bash_write_targets.py leaves the rest of this suite green.
    unresolved("an unassigned $VAR in an UNQUOTED heredoc body is a shape, not a path",
               "python - <<PY\nopen('$SP/o.json','w').write('{}')\nPY")
    writes("the same body with the variable assigned resolves through it",
           "SP=/tmp/scratch python - <<PY\nopen('$SP/o.json','w').write('{}')\nPY",
           "/tmp/scratch/o.json")
    writes("a QUOTED delimiter does not interpolate, so the $ is literal and stays",
           "python - <<'PY'\nopen('out.json','w').write('{}')\nPY", "out.json")

    # --- The LONG spellings of flags the parser acts on. Attempt 1 resolved every one
    # --- of these exactly and the pre-filter said the command could not write at all,
    # --- so `classify` short-circuited to clean and the guard never saw them. `writes()`
    # --- asserts the pre-filter agrees, which is what makes these regression cases.
    print("\nlong flag spellings, which the pre-filter must also see:")
    writes("sed --in-place writes its file operand",
           "sed --in-place 's/x/y/' graph_agents/CURRENT-STATE.md",
           "graph_agents/CURRENT-STATE.md")
    writes("sed --in-place=.bak writes its file operand",
           "sed --in-place=.bak 's/x/y/' notes.md", "notes.md")
    writes("sed -ni is the in-place flag in a cluster",
           "sed -ni 's/x/y/p' notes.md", "notes.md")
    writes("node --eval writes through fs",
           "node --eval \"require('fs').writeFileSync('dist/app.js','x')\"",
           "dist/app.js")
    # The `=`-joined and attached spellings, which the parser reads and nothing here
    # asserted. Found by MUTATION, not by reading: disabling the attached-body branch
    # outright left the suite green. The soundness sweep carries both commands, but it
    # only ever asks whether the pre-filter is NARROWER than the parser -- a parser that
    # stops resolving them satisfies it perfectly, so a sweep cannot stand in for a case.
    writes("node --eval=BODY is the same flag joined with an =",
           "node --eval=\"require('fs').writeFileSync('dist/app.js','x')\"",
           "dist/app.js")
    writes("python -c with no space before its body still has a body",
           "python -c\"open('out.txt','w').write('x')\"", "out.txt")
    check("the pre-filter says yes to sed --in-place",
          has_write_signature("sed --in-place 's/x/y/' notes.md"), True)
    check("the pre-filter says yes to node --eval",
          has_write_signature("node --eval \"require('fs').writeFileSync('a','x')\""),
          True)

    # --- A subshell's cwd dies with the subshell. Leaking it is a WRONG resolved path,
    # --- which is the direction that denies work the plan approved.
    print("\na cd inside a subshell does not escape it:")
    writes("a cd inside ( ) does not reach the command after it",
           "(cd graph_agents && echo x > a.md) ; echo y > b.md",
           "graph_agents/a.md", "b.md")
    writes("a cd inside a pipeline does not reach the command after it",
           "cd graph_agents | cat ; echo y > b.md", "b.md")
    writes("a backgrounded cd does not reach the command after it",
           "cd graph_agents & echo y > b.md", "b.md")
    writes("a cd BEFORE a subshell is still in force inside it",
           "cd graph_agents && (echo x > a.md) && echo y > b.md",
           "graph_agents/a.md", "graph_agents/b.md")
    writes("nested subshells each restore the cwd they were opened at",
           "cd a && (cd b && (cd c && echo x > deep.md)) && echo y > flat.md",
           "a/b/c/deep.md", "a/flat.md")
    unresolved("cd - is the previous directory, not the caller's own",
               "cd a && cd b && cd - && echo x > f.txt")
    unresolved("a bare cd is the home directory, which this file cannot know",
               "cd && echo x > f.txt")

    # --- `>&` is a redirect. Lexed as `>` plus `&` it becomes a segment break instead,
    # --- and the file it names is dropped without a trace.
    print("\n>& redirects a file, >&N duplicates a descriptor:")
    writes("cmd >& file writes that file",
           "python t.py >& all.log", "all.log")
    writes("cmd 2>& file writes that file too",
           "python t.py 2>& errors.log", "errors.log")
    clean("2>&1 is still an fd dup, not a file called 1",
          "python t.py 2>&1 | tail -5")
    clean("2>&- closes a descriptor and writes nothing",
          "python t.py 2>&-")

    # --- curl and wget, which attempt 1 called clean in every spelling. The figure to
    # --- quote for this is the classifier delta, reproduced independently twice over one
    # --- denominator: adding these moves 14 corpus commands from clean to resolved, adds
    # --- a target to 3 already-resolved ones, and moves 1 to unresolved. The unique-
    # --- command counts are methodology-dependent -- see `_download_targets` -- and this
    # --- comment used to carry one of them, contradicting that docstring in the same
    # --- commit.
    print("\ncurl and wget write the file they are told to write:")
    writes("curl -o writes its output path",
           "curl -o graph_agents/GRAPH.md https://example.invalid/a",
           "graph_agents/GRAPH.md")
    writes("curl --output writes its output path",
           "curl --output out.json https://example.invalid/a", "out.json")
    writes("curl --output=PATH writes it too",
           "curl --output=out.json https://example.invalid/a", "out.json")
    writes("curl -sSo is a short-flag cluster ending in -o",
           "curl -sSo out.json https://example.invalid/a", "out.json")
    writes("wget -O writes its output document",
           "wget -O out.html https://example.invalid/a", "out.html")
    writes("a cd applies to a curl output path like any other",
           "cd graph_agents && curl -s -o GRAPH.md https://example.invalid/a",
           "graph_agents/GRAPH.md")
    clean("curl -o /dev/null is not a write worth reporting",
          "curl -s https://example.invalid/health -o /dev/null")
    clean("curl -o - is stdout, not a file called -",
          "curl -s -o - https://example.invalid/a | head -5")
    clean("a curl with no output flag writes nothing this file can see",
          "curl -s https://example.invalid/a | head -5")
    unresolved("curl -O names the file from the remote resource at runtime",
               "curl -O https://example.invalid/a/z.tar")
    unresolved("a bare wget does the same",
               "wget https://example.invalid/a/z.tar")

    # --- Shapes that came back CLEAN on attempt 1 when the stated policy for a shape
    # --- this file cannot pin down is ([], True).
    print("\nwrappers, eval and substitutions fail in the stated direction:")
    writes("sudo is stripped and what it wraps is dispatched",
           "sudo rm -rf build", "build")
    writes("env with an assignment prefix is stripped too",
           "env FOO=1 rm -rf build", "build")
    writes("time is stripped",
           "time cp template.json config.json", "config.json")
    writes("timeout is stripped along with its duration",
           "timeout 30 mkdir -p out/reports", "out/reports")
    writes("a command substitution body is walked as a command",
           "echo $(rm -rf build)", "build")
    writes("a backtick body is walked the same way",
           "echo `rm -rf build`", "build")
    writes("a substitution inside double quotes is walked too",
           "echo \"$(rm -rf build)\"", "build")
    writes("an interpreter body inside a substitution still resolves",
           "X=$(python -c \"open('f.txt','w').write('x')\")", "f.txt")
    writes("eval of a literal is re-classified as shell",
           "eval \"echo x > out.txt\"", "out.txt")
    unresolved("eval of a variable is a shape, not a clean command",
               "eval \"$CMD\"")
    unresolved("xargs writes files named on stdin, not on this line",
               "ls *.md | xargs sed -i 's/a/b/'")
    clean("command -v is a lookup, not a run",
          "command -v gh")
    clean("a substitution that only reads is still clean",
          "echo \"branch $(git branch --show-current)\"")

    # --- An `xargs` replace string is a PLACEHOLDER. Emitting `{}` as a RESOLVED target
    # --- hands the guard a path that matches no approved file, which is a denial of work
    # --- the plan allowed -- the same failure class as a leaked subshell cwd, arriving
    # --- from a different direction. The unresolved flag is the whole honest answer.
    print("\nan xargs replace string is a placeholder, never a resolved path:")
    unresolved("xargs -I{} rm {} reports a shape and no target",
               "ls *.md | xargs -I{} rm {}")
    unresolved("the separated spelling -I {} does the same",
               "ls *.md | xargs -I {} rm {}")
    unresolved("a replace string appearing inside an operand is still a placeholder",
               "ls *.md | xargs -I{} mv {} {}.bak")
    unresolved("a replace string other than {} is honoured",
               "ls *.md | xargs -I@@ rm @@")
    unresolved("--replace=PAT is the same flag spelled long",
               "ls *.md | xargs --replace=@@ rm @@")
    # `-i` takes an OPTIONAL argument and is normally written bare, so listing it among
    # the flags that take a value made it eat `rm` -- and the whole command came back
    # CLEAN while three other spellings of it classified correctly.
    unresolved("xargs -i does not swallow the command it wraps",
               "ls | xargs -i rm {}")
    unresolved("xargs --replace bare does not swallow it either",
               "ls | xargs --replace rm {}")
    unresolved("xargs -n1 still classifies, which is the spelling that always worked",
               "ls *.md | xargs -n1 rm")
    unresolved("an operand that is NOT the replace string still resolves",
               "ls *.md | xargs -I{} mv {} archive/dest.md", "archive/dest.md")

    # --- A brace group is not a subshell: it does NOT scope a `cd`. Ignoring the `cd`
    # --- because a keyword sat in front of it reported the write at the wrong path, in
    # --- the direction that denies approved work.
    print("\na compound statement does not hide the command inside it:")
    writes("a brace group's cd applies to the write after it",
           "{ cd graph_agents; echo x > f.md; }", "graph_agents/f.md")
    writes("an if body inherits the cd its condition performed",
           "if cd graph_agents; then echo x > f.md; fi", "graph_agents/f.md")
    writes("a while body does too",
           "while cd graph_agents; do echo x > f.md; done", "graph_agents/f.md")
    writes("a write verb behind a keyword is still that verb",
           "{ rm -rf build; }", "build")
    unresolved("a loop variable as a cd target is not knowable",
               "for d in a b; do cd $d; echo x > f.md; done")
    unresolved("cd a || cd b ends in one of two directories, so neither is reported",
               "cd graph_agents || cd fleetview ; echo y > b.md")
    clean("`for rm in a b` is a loop variable named rm, not a delete",
          "for rm in a b; do echo $rm; done")

    # --- perl's in-place edit: the same mechanism as `sed -i`, spelled by the other
    # --- program that has it, and invisible while perl went only to the body inspector.
    print("\nperl -i is sed -i, and the write is the flag rather than the body:")
    writes("perl -i -pe writes its file operand",
           "perl -i -pe 's/a/b/' notes.md", "notes.md")
    writes("perl -pi -e is the same command",
           "perl -pi -e 's/a/b/' notes.md", "notes.md")
    writes("perl -i.bak keeps a backup and still writes the file",
           "perl -i.bak -pe 's/a/b/' graph_agents/GRAPH.md", "graph_agents/GRAPH.md")
    writes("a cd applies to a perl in-place target like any other",
           "cd graph_agents && perl -i -pe 's/a/b/' GRAPH.md", "graph_agents/GRAPH.md")
    clean("perl without -i is a read, exactly as sed without -i is",
          "perl -ne 'print if /TODO/' notes.md")
    clean("-MList::Util contains an i and is not the in-place flag",
          "perl -MList::Util -e 'print 1'")

    # --- The three spellings that made the pre-filter's superset property false. The
    # --- parser lexes all of these into the command word `rm`; the anchor is a raw
    # --- string and saw none of them. `writes()` asserts the pre-filter agrees.
    print("\nan escaped, quoted or assignment-prefixed verb is the same verb:")
    writes("a backslash-escaped verb is still that verb",
           "\\rm -rf build", "build")
    writes("a single-quoted verb is still that verb",
           "'rm' -rf build", "build")
    writes("a double-quoted verb is still that verb",
           "\"rm\" -rf build", "build")
    writes("an assignment whose value contains a space does not hide the verb",
           "FOO=\"a b\" rm -rf build", "build")
    writes("the same, in front of a wrapper",
           "FOO=\"a b\" sudo rm -rf build", "build")

    # --- `--staged` restores the INDEX. Reporting a target for it would deny a command
    # --- that changes nothing on disk, and `git add`, which stages the same way, is
    # --- already clean.
    print("\ngit restore: the index is not the working tree:")
    clean("git restore --staged . writes no file",
          "git restore --staged .")
    clean("the -- form is the same command",
          "git restore --staged -- graph_agents/GRAPH.md")
    writes("git restore --staged --worktree DOES write the tree",
           "git restore --staged --worktree notes.md", "notes.md")
    writes("a plain git restore writes the tree",
           "git restore notes.md", "notes.md")

    # --- Things that look like writes and are not. ---
    print("\nnear misses:")
    clean("git checkout -b creates a branch, not a file",
          "git checkout -b feat/bash-write-guard")
    clean("git switch is never a path write",
          "git switch master")
    clean("git apply --check does not touch the tree",
          "git apply --check fix.patch")
    clean("sed without -i is a read",
          "sed -n '1,5p' graph_agents/GRAPH.md")
    clean("tee with no file operand writes only stdout",
          "python tool.py | tee")
    clean("dd with no of= writes only stdout",
          "dd if=disk.img bs=1M count=1 | wc -c")
    clean("a here-string is input, not output",
          "wc -c <<< 'hello'")
    clean("input redirection is a read",
          "python tool.py < input.json")

    # --- The pre-filter's contract with its caller. ---
    print("\nthe pre-filter:")
    check("the pre-filter says no to git status",
          has_write_signature("git status --short"), False)
    check("the pre-filter says no to python -m pytest",
          has_write_signature("python -m pytest -q"), False)
    check("the pre-filter says no to node test.js",
          has_write_signature("node test.js"), False)
    check("the pre-filter says no to a plain grep",
          has_write_signature("grep -rn foo graph_agents/"), False)
    check("the pre-filter says no to ls",
          has_write_signature("ls -la"), False)
    check("the pre-filter says no to wc",
          has_write_signature("wc -l GRAPH.md"), False)
    check("the pre-filter says yes to a redirect",
          has_write_signature("echo x > out.txt"), True)
    check("the pre-filter says yes to a heredoc",
          has_write_signature("cat > f <<'EOF'\nx\nEOF"), True)
    check("nothing is classified without the pre-filter agreeing first",
          classify("git status --short"), ([], False))
    check("a non-string is not a command",
          classify(None), ([], False))
    check("an empty string is not a command", classify(""), ([], False))
    # The length cap is checked BEFORE the pre-filter, so the 128KB bound actually bounds
    # what the regex sees. `has_write_signature` is linear in a real command and
    # quadratic in a run of separators; a cap applied afterwards bounds nothing. An
    # oversized command is the documented fail-open answer -- a shape, never a denial.
    check("a command past MAX_COMMAND is a shape, and the pre-filter never runs on it",
          classify("echo " + "a" * MAX_COMMAND), ([], True))
    check("the pre-filter itself would have said no to that same command",
          has_write_signature("echo " + "a" * MAX_COMMAND), False)

    # --- The corpus half. These are the cases imagination does not produce. ---
    print("\n%d real read-only commands lifted from the corpus:" % len(READ_ONLY_CORPUS))
    for command in READ_ONLY_CORPUS:
        shown = command if len(command) <= 62 else command[:59] + "..."
        corpus_clean(shown, command)

    # --- The pre-filter's superset property, over generated spellings rather than a
    # --- sample. `measure_bash_corpus.py` runs this same question over the corpus, but a
    # --- corpus can only say the blind spot is empty today: attempt 1's counter printed 0
    # --- while two spellings the parser resolved exactly were invisible to the guard,
    # --- because the corpus happened not to contain them. This asks it of every command
    # --- in this file, of a matrix of the spellings the parser implements, AND of five
    # --- rewritings of each -- escaped, single-quoted, double-quoted, behind a spaced
    # --- assignment, and inside a brace group. Those five are where the anchor and the
    # --- lexer disagreed; the property is ANCHOR-RELATIVE, so the way to hold it is to
    # --- generate the families rather than to name them.
    print("\nthe pre-filter is a superset of the parser, over every command in this file:")
    swept = list(ALL_COMMANDS) + list(PRE_FILTER_MATRIX)
    swept += [variant for command in list(swept) for variant in spellings(command)]
    leaks = [c for c in swept if not prefilter_is_sound(c)]
    check("no command here resolves a write the pre-filter cannot see (%d swept)"
          % len(swept), leaks, [])
    for command in leaks[:10]:
        print("  leak: %s" % (command[:59] + "..." if len(command) > 62 else command))

    print()
    check("at least %d cases ran" % MINIMUM_CASES, CASES >= MINIMUM_CASES, True)
    check("at least %d of them are read-only CORPUS commands" % MINIMUM_READ_ONLY,
          CORPUS_CASES >= MINIMUM_READ_ONLY, True)

    print()
    print("%d cases, %d of them not-a-write, %d of those from the corpus"
          % (CASES, READ_ONLY_CASES, CORPUS_CASES))
    if FAILURES:
        print("FAILED (%d):" % len(FAILURES))
        for failure in FAILURES:
            print("  - %s" % failure)
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
