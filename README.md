<h1 align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo-dark.svg">
    <img src="docs/assets/logo-light.svg" alt="graph_agents" height="72">
  </picture>
</h1>

<p align="center">
  <i>Turn a feature request into a scouted, planned, human-approved, built and independently reviewed change, without the orchestrator writing a line of code itself.</i>
</p>

<h4 align="center">
  <a href="https://github.com/njcurtis3/graph_agents/releases/latest">
    <img src="https://img.shields.io/github/v/release/njcurtis3/graph_agents?style=flat-square&color=d9731a" alt="latest release" style="height: 20px;">
  </a>
  <a href="https://claude.com/claude-code">
    <img src="https://img.shields.io/badge/Claude_Code-2.1-17181c.svg?style=flat-square" alt="Claude Code 2.1" style="height: 20px;">
  </a>
  <img src="https://img.shields.io/badge/python-3%20stdlib-8f8c84.svg?style=flat-square&logo=python&logoColor=white" alt="Python 3, stdlib only" style="height: 20px;">
  <img src="https://img.shields.io/badge/status-v1-c9a227.svg?style=flat-square" alt="status: v1" style="height: 20px;">
</h4>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#setup">Setup</a> ·
  <a href="GRAPH.md">Graph spec</a> ·
  <a href="CLAUDE.md">Constitution</a> ·
  <a href="CURRENT-STATE.md">Current state</a> ·
  <a href="decisions/">Decisions</a> ·
  <a href="https://github.com/njcurtis3/graph_agents/releases">Releases</a>
</p>

```
   scout  →  architect  →  ⛔ HUMAN GATE  →  builder(s)  →  reviewer(s)  →  integrator
  (facts)     (plan +                        (implement     (adversarial,   (fan-in,
              shape)                          one slice)     can REJECT)     if diamond)
```

## Introduction

