#!/usr/bin/env python
"""Measure `bash_write_targets.classify` against every Bash command this fleet has run.

    python graph_agents/.claude/hooks/measure_bash_corpus.py
    python graph_agents/.claude/hooks/measure_bash_corpus.py --transcripts DIR

WHY THIS EXISTS. `test_bash_write_targets.py` proves the classifier catches the cases
someone thought to write down. It cannot prove the mechanism list is COMPLETE, and it
cannot say what the guard built on top of this will actually do to real work. Only the
corpus can, so the corpus gets measured rather than assumed -- the same way the design
decision this slice implements was measured rather than argued.

Three buckets, over the unique commands:

    clean                     no write signature, or a write signature with nothing to
                              write. The guard reads no state and denies nothing.
    resolved write            at least one concrete target, all of them pinned down. The
                              guard judges these on their target.
    unresolved write shape    something writes and the target could not be resolved. The
                              guard ALLOWS these and records a warning; the design's
                              stated fail-open direction. Budget: 3% or lower.

A command counts as unresolved if ANY part of it was unresolvable, even when other parts
resolved. That ordering is deliberate: the bucket is "things the guard cannot fully
judge", and rounding those into "resolved" would flatter the number.

WHAT THIS PRINTS, AND WHAT IT WILL NOT PRINT

  The transcripts are the owner's own session logs. They contain absolute paths under the
  owner's home directory and may contain secrets that have passed through a command line.
  The owner approved reading them for this measurement, read-only, and that approval does
  not extend to copying their contents anywhere.

  So this tool prints COUNTS, RATES and SHAPE LABELS. It prints no command text, no path,
  and no fragment of either -- there is nothing here to redact because nothing from a
  transcript is ever put on stdout. The shape labels below are computed by this file, not
  lifted from the data, and they are what a reviewer reads to answer the one question the
  bucket count cannot: is the unresolved bucket variable-and-substitution noise, or is it
  a mechanism nobody implemented?

  The labels are this tool's own reading of why a command landed in the bucket, not the
  classifier's. Only the bucket counts are authoritative.

Exit 0 when the corpus was found and measured, 1 when it was not. A measurement tool that
measured nothing must not report success.
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import bash_write_targets                                      # noqa: E402
from bash_write_targets import classify, has_write_signature   # noqa: E402

HERE = os.path.dirname(os.path.realpath(__file__))
FLEET = os.path.normpath(os.path.join(HERE, "..", ".."))
UMBRELLA = os.path.dirname(FLEET)

# The unresolved-bucket budget the plan set, so the tool says PASS or OVER itself rather
# than leaving a human to divide two numbers.
BUDGET = 0.03


def default_transcripts():
    """Claude Code's own project directory for the umbrella, derived not hardcoded."""
    encoded = re.sub(r"[:\\/]", "-", UMBRELLA)
    return os.path.join(os.path.expanduser("~"), ".claude", "projects", encoded)


def bash_commands(directory):
    """Every Bash `tool_use` command string in every transcript, in file order."""
    for path in sorted(glob.glob(os.path.join(directory, "*.jsonl"))):
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                message = record.get("message")
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use" or block.get("name") != "Bash":
                        continue
                    command = (block.get("input") or {}).get("command")
                    if isinstance(command, str) and command:
                        yield command


# Why did this land in the unresolved bucket? Shape labels only -- see the docstring.
_SHAPES = (
    (re.compile(r"\bxargs\b"), "xargs: the operands arrive on stdin"),
    (re.compile(r"\b(?:curl|wget)\b[^|;&\n]{0,200}?\s-{1,2}[A-Za-z-]*O"),
     "curl -O / wget: the filename comes from the remote resource"),
    (re.compile(r"\$\(|`"), "a $(...) or backtick substitution"),
    (re.compile(r"\bgit\b[^|;&\n]{0,60}\bapply\b"), "git apply (targets live in the patch)"),
    (re.compile(r"\bcd\s+[^\s;&|]*\$"), "a relative target under an unresolvable cd"),
    (re.compile(r"\$\{?[A-Za-z_]"), "a shell variable never assigned in this command"),
    (re.compile(r"\b(?:python|python3|py|node|perl|ruby)\b[^|;&\n]{0,200}?\s-[ce]\b"),
     "an interpreter body whose path is a runtime value"),
    (re.compile(r"<<"), "a heredoc-fed interpreter whose path is a runtime value"),
)

_VERBS = frozenset(("tee", "install", "dd", "truncate", "mv", "cp", "rm", "rmdir",
                    "touch", "mkdir", "ln", "sed", "git", "curl", "wget"))
_INTERPRETERS = frozenset(("python", "python3", "py", "node", "nodejs", "perl", "ruby",
                           "sh", "bash", "zsh", "dash"))


def label(command, table, fallback):
    for pattern, name in table:
        if pattern.search(command):
            return name
    return fallback


