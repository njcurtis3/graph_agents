#!/usr/bin/env python
"""What files, if any, is this Bash command about to write?

    from bash_write_targets import classify, has_write_signature
    targets, unresolved = classify(command)

Nothing imports this yet. It exists on its own so that the iterative, likely-to-be-wrong
half of the Bash write guard could be built while `guard-builder-scope.py` -- which is
registered, live, and fails closed -- stayed byte-identical. A half-written guard does not
degrade to "unguarded"; it degrades to every builder write denied, including the write
that would fix it.

THE CONTRACT

  `has_write_signature(command)` -> bool. A cheap regex over the raw string, no parsing
  and no disk I/O. False means the command cannot write anything this file knows how to
  detect, so a caller may skip the rest -- including whatever state it would have read
  from disk. `classify()` calls it first itself, so the two can never disagree: if the
  pre-filter says no, `classify` returns `([], False)` without looking further.

  `classify(command)` -> `(resolved_targets, unresolved_write_shape)`.

    `resolved_targets`  the concrete paths the command will write, in order of first
                        appearance, deduplicated. A path is returned as the command wrote
                        it, with one deliberate exception described under `cd` below.

    `unresolved_write_shape`  True when a write IS present but its target could not be
                        pinned down -- a shell variable that was never assigned in this
                        same command, a `$(...)` substitution, a `git apply` whose targets
                        live inside the patch. Both halves can be true at once:
                        `echo a > kept.txt && echo b > "$SOMEWHERE"` returns one target
                        AND True.

  THIS FILE OWNS NO PATH MATCHER. It returns paths and has no opinion about whether any
  of them is in scope. Matching a target against an approved file set belongs to
  `approved_paths()` / `_match()` in the guard, and that guard has already been fixed
  TWICE for having two matchers that drifted apart. There will not be a third one here.

WHY A `cd` IS APPLIED, WHICH IS THE ONE PLACE A TARGET IS NOT VERBATIM

  877 of the 2073 unique Bash commands this fleet has ever run begin with `cd`. Returning
  `GRAPH.md` verbatim for `cd graph_agents && echo x > GRAPH.md` would hand the caller a
  path that resolves against the session root, so the caller would judge `repos/GRAPH.md`
  -- a file that does not exist -- and deny a write the plan had approved. So a `cd`
  earlier in the same command string is joined onto later relative targets. An absolute
  target is never touched. If the `cd` target itself cannot be resolved -- an unresolvable
  operand, `cd -`, or a bare `cd` to the home directory -- later RELATIVE targets become
  `unresolved_write_shape` instead of guesses; `git -C DIR` is handled the same way, for
  that segment only.

  A `cd` reaches the next command only when both run in THIS shell. `( cd x && ... )`,
  a pipeline component and a background job are subshells, and their `cd` dies with them:
  `(cd graph_agents && echo a > a.md) ; echo b > b.md` writes `graph_agents/a.md` and then
  `b.md`, not `graph_agents/b.md`. Leaking a subshell's cwd is not an unresolved flag, it
  is a WRONG resolved path -- indistinguishable downstream from a right one, and pointed
  at denying work the plan approved.

WHAT IT DETECTS

  redirects           `>` `>>` `>|` `&>` `&>>` `>&` and any fd form (`2>`, `1>>`).
                      `2>&1` and `2>&-` are fd duplications and not files
  heredocs            the body is removed before parsing, so a heredoc that happens to
                      contain `>` or the word `rm` cannot be mistaken for a command; the
                      redirect on the heredoc's OWN line is what makes it a write
  tee                 every file operand, `-a` included
  install             destination, or every operand under `-d`, or `-t DIR`
  dd                  `of=`
  truncate            every file operand
  mv                  destination AND sources -- a move is a write at one end and a
                      delete at the other, and a delete outside the approved set is a
                      modification the guard should see
  cp                  destination only; the sources are reads
  git                 `checkout` / `restore` pathspecs, `apply`; `checkout -b` is a
                      branch, not a write, and neither is `switch`
  sed -i              every file operand, and ONLY with `-i`
  rm rmdir touch mkdir ln     every operand
  interpreter bodies  `python -c`, `node -e`, `perl -e`, and `python -` fed by a heredoc:
                      the body is INSPECTED for a write call rather than flagged for
                      being a `-c`. Measured over the corpus: 356 commands use this
                      shape and only 57 of them write. Flagging the shape would invent
                      299 false positives.
  curl / wget         `curl -o FILE`, `curl --output=FILE`, `wget -O FILE`, including the
                      `-sSo FILE` cluster spelling. `-o /dev/null` and `-o -` are not
                      writes. `curl -O` and a bare `wget URL` name their file from the
                      remote resource at runtime, so they are an unresolved SHAPE
  sh -c / bash -c     the body is re-classified as a shell command, depth-limited
  eval                a literal `eval "..."` is re-classified the same way
  $(...) / backticks  the substitution body is walked as a command, so `echo $(rm -rf x)`
                      is the delete it is
  wrapper verbs       `sudo`, `doas`, `env`, `nice`, `nohup`, `command`, `time`,
                      `timeout`, `stdbuf`, `xargs` are stripped and what they wrap is
                      dispatched as itself. `xargs` additionally reports an unresolved
                      shape, because the files it writes arrive on stdin

WHAT IT DOES NOT DETECT, ON PURPOSE, SO THE CALLER CAN SAY SO OUT LOUD

  * A write performed by a program the command merely invokes: `npm run build`, `make`,
    `pytest`, `bash script.sh`, or a script written to an approved path and then run.
    This is the largest hole and it is deliberate -- closing it means denying every test
    command, and a guard that denies pytest is switched off within a day.
  * An obfuscated write: a base64 or `exec` payload inside `python -c`, a target
    assembled from runtime values. `eval` of a VARIABLE is here too -- it comes back as
    an unresolved shape rather than a target, which is a record and not a denial.
  * `powershell`, `awk`'s own `print > file`, `patch`, and a bare `>` written by a program
    the command invokes. Each one added is a new way to deny real work; they are named
    here so the limit is documented rather than discovered. `curl` and `wget` USED to sit
    in this list on the grounds that they were not among the ten evidenced mechanisms.
    Measured, that was simply wrong -- `curl` is in command position 171 times in the
    corpus and 9 unique commands write a literal path with `-o` -- so they moved up to
    the detected list instead. See `_download_targets` for the full breakdown.
  * A write flag the parser reads but a MEASUREMENT could not have shown: this list is
    kept honest by the pre-filter soundness counter in `measure_bash_corpus.py`, which
    asks the parser directly for every command the pre-filter rejected and must print 0.
  * Anything a variable hides that was not assigned in the same command string. There is
    no environment lookup here on purpose: the classifier is pure, so its answer for a
    given string is the same in a test as it is in a hook.

FAILURE DIRECTION. A command this file cannot parse at all comes back as
`([], True)` -- no targets, write shape unresolved. The caller is expected to allow and
record, never to deny on it. A parser that denies what it failed to understand is a
parser that gets routed around.
"""
import posixpath
import re

