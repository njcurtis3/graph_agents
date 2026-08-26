---
name: fleetview
description: Launch FleetView, the local viewer for run state — every run's work graph, the node roster, and the portfolio graph, rendered from disk. Use when asked to "show", "visualize", "look at" or "open" a run, the graph, or the fleet, or when a human wants to see what a run did rather than read JSON.
---

# fleetview

FleetView is a **separate standalone app** (`fleetview/`, its own repo). It is not part of
the fleet and the fleet does not depend on it. This skill only launches it.

## Run it

```bash
python fleetview/serve.py
```

From `repos/`, that is all — FleetView auto-detects `./graph_agents` as the fleet. It opens
a browser at `http://127.0.0.1:8787/`. Add `--port N` if that port is taken, `--no-open` to
skip the browser, `--fleet <path>` to read a different fleet.

It is a long-running server. Start it in the background and hand the user the URL; do not
block on it.

## If `fleetview/` is not there

It is an independent repo and may simply be absent. Say so and stop — do not recreate it,
do not vendor a copy into `graph_agents/`, and do not fall back to hand-rendering a graph
in the terminal. Run state is readable JSON; point the user at
`graph_agents/.graph/runs/<run-id>/state.json` instead.

## What it is for

Reading a finished or in-flight run as a picture instead of as JSON: the shape the
architect chose, which slices passed, which got rejected and looped, what each node
actually wrote into `state.json`. Also the node roster with live model tiers, and the
portfolio graph.

**It is read-only.** It cannot approve a gate, resume a run, or change state. If a run
looks wrong in FleetView, the state is wrong — fix `state.json`.

## Before a screenshot

Tell the user about the **Anonymize** toggle in the header. `portfolio/registry.json` names
real local directories; Anonymize relabels apps as App 1..N and hides one-liners and stack
tags everywhere they appear.

## The boundary

FleetView reads the run-state *format* — `.graph/runs/<run-id>/state.json`,
`.claude/agents/*.md` frontmatter, `portfolio/registry.json` — as a convention, which is
one of the three things allowed to cross an app boundary. Keep it that way:

- Never make the fleet import from `fleetview/`, or a fleet file read one.
- Never move FleetView's files back under `graph_agents/`.
- If the state format changes, the fleet is the authority; FleetView follows. It is a
  viewer, so a field it does not know about is invisible, not an error.