def mechanisms(command):
    """Which write mechanisms a command uses, read through the classifier's OWN lexer.

    A regex sweep over the raw string was tried first and it lied: it reported `ln` for
    25 commands that never ran `ln`, because the letters sat inside a heredoc paragraph.
    So the labels come from the same tokenizer the classifier uses -- one lexer, one
    answer. It still assigns no paths and matches nothing against a file set; the
    classifier owns that and this file has no opinion.

    A command can use several mechanisms, so these counts sum to more than the bucket.
    """
    found = set()
    text, bodies = bash_write_targets._strip_heredocs(command)
    heredoc = bool(bodies)
    for segment, _separator in bash_write_targets._segments(
            bash_write_targets._tokenize(text)):
        words = []
        redirect = False
        for kind, value in segment:
            if kind == "op" and value in bash_write_targets._WRITE_REDIRECTS:
                redirect = True
            elif kind == "word":
                words.append(bash_write_targets._expand(value, {})[0])
        while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
            words.pop(0)
        if redirect:
            found.add("heredoc to a file" if heredoc else "redirect")
        if not words:
            continue
        name = os.path.basename(words[0].replace("\\", "/"))
        if name in _VERBS:
            if name == "sed":
                found.add("sed -i")
            elif name == "git":
                found.add("git checkout/restore/apply")
            else:
                found.add(name)
        elif name in _INTERPRETERS:
            found.add("interpreter body")
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--transcripts", default=default_transcripts(),
                        help="directory of Claude Code .jsonl transcripts")
    options = parser.parse_args()

    # Neither failure path below names the directory. It is this tool's own argument
    # rather than corpus content, but it is an absolute path under the owner's home and
    # it is the ONLY owner-identifying string this tool could ever emit -- and a failed
    # run is exactly the output that gets pasted into a report. A basename would not help:
    # the default directory's basename is the owner's home path with the slashes swapped.
    if not os.path.isdir(options.transcripts):
        print("no transcript directory at the path given; nothing measured")
        print("pass --transcripts DIR")
        return 1

    total = 0
    unique = set()
    for command in bash_commands(options.transcripts):
        total += 1
        unique.add(command)
    if not unique:
        print("no Bash commands in the %d transcript files found there"
              % len(glob.glob(os.path.join(options.transcripts, "*.jsonl"))))
        return 1

    buckets = collections.Counter()
    shapes = collections.Counter()
    used = collections.Counter()
    prefiltered = 0
    both = 0
    target_count = 0
    unsound = 0

    for command in sorted(unique):
        signature = has_write_signature(command)
        if signature:
            prefiltered += 1
        targets, unresolved = classify(command)
        if not signature:
            # The pre-filter's ONE hard requirement: it may cost a wasted state.json
            # read, it may never hide a write. Ask the parser directly, past the
            # short-circuit `classify` does, and count every disagreement.
            try:
                if bash_write_targets._walk(command, "", {}, 0) != ([], False):
                    unsound += 1
            except Exception:
                unsound += 1
        if unresolved:
            buckets["unresolved"] += 1
            shapes[label(command, _SHAPES, "no shape matched -- READ THIS ONE")] += 1
            if targets:
                both += 1
        elif targets:
            buckets["resolved"] += 1
            target_count += len(targets)
        else:
            buckets["clean"] += 1
        if targets or unresolved:
            used.update(mechanisms(command))

    count = len(unique)
    print("corpus: %d Bash calls, %d unique commands, %d transcripts"
          % (total, count, len(glob.glob(os.path.join(options.transcripts, "*.jsonl")))))
    print()
    print("  clean                   %5d  %5.1f%%" % (buckets["clean"],
                                                      100.0 * buckets["clean"] / count))
    print("  resolved write          %5d  %5.1f%%" % (buckets["resolved"],
                                                      100.0 * buckets["resolved"] / count))
    print("  unresolved write shape  %5d  %5.1f%%" % (buckets["unresolved"],
                                                      100.0 * buckets["unresolved"] / count))
    print("  %s%d = %d" % ("-" * 22 + "  ", count,
                           buckets["clean"] + buckets["resolved"] + buckets["unresolved"]))
    print()
    print("pre-filter passes %d of %d (%.1f%%); the other %d pay no disk I/O at all"
          % (prefiltered, count, 100.0 * prefiltered / count, count - prefiltered))
    print("pre-filter soundness: %d commands the parser calls a write and the pre-filter "
          "does not (must be 0)" % unsound)
    print("resolved bucket names %d target paths" % target_count)
    print("%d unresolved commands ALSO resolved at least one target" % both)
    print()

    rate = float(buckets["unresolved"]) / count
    print("unresolved budget: %.2f%% measured against %.0f%% allowed -- %s"
          % (100.0 * rate, 100.0 * BUDGET, "WITHIN" if rate <= BUDGET else "OVER"))
    print()

    print("why the unresolved bucket is unresolved (shape labels, no command text):")
    for name, hits in shapes.most_common():
        print("  %5d  %s" % (hits, name))
    print()
    # PRESENCE, not attribution. `git checkout -b x && echo y > z` lands here as both
    # `git` and `redirect` although only the redirect produced a target; separating the
    # two would mean re-deciding in this file what the classifier already decided.
    print("write mechanisms PRESENT in the %d write commands (several per command; "
          "presence is not attribution):"
          % (buckets["resolved"] + buckets["unresolved"]))
    for name, hits in used.most_common():
        print("  %5d  %s" % (hits, name))
    return 0 if unsound == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