# A command longer than this is not something a builder typed; parsing it is a cost with
# no upside, so it is reported as an unresolvable write shape and left to the caller.
MAX_COMMAND = 128 * 1024

# `bash -c '... bash -c "..."'`. Three is already further than anything in the corpus.
MAX_DEPTH = 3

# Writing here writes nothing. `> /dev/null` is 60 of the corpus's 962 redirects and
# reporting it would be noise in every listing a human ever reads.
NULL_SINKS = frozenset((
    "/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty",
    "/dev/fd/1", "/dev/fd/2", "nul", "con",
))

# The pre-filter. It runs on every Bash call in the session, before the caller touches
# disk, so it is regex over the raw string and nothing more.
#
# It is deliberately a SUPERSET of what the parser below can act on: a false positive here
# costs one state.json read, while a false negative here is a write nobody ever looks at.
# What it must NOT do is fire on the read-only commands this fleet actually runs -- `git
# status`, `git log`, `git diff`, `grep`, `ls`, `wc`, `python -m pytest`, `node test.js` --
# because those are the hot path and they must pay nothing.
#
# THE SUPERSET PROPERTY IS STRUCTURAL, NOT MEASURED, and it is spelled this way because
# the first version of this file was neither. That version paired a verb with its write
# flag inside ONE regex, separated by a bounded `[^|;&\n]{0,120}` window. Two spellings
# the parser resolves exactly -- `sed --in-place` and `node --eval` -- could not match a
# window that required a single-dash flag, so the guard never saw them while the same
# commands spelled `-i` and `-e` were denied. The property was true only of the commands
# that happened to be in the corpus, and a bounded window has the same defect for any
# long flag list, any quoted `|`, and anything past 120 characters.
#
# So the verb and the flag are searched INDEPENDENTLY now. A paired clause fires when the
# verb appears ANYWHERE in the string and a flag that could make that verb write appears
# ANYWHERE in the string. No distance, ordering, quoting or window length can hide a
# pairing the parser would act on, and each flag pattern is a deliberate superset of the
# predicate the parser uses (`_in_place`, `_output_flag`, the `-c`/`-e`/`--eval` scan).
# The cost is over-firing on `grep -i sed`, and over-firing costs one state.json read.
_REDIRECTION = re.compile(r">|<<")

# A write verb only counts in a COMMAND POSITION -- start of input, after a separator, an
# opening paren or a backtick, after wrapper verbs and `VAR=x` prefixes. Not because it is
# prettier, but because that is the only place the parser below will act on one, so
# anywhere else is a state.json read bought for nothing. The word `rm` inside a heredoc
# paragraph is prose. `(` and `` ` `` are in the anchor class because the parser walks
# into `$(...)` and backtick bodies, and the pre-filter has to reach where the parser goes.
_COMMAND_POSITION = re.compile(
    r"(?:\A|[;&|\n()`])\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
    r"(?:\S*/)?"
    r"(?:tee|install|dd|truncate|mv|cp|rm|rmdir|touch|mkdir|ln|wget|eval)\b"
)

# A wrapper verb in command position, for the paired clause below. It is paired rather
# than folded into `_COMMAND_POSITION` because `nice -n 5 rm`, `timeout 30 mkdir` and
# `xargs -I {} rm` put arbitrary operands between the wrapper and the verb, and matching
# those inline needs a nested quantifier -- a catastrophic-backtracking shape to run on
# every Bash call. Two flat searches say the same thing and cannot blow up.
_WRAPPER_POSITION = re.compile(
    r"(?:\A|[;&|\n()`])\s*(?:\S*/)?"
    r"(?:sudo|doas|env|nice|nohup|command|time|timeout|stdbuf|xargs)\b"
)

# (a command name, a flag that can make it write). Both are searched over the whole
# string and independently of each other -- see the note above.
_PAIRED_SIGNATURES = (
    (_WRAPPER_POSITION,
     re.compile(r"\b(?:tee|install|dd|truncate|mv|cp|rm|rmdir|touch|mkdir|ln|sed|git"
                r"|curl|wget|eval|python|python3|py|node|nodejs|perl|ruby"
                r"|bash|sh|zsh|dash)\b")),
    (re.compile(r"\bsed\b"),
     re.compile(r"(?:\A|\s)(?:-[A-Za-z]*i|--in-place)")),
    (re.compile(r"\bgit\b"),
     re.compile(r"\b(?:checkout|restore|apply)\b")),
    (re.compile(r"\b(?:python|python3|py|node|nodejs|perl|ruby|bash|sh|zsh|dash)\b"),
     re.compile(r"(?:\A|\s)(?:-[A-Za-z]*[ce]|--eval)")),
    (re.compile(r"\bcurl\b"),
     re.compile(r"(?:\A|\s)(?:-[A-Za-z0-9#]*[oO]|--output|--remote-name)")),
)

# Longest first: `<<<` is a herestring and `<<-` a heredoc, and neither may be read as
# `<<` plus something. `>&` sits before `>` for the same reason -- lexed as `>` plus `&`
# it becomes a segment break and `cmd >& file` loses its file entirely.
_OPERATORS = ("<<<", "&>>", "<<-", ">>", "<<", "&&", "||", ">|", "&>", ">&",
              ">", "<", "|", ";", "&", "(", ")")

_SEPARATORS = frozenset(("|", "||", "&&", ";", "&", "\n", "(", ")"))
_WRITE_REDIRECTS = frozenset((">", ">>", ">|", "&>", "&>>", ">&"))

# The separators that put their segment in a SUBSHELL, so a `cd` inside it dies with it.
_SUBSHELL_SEPARATORS = frozenset(("|", "&"))

_VAR = re.compile(r"\$(\{[A-Za-z_][A-Za-z0-9_]*\}|[A-Za-z_][A-Za-z0-9_]*)")
_LEFTOVER_VAR = re.compile(r"\$[A-Za-z_{(0-9@*?!#$]")
_ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", re.DOTALL)
_ABSOLUTE = re.compile(r"^(?:/|~|\\\\|[A-Za-z]:[\\/])")
_HEREDOC_START = re.compile(r"<<-?\s*(\"[^\"]*\"|'[^']*'|[A-Za-z_][A-Za-z0-9_]*)")
_SUBSTITUTION = re.compile(r"\$\(|`")
_SHORT_CLUSTER = re.compile(r"^[A-Za-z0-9#]*$")
_DURATION = re.compile(r"^[0-9]+(?:\.[0-9]+)?[smhd]?$")

