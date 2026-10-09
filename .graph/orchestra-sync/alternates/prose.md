@@@ alt architect-ui-planning pin=9308799d9c60
@@@ end
@@@ alt architect-invariant pin=0ce06c69c790
@@@ end
@@@ alt architect-rlm-ref pin=e2cbf5e11ff6
  the scout's to reduce, not yours to skim.
@@@ end
@@@ alt builder-board-name pin=3b319d3b1371
     followed the hooks/scope guard — a human reading the board wants a headline, not an
@@@ end
@@@ alt builder-umbrella-bullets pin=7960de872beb
@@@ end
@@@ alt builder-attribution pin=74b0c1b7ba9c
@@@ end
@@@ alt integrator-rlm-ref pin=17c015adadb3
  single reviewer could see, and a summary of the two sides is exactly where it hides.
@@@ end
@@@ alt integrator-attribution pin=3bc7322adaa6
@@@ end
@@@ alt ops-one-app pin=aa7cc82843d6
@@@ end
@@@ alt ops-attribution pin=06c5dc2263ec
@@@ end
@@@ alt ops-native-intro pin=2fde3ab1a18b
This section applies to a native mobile (Expo) or desktop (Tauri) app. One pipeline per app;
secrets live in the app's own repo's CI secret store.
@@@ end
@@@ alt reviewer-invariant pin=50ba2393ac7c
@@@ end
@@@ alt reviewer-ui-checklists pin=670e56bc5a59
@@@ end
@@@ alt reviewer-rlm-ref pin=45dde42f2de6
too large to read, that is a finding about the slice, not a reason to skim it.
@@@ end
@@@ alt scout-registry pin=014b7d49016d
1. Identify which app this task belongs to (the project you are working in). If it belongs to none, say so — do not guess.
@@@ end
@@@ alt scout-example-stack pin=780859cb9ef4
confirming that the project is TypeScript is a call not spent finding the migration that
@@@ end
@@@ alt fg-desc pin=bfb3e0f208ed
description: Run a task through the work graph — scout, architect, human gate, then either a single loop or a parallel diamond of builders and independent reviewers converging on one integrator. Use when starting any non-trivial piece of work on an app. Also use when asked to "run the graph" or "fan this out".
@@@ end
@@@ alt fg-launch pin=cc01b5e8d752
Run this from your project root. The fleet's files live under `@FLEET@/`.
@@@ end
@@@ alt fg-collector-anecdote pin=66a77c66fbf0
this every run — never carry it over from a previous one.
@@@ end
@@@ alt fg-repos-not-a-repo pin=9a2ea22436c7
A run whose target is any directory that is not itself a repo is always in degraded mode.
@@@ end
@@@ alt fg-app-registry pin=9c15c5f4b63f
Fill `run_id`, `goal` (the user's own words), and `app` (the project's name).
@@@ end
@@@ alt fg-s2-anecdote pin=6fe0a31bd1da
@@@ end
@@@ alt fg-merge-history pin=a1fcd089fe25
**Then merge it — this step is yours.** A single-loop run still leaves a branch behind. On `PASS`, and only on `PASS`,
the orchestrator merges the one reviewed branch itself.
@@@ end
@@@ alt fg-risk-anecdote pin=8bb86f767dec
self-report, re-walk by hand what the test cannot check. `risk: low` gets a lighter
@@@ end
@@@ alt fg-close-anecdote pin=b0fb6b3b199c
@@@ end
@@@ alt fg-audit-fleet pin=f54e9de2a349
@@@ end
@@@ alt cr-intro-anecdote pin=dc8ca1337acb
this fleet can most easily get wrong: the close is where attention is lowest and the record is most likely to be wrong, so it gets a script.
@@@ end
@@@ alt cr-parked-anecdote pin=81bb76928f37
`parked` or `blocked` is the honest status.
@@@ end
@@@ alt cr-recheck pin=724c269a03d0
To re-examine a run that is already closed — checking whether an old run
would pass today — use `--recheck`.
@@@ end
@@@ alt rlm-desc pin=5a4bd7805f39
description: Read an input too large to hold in context — a long file, a run's activity.jsonl, a big log — as a Recursive Language Model, by loading it into a REPL and mapping cheap haiku sub-calls over pieces of it, instead of reading it whole. Use when a scout or audit would otherwise read more than ~50KB, or when asked to "RLM this", "map over this file" or "read this without loading it".
@@@ end
@@@ alt rlm-never-refs pin=d100fc11ec19
  done through haiku summaries is a laundered review.
- **From a hook.** A sub-call is a network call.
@@@ end
@@@ alt rlm-live-run pin=579fc2838ac8
a fact.** Sub-models add items the source never had; one `grep` against `context` catches
@@@ end
@@@ alt graph-portfolio pin=e7f050738012
This file describes the work graph: the subagents that run one task. Section numbers start at 2
because other files cite them by number.

@@@ end
@@@ alt graph-agents-path pin=f702ac208e23
Nodes are **subagents** in `graph_agents/.claude/agents/`. A new work graph is generated for each
@@@ end
@@@ alt graph-degraded-repos pin=9a1eec81c957
Force **`single-loop`**, or make the target its own repo first. Full
pre-flight: `feature-graph` step 0.5.
@@@ end
@@@ alt graph-state-path pin=10e7c836c62c
graph_agents/.graph/runs/<run-id>/state.json      # relative to the project root
@@@ end
@@@ alt graph-activity-render pin=fc9ba5c7a9f0
name. It is also the evidence base for four things
@@@ end
@@@ alt graph-activity-gap pin=ef0d4a78af29
@@@ end
@@@ alt graph-board-gaps pin=238bfdd5c8d1
and never the human.
@@@ end
@@@ alt graph-board-fleetview pin=4a00a0862fcb
board).
@@@ end
@@@ alt graph-commit-attribution pin=f8ebdd4f3cac
@@@ end
@@@ alt graph-builder-footnote pin=0e6802b90192
builder. `builder.md`'s frontmatter says the same thing in the same words.
@@@ end
@@@ alt graph-architect-example pin=1a25205c60cc
- **`architect`** — it decides the shape, and shape errors are the expensive ones. A plan
  built on a wrong reading of the data ships broken.
@@@ end
@@@ alt graph-cache-anecdote pin=8287c1527955
@@@ end
@@@ alt graph-rlm-inputs pin=a763bb99425f
The same rule also applies *inside* a node. When a scout must read
an input too large to hold — a diamond's `activity.jsonl`
@@@ end
@@@ alt graph-rlm-fence pin=10bac8bb1d68
                                          no tools, no settings, cwd outside the project
@@@ end
@@@ alt graph-rlm-decision pin=84c943817a79
The scope and the measurements behind each default are in the `rlm.py` docstring.
@@@ end