`graph_agents` is an agent fleet for [Claude Code](https://claude.com/claude-code). It
runs every non-trivial change through the same structure. Facts are established before
anyone plans. You approve the plan before any code exists: its shape, its slices, and the
explicit "not doing" list. A reviewer that never saw the code being written can reject it
twice before you are pulled back in. A run is called done only when git confirms the
merge, not on the strength of a state file that only knows what it was told.

Letting an agent write code unsupervised means trusting a diff you didn't watch get
written. Reviewing every change by hand doesn't scale past the first app. This is the
third option.

It is **tooling, not a product**. It operates *on* a portfolio of standalone apps that
live beside it, each with its own git repo, deploys and lifecycle, and it ships inside
none of them.

> [!WARNING]
> **v1 covers the fleet as it has actually been exercised.** Five of the six nodes have
> run on real work, including two full diamonds. **`ops` has never executed.** The fleet
> has been run on one machine (Windows 11), and changes to its agent or skill files take
> effect only in a fresh Claude Code session. `CURRENT-STATE.md` separates what has been
> exercised from what is still a documented gap, and it is verified against disk rather
> than written aspirationally.

> [!NOTE]
> graph_agents is an independent project. It is not part of, or endorsed by, Anthropic.

<details open>
<summary>
 Features
</summary> <br />

<table>
  <tr>
    <td width="50%"><b>The work graph</b><br><code>scout</code> returns verified <code>file:line</code> facts. <code>architect</code> turns them into a plan <i>and</i> a shape: a <b>single loop</b>, or a <b>diamond</b> of parallel builders in linked git worktrees when 3+ slices are genuinely disjoint. <code>builder</code> implements exactly one slice and never reviews its own work.</td>
    <td width="50%"><b>Independent review</b><br><code>reviewer</code> runs in a fresh context that never saw the code being written, re-derives every check itself, and can REJECT, at most twice per slice before the run escalates. <code>integrator</code> is the one merge point and proves the <i>whole</i> is coherent, catching the cross-slice conflict no single reviewer could see.</td>
  </tr>
  <tr>
    <td><b>The human gate</b><br>The shape, the slices, the file-level edges and the "not doing" list are shown before any code is written. Nothing proceeds without approval, and a second gate sits in front of <code>ops</code>, which never runs automatically.</td>
    <td><b>Shared state, not shared context</b><br>One <code>state.json</code> per run is the only wire between agents. Each node owns one key and is stamped <code>written_by</code>, and <code>verify-state.py --audit</code> checks that the edges actually held.</td>
  </tr>
  <tr>
    <td><b>Guardrails that block</b><br>A scope guard denies a builder's <code>Write</code>/<code>Edit</code>/<code>Bash</code> outside the file set you approved. A commit guard denies AI co-author trailers and non-owner authors on every agent, the orchestrator included. Both fail <b>closed</b>.</td>
    <td><b>Model tiering</b><br>Retrieval runs cheap and judgment does not. <code>scout</code> is on haiku and <code>builder</code> on sonnet, because the judgment already happened at the gate. <code>reviewer</code> and <code>architect</code> are never downgraded: a verifier that misses the bug is worse than none.</td>
  </tr>
  <tr>
    <td><b>The board</b><br>A heartbeat logs every node event to <code>activity.jsonl</code>, and a run board appears in the main tab the moment a node is dispatched. It is derived, never authored, so it cannot drift from the run.</td>
    <td><b>Verified, not asserted</b><br><code>close-run</code>, <code>audit-fleet</code> and <code>postmortem</code> are read-only checkers. They report, and you act. The fleet's claims about itself are checked against disk and git, not trusted because they were once written down.</td>
  </tr>
  <tr>
    <td colspan="2"><b>Recursive reading (RLM)</b><br>For inputs too large to hold in context, <code>.graph/rlm.py</code> implements a <a href="https://arxiv.org/abs/2512.24601">Recursive Language Model</a>. The input sits in a REPL variable, the node peeks, greps and chunks it in code, and haiku sub-calls read the pieces four at a time under a dollar budget enforced <i>before</i> each call. <code>scout</code>, <code>postmortem</code> and <code>audit-fleet</code> use it. <code>reviewer</code>, <code>architect</code> and <code>integrator</code> never do, because reading through a cheaper model would downgrade exactly the nodes that must not be (<a href="decisions/0002-rlm-scope.md">ADR 0002</a>).</td>
  </tr>
</table>

</details>

<details>
<summary>
 Routers: seven skills, each one thing
</summary> <br />

| Router | What it does |
|---|---|
| `feature-graph` | The main one. Turns a goal into a scout → architect → gate → single-loop-or-diamond run. |
| `new-app` | Scaffolds a new standalone app under the umbrella, with its own repo and `CLAUDE.md`, registered in the portfolio index. |
| `fleetview` | Launches the read-only viewer for run state. |
| `close-run` | Checks whether a run may be marked done: audit clean, gate passed, every slice built and reviewed `PASS`, and the work actually merged in **git**. |
| `audit-fleet` | Re-verifies `CURRENT-STATE.md` against disk and reports only drift. |
| `postmortem` | Reviews a finished run for what its shape actually cost and caught: tool counts, diamond concurrency, slice round-trips, risk-tag fit. |
| `rlm` | Reads an input too large for context as a Recursive Language Model: code to slice it, haiku sub-calls to read the slices, a hard budget on both. |

Every one is thin. The logic lives in a tested `.graph/` script, and the `SKILL.md` routes
to it.

</details>

## Install

<details open>
<summary>
 Clone beside your apps
</summary> <br />

graph_agents lives *inside* an umbrella directory that also holds your apps. The umbrella
itself is deliberately not a git repo, and you launch Claude Code from it, never from inside
`graph_agents/`, because every path in the fleet is relative to the umbrella.

```bash
cd ~/code/umbrella                     # the directory that holds your apps
git clone https://github.com/njcurtis3/graph_agents
```

Then expose the fleet's `.claude/` at the umbrella root so Claude Code discovers the agents,
skills and hooks. It is a link, not a copy, so there is nothing to keep in sync:

```bash
ln -s graph_agents/.claude .claude                       # macOS / Linux
cmd /c mklink /J .claude graph_agents\.claude            # Windows (directory junction)
```

To update, `git pull` inside `graph_agents/` and start a fresh Claude Code session.

</details>

<details>
<summary>
 Write your portfolio index
</summary> <br />

`portfolio/registry.json` is **not in this repo, on purpose**: it lists real local
directory paths. The fleet reads it as the first step of every run to decide which app a
task belongs to, so a fresh clone cannot route anything until you write one. It is a JSON
object whose `apps` array holds one entry per app:

```json
{
  "apps": [
    {
      "id": "my-app",
      "kind": "product",
      "path": "my-app",
      "status": "active",
      "one_liner": "What it is, in one line",
      "stack": ["typescript", "next"],
      "ui": "responsive-web",
      "entry_docs": ["CLAUDE.md", "README.md"],
      "owns": ["what this app is the authority on"]
    }
  ]
}
```

`kind` is one of `product`, `site`, `tool` or `vendor`. `path` is the sibling directory
name. `ui` decides whether [mobile-first](conventions/mobile-first.md) applies.

</details>

## Setup

The fleet's hooks are registered in `.claude/settings.json` and run on their own once the
link above exists. Each one is stdlib Python and makes no network call:

| Hook | When | What it does |
|---|---|---|
| `guard-builder-scope` | before `Write`/`Edit`/`Bash` | denies a builder's write outside the file set approved at the gate |
| `guard-commit-trailers` | before `Bash` | denies a `git commit` carrying AI attribution or a non-owner author |
| `flag-stale-state` | after `Write`/`Edit` | says when a fleet definition changed and `CURRENT-STATE.md` is now stale |
| `flag-cross-app-import` | after `Write`/`Edit` | flags an app importing or reading another app |
| `flag-state-gap` | after `Write`/`Edit` of a `state.json` | audits the run's edge ordering and authorship |
| `record-activity` | every tool call, subagent start and stop | appends the heartbeat to the run's `activity.jsonl` |
| `show-board` | after an `Agent` spawn | prints the run board into the main tab |

Then, from the umbrella:

```bash
/feature-graph      # run a task through the graph
/new-app            # bootstrap a new standalone app under the portfolio
/fleetview          # open the run viewer
/close-run          # check whether the open run may be marked done
/audit-fleet        # re-verify CURRENT-STATE.md against disk
/postmortem         # review a finished run's shape and cost
/rlm                # read a file too large for context, by recursive sub-calls
```

<details>
<summary>
 Seeing a run
</summary> <br />

Run state is JSON on disk, and you can read it as JSON. To look at it instead, use
**FleetView**, a separate standalone app with its own repo:

```bash
python fleetview/serve.py        # from the umbrella root
```

It renders each run's work graph, the portfolio graph, and the node roster read live from
agent frontmatter. It is a viewer: read-only, and it never writes to a run. This repo does
not depend on it. FleetView reads the run-state format as a convention rather than an
import, so this fleet works without it.

</details>

<details>
<summary>
 The one invariant
</summary> <br />

> **No app may import, build against, or read files from another app.**

If two apps need the same thing, the pattern is copy, don't couple. A shared package turns
N standalone products into one distributed monolith you cannot sell, kill or hand off
separately. Only conventions, one-time-copy templates, and this fleet may cross app
boundaries. `flag-cross-app-import` and `.graph/verify-invariant.py` check it.

</details>

<details>
<summary>
 Layout
</summary> <br />

```
graph_agents/
  CLAUDE.md                the constitution: the invariant, restated
  GRAPH.md                 the graph spec: nodes, edges, shared state, human gates
  CURRENT-STATE.md         a disk-verified snapshot: what's live, what's still a gap
  HISTORY.md               what happened: per-run narratives and the changelog
  conventions/             cross-app "how we build" prose, read and copied, never imported
  decisions/               numbered decision records: settled questions, and what would reopen them
  portfolio/registry.json  the index over the app portfolio (not tracked; see Install)
  .claude/
    agents/                the six node definitions
    skills/                the seven routers
    hooks/                 the guardrails, the heartbeat and the board
  .graph/
    runs/<run-id>/         one state.json and activity.jsonl per unit of work
    verify-state.py        checks a node actually wrote its result, and the edges held
    close-run.py           checks whether a run may be closed
    audit-fleet.py         checks CURRENT-STATE.md against disk
    postmortem.py          reviews a finished run's shape and cost
    rlm.py                 the Recursive Language Model REPL behind /rlm
```

</details>

<details>
<summary>
 Supported versions
</summary> <br />

| | Tested with | Needs |
|---|---|---|
| Claude Code | 2.1.291 | subagents, skills, `PreToolUse`/`PostToolUse`/`SubagentStart`/`SubagentStop` hooks; `claude -p` on your PATH for `/rlm` |
| Python | 3.13.5 | 3.x as `python`, standard library only |
| git | 2.51 | worktrees, for diamond runs |
| OS | Windows 11 | the hooks are cross-platform Python; macOS and Linux are untried |

</details>

## Documentation

- [Constitution](CLAUDE.md): the one invariant, commit ownership, launch and read-order rules
- [Graph spec](GRAPH.md): both graphs, the stop rule, shared state, the node roster, model
  tiering, recursive reading, human gates
- [Current state](CURRENT-STATE.md): what is live and exercised, and every known gap,
  verified against disk
- [History](HISTORY.md): what each run did, and the changelog
- [Decisions](decisions/): [0001: no Jev in the fleet](decisions/0001-no-jev-in-the-fleet.md),
  [0002: RLM scope](decisions/0002-rlm-scope.md)
- [Conventions](conventions/): [mobile-first](conventions/mobile-first.md)