# The cwd of a segment whose `cd` could not be resolved. Distinct from "" -- which means
# the caller's own cwd -- because a relative target under an UNKNOWN cwd is an unresolved
# write shape, while a relative target under "" is exactly what the command said.
_UNKNOWN = object()


def has_write_signature(command):
    """Could this command write anything? Cheap, no parsing, no disk."""
    if not isinstance(command, str) or not command:
        return False
    if _REDIRECTION.search(command) or _COMMAND_POSITION.search(command):
        return True
    return any(verb.search(command) and flag.search(command)
               for verb, flag in _PAIRED_SIGNATURES)


def classify(command):
    """(resolved_targets, unresolved_write_shape). See the module docstring."""
    if not has_write_signature(command):
        return [], False
    if len(command) > MAX_COMMAND:
        return [], True
    try:
        targets, unresolved = _walk(command, "", {}, 0)
    except Exception:
        # A shape we could not parse is a shape we could not resolve. Saying so is the
        # whole point: the caller allows and records rather than denying on a crash.
        return [], True
    return targets, unresolved


# --------------------------------------------------------------------------- lexing


def _strip_heredocs(command):
    """(command with heredoc BODIES removed, [(body, expands), ...] in order of `<<`).

    A heredoc body is data, not shell. Left in place, `cat <<'EOF' ... rm -rf / ... EOF`
    parses as a delete, and `python - <<PY` parses its own source as commands. Bodies come
    back separately so an interpreter's body can still be inspected as an interpreter's
    body.

    `expands` is the shell's own rule: `<<PY` interpolates `$VAR` into the body, `<<'PY'`
    does not. It matters because a body that writes to `os.path.join(r"$SP", "x.js")` is
    writing to a path the shell already filled in from an assignment two lines up, and
    reading the body literally would call that unresolvable when it is not.
    """
    kept = []
    bodies = []
    pending = []            # [(delimiter, expands, [collected lines]), ...], in order
    for line in command.split("\n"):
        if pending:
            delimiter, expands, collected = pending[0]
            if line.strip() == delimiter:
                bodies.append(("\n".join(collected), expands))
                pending.pop(0)
                continue            # the terminator line is not shell either
            collected.append(line)
            continue
        kept.append(line)
        for delimiter, expands in _heredoc_delimiters(line):
            pending.append((delimiter, expands, []))
    for _delimiter, expands, collected in pending:
        bodies.append(("\n".join(collected), expands))   # unterminated; take what exists
    return "\n".join(kept), bodies


def _heredoc_delimiters(line):
    """[(delimiter, expands)] opened by this line, ignoring `<<` in quotes and `<<<`."""
    masked = _mask_quoted(line)
    found = []
    index = 0
    while True:
        index = masked.find("<<", index)
        if index < 0:
            return found
        if masked[index + 2:index + 3] == "<":       # herestring, not a heredoc
            index += 3
            continue
        match = _HEREDOC_START.match(line, index)
        if match:
            raw = match.group(1)
            found.append((raw.strip("\"'"), raw[:1] not in ("'", '"')))
        index += 2


def _mask_quoted(line):
    """The line with quoted regions blanked, so operators inside them are not seen."""
    out = []
    quote = ""
    for char in line:
        if quote:
            out.append(" ")
            if char == quote:
                quote = ""
            continue
        if char in "\"'":
            quote = char
            out.append(" ")
            continue
        out.append(char)
    return "".join(out)


def _tokenize(text):
    """[("word", [(chunk, expandable), ...]) | ("op", text), ...].

    A word is kept as chunks rather than a string so that expansion knows which parts came
    out of single quotes: `echo '$HOME' > out` writes `out`, and `$HOME` in it is four
    literal characters, not an unresolved variable.
    """
    tokens = []
    pieces = []
    state = {"chunk": [], "expandable": True}

    def push(text_, expandable):
        if state["chunk"] and state["expandable"] != expandable:
            pieces.append(("".join(state["chunk"]), state["expandable"]))
            state["chunk"] = []
        state["expandable"] = expandable
        state["chunk"].append(text_)

    def end_word():
        if state["chunk"]:
            pieces.append(("".join(state["chunk"]), state["expandable"]))
            state["chunk"] = []
            state["expandable"] = True
        if pieces:
            tokens.append(("word", list(pieces)))
            del pieces[:]

    index = 0
    length = len(text)
    while index < length:
        char = text[index]

        if char == "\\" and index + 1 < length:
            push(text[index + 1], False)
            index += 2
            continue

        if char == "'":
            end = text.find("'", index + 1)
            end = length if end < 0 else end
            push(text[index + 1:end], False)
            index = end + 1
            continue

        if char == '"':
            cursor = index + 1
            collected = []
            while cursor < length:
                if text[cursor] == "\\" and cursor + 1 < length:
                    collected.append(text[cursor + 1])
                    cursor += 2
                    continue
                if text[cursor] == '"':
                    break
                collected.append(text[cursor])
                cursor += 1
            push("".join(collected), True)
            index = cursor + 1
            continue

        if char == "$" and text[index + 1:index + 2] == "(":
            # Consumed whole so a substitution's own spaces and `)` do not split the word
            # or fake a segment boundary. `_expand` will refuse to resolve it.
            depth = 0
            cursor = index + 1
            while cursor < length:
                if text[cursor] == "(":
                    depth += 1
                elif text[cursor] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                cursor += 1
            push(text[index:cursor + 1], True)
            index = cursor + 1
            continue

        if char == "`":
            end = text.find("`", index + 1)
            end = length if end < 0 else end
            push(text[index:end + 1], True)
            index = end + 1
            continue

        if char in " \t\r":
            end_word()
            index += 1
            continue

        if char == "\n":
            end_word()
            tokens.append(("op", "\n"))
            index += 1
            continue

        if char == "#" and not state["chunk"] and not pieces:
            end = text.find("\n", index)
            index = length if end < 0 else end
            continue

        operator = _operator_at(text, index)
        if operator:
            # `2>` and `1>>` are one redirect, not the word "2" followed by one. Drop a
            # pending all-digit word so it is not mistaken for a command or an operand.
            if operator[0] in "<>" and not pieces and "".join(state["chunk"]).isdigit():
                state["chunk"] = []
            end_word()
            tokens.append(("op", operator))
            index += len(operator)
            continue

        push(char, True)
        index += 1

    end_word()
    return tokens


def _operator_at(text, index):
    for operator in _OPERATORS:
        if text.startswith(operator, index):
            return operator
    return None


def _segments(tokens):
    """[(token list, the separator that ENDED it), ...], split on `|`, `&&`, `;` and kin.

    The separator is kept rather than thrown away because it decides SCOPE, and scope is
    what makes a `cd` reach the next command or not. `(` and `)` come back as their own
    entries with an empty token list, so the walker can push and pop a cwd around a
    subshell instead of letting a `cd` inside one escape into the rest of the line.
    """
    out = []
    current = []
    for kind, value in tokens:
        if kind == "op" and value in _SEPARATORS:
            if value in ("(", ")"):
                if current:
                    out.append((current, ""))
                    current = []
                out.append(([], value))
                continue
            out.append((current, value))
            current = []
            continue
        current.append((kind, value))
    if current:
        out.append((current, ""))
    return out


# ------------------------------------------------------------------------ expansion


def _expand(pieces, env):
    """(text, resolved) for one word. `resolved` is False if anything stayed unknown."""
    out = []
    resolved = [True]

    def substitute(match):
        name = match.group(1).strip("{}")
        value = env.get(name)
        if value is None or not value[1]:
            resolved[0] = False
            return match.group(0)
        return value[0]

    for chunk, expandable in pieces:
        if not expandable:
            out.append(chunk)
            continue
        if chunk.startswith("$(") or chunk.startswith("`"):
            resolved[0] = False                 # a substitution is a runtime value
            out.append(chunk)
            continue
        replaced = _VAR.sub(substitute, chunk)
        if _LEFTOVER_VAR.search(replaced):
            # `${X:-y}`, `$1`, `$@`, a nested `$(`. Anything still wearing a `$` after
            # substitution is something this file chose not to model.
            resolved[0] = False
        out.append(replaced)
    return "".join(out), resolved[0]


def _place(target, cwd):
    """(path as the caller should read it, resolved). Applies an in-command `cd`."""
    if _ABSOLUTE.match(target):
        return target, True
    if cwd is _UNKNOWN:
        return target, False
    if not cwd:
        return target, True
    joined = cwd.replace("\\", "/").rstrip("/") + "/" + target.replace("\\", "/")
    return posixpath.normpath(joined), True


def _is_null_sink(target):
    return target.replace("\\", "/").lower() in NULL_SINKS


# -------------------------------------------------------------------------- walking


class _Result(object):
    """Targets in first-seen order, plus the one flag that says "and something else"."""

    def __init__(self):
        self.targets = []
        self.unresolved = False

    def add(self, target, resolved, cwd):
        if not resolved or not target:
            self.unresolved = True
            return
        if "$" in target:
            # A `$` that survived every expansion this file does is a value it did not
            # resolve, whichever layer put it there -- a shell word, or a heredoc body
            # the shell would have interpolated. Reporting it as a path would hand the
            # caller a filename no process will ever open.
            self.unresolved = True
            return
        if _is_null_sink(target):
            return
        placed, ok = _place(target, cwd)
        if not ok:
            self.unresolved = True
            return
        if placed not in self.targets:
            self.targets.append(placed)

    def merge(self, other, cwd):
        for target in other[0]:
            self.add(target, True, cwd)
        self.unresolved = self.unresolved or other[1]


def _walk(command, cwd, env, depth):
    """(targets, unresolved) for a whole command string at a given cwd."""
    result = _Result()
    if depth > MAX_DEPTH:
        result.unresolved = True
        return result.targets, result.unresolved

    text, bodies = _strip_heredocs(command)
    body_queue = list(bodies)
    env = dict(env)

    # A `cd` reaches the next command only when both of them run in THIS shell. Inside
    # `( ... )` it dies at the closing paren, and a pipeline component or a background
    # job is a subshell too, so its `cd` dies with the component. Getting this wrong is
    # not an unresolved flag -- it is a WRONG resolved path, which nothing downstream can
    # tell from a right one, and it fails in the direction that denies approved work.
    scopes = []
    previous = ""
    for segment, separator in _segments(_tokenize(text)):
        if not segment and separator == "(":
            scopes.append(cwd)
            previous = ""
            continue
        if not segment and separator == ")":
            cwd = scopes.pop() if scopes else cwd
            previous = ""
            continue
        moved = _walk_segment(segment, body_queue, env, cwd, depth, result)
        # Ends a pipeline component or is backgrounded, or follows a `|` and so is a
        # pipeline component itself. `||` is a different string and is not one of these.
        if separator not in _SUBSHELL_SEPARATORS and previous != "|":
            cwd = moved
        previous = separator
    return result.targets, result.unresolved


def _walk_segment(segment, body_queue, env, cwd, depth, result):
    """Handle one segment; return the cwd the NEXT segment inherits."""
    words = []
    heredocs = []
    index = 0
    while index < len(segment):
        kind, value = segment[index]
        index += 1
        if kind == "word":
            words.append(value)
            continue

        if value in ("<<", "<<-"):
            heredocs.append(body_queue.pop(0) if body_queue else ("", False))
            index += 1                                  # the delimiter word
            continue
        if value in ("<<<", "<"):
            index += 1                                  # input, not output
            continue
        if value in _WRITE_REDIRECTS:
            if index < len(segment) and segment[index] == ("op", "&"):
                index += 2                              # `> &1`: an fd dup, not a file
                continue
            if index < len(segment) and segment[index][0] == "word":
                target, resolved = _expand(segment[index][1], env)
                index += 1
                if value == ">&" and (target.isdigit() or target == "-"):
                    continue                            # `2>&1`, `2>&-`: an fd dup
                result.add(target, resolved, cwd)
            continue

    # Leading `NAME=value` -- the assignments that make `$SP/out.log` resolvable at all.
    expanded = []
    leading = True
    for word in words:
        text, resolved = _expand(word, env)
        match = _ASSIGNMENT.match(text) if leading else None
        if match:
            env[match.group(1)] = (match.group(2), resolved)
            continue
        leading = False
        expanded.append((text, resolved))

    # After the assignments, so `SP=/tmp echo $(rm $SP/x)` sees `SP`; before the early
    # return, so a segment that is nothing BUT a substitution is still walked.
    _substitutions(segment, env, cwd, depth, result)

    if not expanded:
        return cwd

    name = posixpath.basename(expanded[0][0].replace("\\", "/"))
    args = expanded[1:]

    if name == "export":
        for text, resolved in args:
            match = _ASSIGNMENT.match(text)
            if match:
                env[match.group(1)] = (match.group(2), resolved)
        return cwd

    if name == "cd":
        return _new_cwd(args, cwd)

    # Done here rather than at collection time so that a `SP=... python - <<PY` in ONE
    # segment has its assignment recorded before the body that uses it is expanded.
    bodies = []
    for body, expands in heredocs:
        if expands and "$" in body:
            body = _expand([(body, True)], env)[0]
        bodies.append(body)

    _command_targets(name, args, bodies, env, cwd, depth, result)
    return cwd


def _substitutions(segment, env, cwd, depth, result):
    """Walk the body of every `$(...)` and backtick in this segment as a command.

    `echo $(rm -rf build)` really does delete `build`, and `X=$(python -c "...")` really
    does run the interpreter body. The first version of this file returned ([], False)
    for both -- CLEAN -- because `_tokenize` swallows a substitution whole and nobody
    ever looked inside. Clean is the wrong answer in the wrong direction: this module's
    stated policy is that a shape it cannot resolve comes back ([], True), and a shape it
    CAN resolve should come back with the path. A substitution runs in a subshell, so its
    own `cd` starts fresh and cannot leak back out here.
    """
    for kind, value in segment:
        if kind != "word":
            continue
        for chunk, expandable in value:
            if not expandable or not _SUBSTITUTION.search(chunk):
                continue
            for body in _substitution_bodies(chunk):
                if body.strip():
                    result.merge(_walk(body, "", env, depth + 1), cwd)


def _substitution_bodies(text):
    """The inner text of every `$(...)` and `` `...` `` in one expandable chunk."""
    out = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] == "$" and text[index + 1:index + 2] == "(":
            depth = 0
            cursor = index + 1
            while cursor < length:
                if text[cursor] == "(":
                    depth += 1
                elif text[cursor] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                cursor += 1
            out.append(text[index + 2:cursor])
            index = cursor + 1
            continue
        if text[index] == "`":
            end = text.find("`", index + 1)
            end = length if end < 0 else end
            out.append(text[index + 1:end])
            index = end + 1
            continue
        index += 1
    return out


def _new_cwd(args, cwd):
    # `-` is an OPERAND of `cd`, not a flag, and dropping it with the flags is what made
    # the `target == "-"` branch below unreachable -- so `cd -` fell through to `return
    # ""`, the RESOLVED "caller's own cwd" sentinel, and every later relative target was
    # placed at a directory the command was not in. A bare `cd` has the same defect for a
    # different reason: it goes to the home directory, which this file cannot know.
    operands = [a for a in args if a[0] == "-" or not a[0].startswith("-")]
    if not operands:
        return _UNKNOWN                                 # `cd` alone: home. Unknowable.
    target, resolved = operands[0]
    if not resolved or target == "-":                   # `cd -`: the previous directory
        return _UNKNOWN
    if _ABSOLUTE.match(target):
        return target.replace("\\", "/").rstrip("/")
    if cwd is _UNKNOWN:
        return _UNKNOWN
    if not cwd:
        return posixpath.normpath(target.replace("\\", "/"))
    return posixpath.normpath(cwd.rstrip("/") + "/" + target.replace("\\", "/"))


# ---------------------------------------------------------------------- the verbs


def _operands(args, valued=(), stop_flags=()):
    """Non-flag arguments, honouring `--`, `--flag=value` and flags that take a value.

    `stop_flags` are flags whose presence means this invocation is not a write at all;
    when one is seen the caller gets None back rather than a list.
    """
    out = []
    index = 0
    while index < len(args):
        text = args[index][0]
        if text == "--":
            out.extend(args[index + 1:])
            return out
        if text in stop_flags:
            return None
        if text.startswith("-") and len(text) > 1:
            if text in valued:
                index += 2
                continue
            index += 1
            continue
        out.append(args[index])
        index += 1
    return out


def _add_all(operands, result, cwd):
    for text, resolved in operands:
        result.add(text, resolved, cwd)


def _command_targets(name, args, heredocs, env, cwd, depth, result):
    """Everything that is a write because of WHICH command it is, not because of a `>`."""
    if name in _WRAPPER_VALUED:
        _wrapper_targets(name, args, heredocs, env, cwd, depth, result)
        return

    if name == "eval":
        # `eval "echo x > out.txt"` is that redirect. `eval "$CMD"` is the documented
        # hole -- but it is an unresolved write shape now, not a clean command.
        if all(resolved for _text, resolved in args):
            result.merge(_walk(" ".join(t for t, _r in args), "", env, depth + 1), cwd)
        else:
            result.unresolved = True
        return

    if name in ("curl", "wget"):
        _download_targets(name, args, result, cwd)
        return

    if name == "tee":
        _add_all(_operands(args), result, cwd)
        return

    if name == "install":
        if any(a[0].startswith("-d") for a in args):
            _add_all(_operands(args, valued=("-m", "--mode", "-o", "-g")), result, cwd)
            return
        operands = _operands(args, valued=("-m", "--mode", "-o", "-g", "-t",
                                           "--target-directory"))
        directory = _flag_value(args, ("-t", "--target-directory"))
        if directory is not None:
            result.add(directory[0], directory[1], cwd)
        elif len(operands) >= 2:
            result.add(operands[-1][0], operands[-1][1], cwd)
        return

    if name == "dd":
        for text, resolved in args:
            if text.startswith("of="):
                result.add(text[3:], resolved, cwd)
        return

    if name == "truncate":
        _add_all(_operands(args, valued=("-s", "--size", "-r", "--reference")),
                 result, cwd)
        return

    if name == "mv":
        # Both ends. The destination is written and every source is removed, and a
        # removal outside the approved set is a modification the caller should see.
        _add_all(_operands(args, valued=("-t", "--target-directory", "-S", "--suffix")),
                 result, cwd)
        directory = _flag_value(args, ("-t", "--target-directory"))
        if directory is not None:
            result.add(directory[0], directory[1], cwd)
        return

    if name == "cp":
        operands = _operands(args, valued=("-t", "--target-directory", "-S", "--suffix"))
        directory = _flag_value(args, ("-t", "--target-directory"))
        if directory is not None:
            result.add(directory[0], directory[1], cwd)
        elif len(operands) >= 2:
            result.add(operands[-1][0], operands[-1][1], cwd)
        return

    if name in ("rm", "rmdir", "touch", "mkdir"):
        valued = ("-d", "--date", "-r", "--reference", "-t", "-m", "--mode")
        _add_all(_operands(args, valued=valued), result, cwd)
        return

    if name == "ln":
        operands = _operands(args)
        if len(operands) >= 2:
            result.add(operands[-1][0], operands[-1][1], cwd)
        elif operands:
            result.add(posixpath.basename(operands[0][0].replace("\\", "/")),
                       operands[0][1], cwd)
        return

    if name == "sed":
        _sed_targets(args, result, cwd)
        return

    if name == "git":
        _git_targets(args, result, cwd)
        return

    if name in ("python", "python3", "py", "node", "nodejs", "perl", "ruby"):
        _interpreter_targets(name, args, heredocs, result, cwd)
        return

    if name in ("sh", "bash", "zsh", "dash"):
        body = _flag_value(args, ("-c",))
        bodies = [body[0]] if body is not None and body[1] else []
        if body is not None and not body[1]:
            result.unresolved = True
        bodies.extend(heredocs)
        for text in bodies:
            result.merge(_walk(text, "", env, depth + 1), cwd)
        return


# Verbs that run ANOTHER command. Each maps to the flags of its own that take a value, so
# the wrapper can be stripped and the thing it wraps dispatched as itself: `sudo rm -rf
# build` is the write `rm -rf build` is. The first version of this file had no such
# branch, so every one of these came back CLEAN -- and a wrapper verb also walked past
# the pre-filter, which is why `_COMMAND_POSITION` now allows them in front of a verb.
_WRAPPER_VALUED = {
    "sudo": ("-u", "-g", "-p", "--user", "--group", "--prompt"),
    "doas": ("-u", "-C"),
    "env": ("-u", "--unset"),
    "nice": ("-n", "--adjustment"),
    "nohup": (),
    "command": (),
    "time": (),
    "timeout": ("-s", "--signal", "-k", "--kill-after"),
    "stdbuf": ("-i", "-o", "-e", "--input", "--output", "--error"),
    "xargs": ("-I", "-i", "-n", "-P", "-a", "-d", "-E", "-L", "-s", "--replace",
              "--max-args", "--max-procs", "--arg-file", "--delimiter", "--eof",
              "--max-lines", "--max-chars"),
}

# The verbs `_command_targets` treats as writes. Only `xargs` needs to ask: the files it
# writes arrive on stdin rather than on this command line.
_WRITE_VERBS = frozenset((
    "tee", "install", "dd", "truncate", "mv", "cp", "rm", "rmdir", "touch", "mkdir",
    "ln", "sed", "git", "curl", "wget",
))


def _wrapper_targets(name, args, heredocs, env, cwd, depth, result):
    """Strip a wrapper verb and dispatch on the command it wraps."""
    if name == "command" and any(a[0] in ("-v", "-V") for a in args):
        return                                  # `command -v gh` is a lookup, not a run
    valued = _WRAPPER_VALUED[name]
    index = 0
    while index < len(args):
        text = args[index][0]
        if text == "--":
            index += 1
            break
        if text in valued:
            index += 2
            continue
        if text.startswith("-") and len(text) > 1:
            index += 1
            continue
        if _ASSIGNMENT.match(text):
            index += 1                          # `env FOO=1 rm x`
            continue
        if name == "timeout" and _DURATION.match(text):
            index += 1                          # `timeout 30 python t.py`
            continue
        break
    if index >= len(args):
        return
    inner = posixpath.basename(args[index][0].replace("\\", "/"))
    if name == "xargs" and inner in _WRITE_VERBS:
        # `ls *.md | xargs sed -i 's/a/b/'` writes files named on STDIN. The write is
        # real and its targets are not in this string, which is the definition of an
        # unresolved write shape.
        result.unresolved = True
    _command_targets(inner, args[index + 1:], heredocs, env, cwd, depth, result)


def _download_targets(name, args, result, cwd):
    """`curl -o` / `-O`, `wget -O`. Added after the corpus was measured, not before.

    The docstring used to name `curl` among the mechanisms this fleet has never used.
    That claim was false in the direction that matters. Read through this file's own
    lexer, `curl` sits in COMMAND POSITION 171 times across the 2078 unique corpus
    commands, and 93 of those invocations carry an output flag: 64 write `/dev/null` and
    drop out at `_is_null_sink`, 16 name a shell variable, and 13 name a literal path
    right there on the command line. By unique command that is 57 / 8 / 9 -- and the 9
    are more real use than `mv` (2) and `touch` (2) combined, both of which are detected.
    Adding this moved 12 corpus commands from clean to resolved, gave 3 already-resolved
    commands another target, and moved 1 to unresolved.

    (The review that asked for this counted 28. That is the number of NON-`/dev/null`
    output-flag occurrences, which is 29 here on a corpus three commands larger; roughly
    half of them name a variable rather than a path. The mechanism is real either way,
    and the smaller number is the one that belongs in a document.)

    `curl -O` and a bare `wget URL` name the file after the remote resource, which is
    decided at runtime by the URL the transfer ends up at. Those are reported as an
    unresolved SHAPE rather than guessed from the URL: a wrong resolved path is worse
    than an honest unresolved one, because nothing downstream can tell it was a guess.
    """
    letter, longs = (("o", ("--output",)) if name == "curl"
                     else ("O", ("--output-document",)))
    named = False
    index = 0
    while index < len(args):
        text, resolved = args[index]
        if name == "wget" and text in ("--spider", "--version", "--help"):
            return                              # asks, does not fetch
        value = _output_flag(text, letter, longs)
        if value is not None:
            named = True
            if not value:
                if index + 1 >= len(args):
                    result.unresolved = True
                    return
                index += 1
                value, resolved = args[index]
            if value != "-":                    # `-o -` / `-O -` is stdout
                result.add(value, resolved, cwd)
        index += 1
    if named:
        return
    if name == "wget" or any(_output_flag(a[0], "O", ("--remote-name",
                                                      "--remote-name-all")) is not None
                             for a in args):
        result.unresolved = True


def _output_flag(text, letter, longs):
    """None when `text` is not this output flag; "" when its value is the NEXT argument.

    Otherwise the value carried inside the flag itself -- `-ofile`, `--output=file`.
    `curl -sSo out.json` is a short-flag cluster ending in the flag that takes the value,
    which is why the letter is looked for anywhere in the cluster rather than at the end.
    """
    for long_flag in longs:
        if text == long_flag:
            return ""
        if text.startswith(long_flag + "="):
            return text[len(long_flag) + 1:]
    if text == "-" or not text.startswith("-") or text.startswith("--"):
        return None
    cluster = text[1:]
    position = cluster.find(letter)
    if position < 0 or not _SHORT_CLUSTER.match(cluster[:position]):
        return None
    return cluster[position + 1:]


def _flag_value(args, flags):
    """(text, resolved) for the argument after `flag`, or inside `--flag=value`."""
    for index, (text, _resolved) in enumerate(args):
        if text in flags and index + 1 < len(args):
            return args[index + 1]
        for flag in flags:
            if flag.startswith("--") and text.startswith(flag + "="):
                return text[len(flag) + 1:], args[index][1]
    return None


def _in_place(text):
    """Is this `sed` argument the in-place flag? `-i`, `-i.bak`, `-ni`, `--in-place`."""
    if text.startswith("--"):
        return text == "--in-place" or text.startswith("--in-place=")
    return text.startswith("-") and "i" in text[1:].split(".")[0]


def _sed_targets(args, result, cwd):
    """`sed` writes only under `-i`. Without it every operand is a read."""
    if not any(_in_place(a[0]) for a in args):
        return
    scripted = any(a[0] in ("-e", "--expression", "-f", "--file")
                   or a[0].startswith("--expression=") or a[0].startswith("--file=")
                   for a in args)
    operands = []
    index = 0
    while index < len(args):
        text = args[index][0]
        if text in ("-e", "--expression", "-f", "--file"):
            index += 2
            continue
        if text.startswith("-"):
            index += 1
            continue
        operands.append(args[index])
        index += 1
    if not scripted:
        operands = operands[1:]                 # the first operand is the script itself
    _add_all(operands, result, cwd)


_GIT_GLOBAL_VALUED = ("-c", "--git-dir", "--work-tree", "--exec-path", "--namespace")
_CHECKOUT_NOT_A_PATH = ("-b", "-B", "--orphan", "--detach", "--track", "-t",
                        "--guess", "--no-guess")


def _git_targets(args, result, cwd):
    """`git checkout`/`restore` pathspecs and `git apply`. Branches are not writes."""
    index = 0
    while index < len(args):
        text = args[index][0]
        if text == "-C" and index + 1 < len(args):
            cwd = _new_cwd([args[index + 1]], cwd)
            index += 2
            continue
        if text in _GIT_GLOBAL_VALUED:
            index += 2
            continue
        if text.startswith("-"):
            index += 1
            continue
        break
    if index >= len(args):
        return
    subcommand = args[index][0]
    rest = args[index + 1:]

    if subcommand == "apply":
        if any(a[0] in ("--check", "--stat", "--numstat", "--summary") for a in rest):
            return
        result.unresolved = True                # the targets live inside the patch
        return

    if subcommand not in ("checkout", "restore"):
        return                                  # `switch` and everything else: no paths

    for position, argument in enumerate(rest):
        if argument[0] == "--":
            _add_all(rest[position + 1:], result, cwd)
            return

    if subcommand == "restore":
        _add_all(_operands(rest, valued=("-s", "--source")), result, cwd)
        return

    if any(a[0] in _CHECKOUT_NOT_A_PATH for a in rest):
        return
    operands = _operands(rest)
    if len(operands) >= 2:
        _add_all(operands[1:], result, cwd)     # `git checkout <tree-ish> <path>...`
        return
    if len(operands) == 1 and _looks_like_a_path(operands[0][0]):
        result.add(operands[0][0], operands[0][1], cwd)


def _looks_like_a_path(text):
    """`git checkout X` with one operand: branch or file?

    Without touching disk the only signal is shape. A dot in the last segment, or a
    leading `./`, says file; `feat/bash-write-guard` and `master` say branch. Guessing
    wrong in the branch direction misses a write, which is the direction this file is
    supposed to fail in.
    """
    cleaned = text.replace("\\", "/")
    if cleaned.startswith("./") or cleaned.startswith("../"):
        return True
    return "/" in cleaned and "." in cleaned.rsplit("/", 1)[1]


# ---------------------------------------------------------------- interpreter bodies


def _interpreter_targets(name, args, heredocs, result, cwd):
    """Inspect `-c` / `-e` bodies and heredoc-fed source. Do not flag the shape.

    356 corpus commands run an interpreter with an inline body and only 57 of them write
    anything. `python -c "import json; print(json.load(open(p)))"` is how half this
    fleet's questions get answered, and denying it would be denying `cat`.
    """
    bodies = []
    unresolved_body = False
    index = 0
    while index < len(args):
        text, resolved = args[index]
        if text in ("-c", "-e", "--eval") and index + 1 < len(args):
            bodies.append(args[index + 1][0])
            unresolved_body = unresolved_body or not args[index + 1][1]
            index += 2
            continue
        index += 1
    bodies.extend(heredocs)                     # `python - <<'PY'` and `python <<'PY'`
    if not bodies:
        return                                  # `python script.py`: not our business
    _ = name
    for body in bodies:
        targets, unresolved = _inspect_body(body)
        for target in targets:
            result.add(target, True, cwd)
        if unresolved:
            result.unresolved = True
        if unresolved_body and (targets or unresolved):
            result.unresolved = True


# Calls that write, keyed by the name at the call site. The value says where the path is:
#   "arg0" / "arg1"   that positional argument
#   "both"            arg0 and arg1 (a rename or a move)
#   "receiver"        the expression the method was called on
#
# `json.dump`, `yaml.dump`, `pickle.dump`, `f.write` and `f.writelines` are NOT here, and
# leaving them out is what took the corpus's unresolved bucket down. Every one of them
# needs a writable file OBJECT, and the only way to get one is the `open(..., "w")` this
# table already resolves. Counting them too meant `json.dump(d, open(p, "w"))` resolved
# `p` from the `open` and then reported an unresolvable write anyway, from the `dump`.
# THE RESIDUAL, on the record rather than left to be rediscovered: a handle that did NOT
# come from a literal `open()` -- `tempfile.NamedTemporaryFile("w", delete=False)`, or
# `os.fdopen(3, "w")` -- followed by a dump or a `writelines` is now ([], False) where it
# used to be unresolved-and-recorded. Contrived, and 0 commands in the corpus; it is the
# price of removing the double count.
_WRITE_CALLS = {
    "write_text": "receiver",
    "write_bytes": "receiver",
    "writeFileSync": "arg0",
    "appendFileSync": "arg0",
    "writeFile": "arg0",
    "appendFile": "arg0",
    "createWriteStream": "arg0",
    "mkdirSync": "arg0",
    "rmSync": "arg0",
    "rmdirSync": "arg0",
    "unlinkSync": "arg0",
    "renameSync": "both",
    "copyFileSync": "arg1",
    "copy": "arg1",
    "copy2": "arg1",
    "copyfile": "arg1",
    "copytree": "arg1",
    "move": "both",
    "rmtree": "arg0",
    "remove": "arg0",
    "unlink": "arg0",
    "rename": "both",
    "replace": "both",
    "makedirs": "arg0",
    "mkdir": "arg0",
    "rmdir": "arg0",
    "symlink": "arg1",
    "truncate": "arg0",
}

# `copy`, `move`, `remove`, `replace`, `dump`, `mkdir` and `truncate` are also perfectly
# ordinary names on lists, dicts, strings and regexes. Requiring the qualifier keeps
# `text.replace("a", "b")` and `queue.remove(x)` out of the write set.
_QUALIFIED_ONLY = {
    "copy": ("shutil",), "copy2": ("shutil",), "copyfile": ("shutil",),
    "copytree": ("shutil",), "move": ("shutil",), "rmtree": ("shutil",),
    "remove": ("os",), "unlink": ("os", "Path", "path"), "rename": ("os", "shutil"),
    "replace": ("os",), "makedirs": ("os",), "rmdir": ("os",),
    "symlink": ("os",), "truncate": ("os",), "mkdir": ("os",),
}

# Methods whose path is the thing they were called ON, not an argument.
_RECEIVER_WRITES = frozenset((
    "write_text", "write_bytes", "mkdir", "touch", "unlink", "rmdir", "rename",
    "replace", "open",
))

_CALL = re.compile(
    r"(?<![A-Za-z0-9_])(?P<qualifier>(?:[A-Za-z_][A-Za-z0-9_]*\s*\.\s*)*)"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
_METHOD_CALL = re.compile(r"\)\s*\.\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\(")
_BODY_ASSIGNMENT = re.compile(
    r"(?:^|[;\n])\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>[^;\n]+)")
_STRING = re.compile(r"^(?:[rbuf]{0,2})(\"[^\"]*\"|'[^']*')$")
_WRITE_MODE = re.compile(r"^[rbuf]{0,2}[\"'][rbt+]*[wax][rbt+]*[\"']$")
_PERL_WRITE_MODE = re.compile(r"^[\"']\s*\+?>{1,2}")


def _inspect_body(body):
    """(targets, unresolved) for interpreter source. A body with no write call is clean."""
    variables = _body_variables(body)
    targets = []
    unresolved = False

    for match in _CALL.finditer(body):
        name = match.group("name")
        qualifier = match.group("qualifier").replace(" ", "").strip(".")
        last = qualifier.rsplit(".", 1)[-1] if qualifier else ""

        if name == "open":
            args = _call_arguments(body, match.end() - 1)
            mode = next((a for a in args[1:] if _WRITE_MODE.match(a.strip())), None)
            perl = next((a for a in args[1:] if _PERL_WRITE_MODE.match(a.strip())), None)
            if mode is None and perl is None:
                continue                        # a read; the common case by far
            path = _literal(args[0], variables) if args else None
            if perl is not None and (path is None or path.startswith(">")):
                # Perl two-arg `open(FH, ">$out")`: the mode and the path are one string.
                path = _literal(perl, variables)
                path = path.lstrip("+>").strip() if path else None
                if path and "$" in path:
                    path = None
            if path:
                targets.append(path)
            else:
                unresolved = True
            continue

        where = _WRITE_CALLS.get(name)
        if where is None:
            continue
        allowed = _QUALIFIED_ONLY.get(name)
        if allowed is not None and last not in allowed:
            continue
        if where == "receiver":
            continue                            # a method on a path; the two passes below
        unresolved = _record(body, match, where, variables, targets) or unresolved

    # `Path("x").write_text(...)` and `Path(p).mkdir(...)` -- the path is the RECEIVER,
    # so the call regex above cannot see it and the text before the dot is read instead.
    for match in _METHOD_CALL.finditer(body):
        name = match.group("name")
        if name not in _RECEIVER_WRITES:
            continue
        if name == "open" and not any(
                _WRITE_MODE.match(a.strip())
                for a in _call_arguments(body, match.end() - 1)):
            continue
        unresolved = _add_receiver(body, match.start() + 1, variables, targets) or unresolved

    # The same thing where the receiver is a plain name: `out.write_text(...)`.
    for match in re.finditer(
            r"(?<![A-Za-z0-9_)\]])([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*"
            r"(?:write_text|write_bytes)\s*\(", body):
        unresolved = _add_receiver(body, match.end(1), variables, targets) or unresolved

    ordered = []
    for target in targets:
        if target and target not in ordered:
            ordered.append(target)
    return ordered, unresolved


def _add_receiver(body, end, variables, targets):
    """Append the receiver path ending at `end`; True when it is a runtime value."""
    receiver = _receiver_literal(body[:end], variables)
    if not receiver:
        return True
    targets.append(receiver)
    return False


def _record(body, match, where, variables, targets):
    """Append what `where` points at; return True if it could not be pinned down."""
    if where == "none":
        return True
    args = _call_arguments(body, match.end() - 1)
    wanted = {"arg0": [0], "arg1": [1], "both": [0, 1]}[where]
    unresolved = False
    for position in wanted:
        if position >= len(args):
            unresolved = True
            continue
        path = _literal(args[position], variables)
        if path:
            targets.append(path)
        else:
            unresolved = True
    return unresolved


def _call_arguments(body, open_paren):
    """Top-level argument strings of the call whose `(` is at `open_paren`."""
    depth = 0
    quote = ""
    args = []
    current = []
    index = open_paren
    while index < len(body):
        char = body[index]
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in "\"'":
            quote = char
            current.append(char)
            index += 1
            continue
        if char in "([{":
            depth += 1
            if depth == 1:
                index += 1
                continue
        elif char in ")]}":
            depth -= 1
            if depth == 0:
                args.append("".join(current))
                return [a.strip() for a in args]
        elif char == "," and depth == 1:
            args.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    args.append("".join(current))
    return [a.strip() for a in args]


def _body_variables(body):
    """`name = "literal"` inside the body, so `p = "x/y"; open(p, "w")` resolves."""
    variables = {}
    for match in _BODY_ASSIGNMENT.finditer(body):
        value = match.group("value").strip()
        literal = _STRING.match(value)
        if literal:
            variables[match.group("name")] = literal.group(1)[1:-1]
            continue
        path_call = re.match(r"^Path\s*\(\s*(\"[^\"]*\"|'[^']*')\s*\)$", value)
        if path_call:
            variables[match.group("name")] = path_call.group(1)[1:-1]
    return variables


def _literal(argument, variables):
    """The path an argument names, or None when it is a runtime value."""
    if not argument:
        return None
    argument = argument.strip()
    match = _STRING.match(argument)
    if match:
        text = match.group(1)[1:-1]
        if argument[:1] == "f" and ("{" in text):
            return None                         # an f-string is a runtime value
        return text or None
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", argument):
        return variables.get(argument)
    path_call = re.match(r"^Path\s*\(\s*(\"[^\"]*\"|'[^']*')\s*\)$", argument)
    if path_call:
        return path_call.group(1)[1:-1]
    join_call = re.match(r"^(?:os\.path\.join|posixpath\.join|path\.join)\s*\((.*)\)$",
                         argument, re.DOTALL)
    if join_call:
        parts = []
        for piece in _split_join_arguments(join_call.group(1)):
            resolved = _literal(piece, variables)
            if not resolved:
                return None
            parts.append(resolved.strip("/"))
        return "/".join(parts) if parts else None
    return None


def _split_join_arguments(text):
    depth = 0
    quote = ""
    parts = []
    current = []
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            continue
        if char in "\"'":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def _receiver_literal(prefix, variables):
    """The path in `Path("x").write_text(...)` or `p.write_text(...)`, if it is one."""
    prefix = prefix.rstrip()
    if prefix.endswith(")"):
        depth = 0
        index = len(prefix) - 1
        while index >= 0:
            if prefix[index] == ")":
                depth += 1
            elif prefix[index] == "(":
                depth -= 1
                if depth == 0:
                    break
            index -= 1
        called = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*$", prefix[:index])
        inner = prefix[index + 1:-1].strip()
        if called and called.group(1) in ("Path", "PurePath", "PosixPath",
                                          "WindowsPath"):
            return _literal(inner, variables)
        return None
    match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)$", prefix)
    if match:
        return variables.get(match.group(1))
    return None
