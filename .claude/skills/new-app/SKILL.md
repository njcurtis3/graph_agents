---
name: new-app
description: Bootstrap a new standalone application under the holding-company umbrella — its own git repo, its own CLAUDE.md, registered in the portfolio index, with zero coupling to sibling apps. Use when starting a new app, product, or site under the umbrella.
---

# new-app

A new app is a long-term maintenance commitment, not a folder. Treat it that way.

## Step 1 — HUMAN GATE ⛔

Before creating anything, get explicit answers and confirm them back:

1. **id** — kebab-case, becomes the directory and repo name
2. **one_liner** — what it does, one sentence. If this is hard to write, the app is not ready to exist.
3. **kind** — `product` | `site` | `tool` | `vendor`
4. **stack** — language and framework
5. **Why is this not a feature of an existing app?** If there is no clean answer, it probably is one. Say so.
6. **ui** — `responsive-web` | `native-mobile` | `native-desktop` | `desktop-only` | `none`.
   One-line test: does a human reach this on a device they choose, in a browser? If yes it
   is `responsive-web`. An installed iOS/Android app is `native-mobile` (Expo, built on
   EAS); an installed Windows/macOS/Linux app is `native-desktop` (Tauri 2). `desktop-only`
   is only a local-only dev/inspection viewer bound to `127.0.0.1` — no installable binary.
   CLIs, libraries and pipelines are `none`. One repo shipping several surfaces takes an
   array, e.g. `["responsive-web", "native-mobile"]`. Expo + Tauri together is **two apps**
   unless it is genuinely one product on one release cadence; if unsure, split it.
   See `graph_agents/decisions/0003-native-stack.md`.

Do not create anything until they confirm.

## Step 2 — create it standalone

```bash
# from repos/ — apps are siblings of graph_agents/
mkdir -p <id> && cd <id> && git init
```

It gets its **own** repo. It does **not** get added to a root workspace, a root lockfile,
or a shared tsconfig/pyproject — none of those exist here, and creating one would collapse
the holding company into a monorepo.

Scaffold with the ecosystem's own tool (`npm create`, `uv init`, `cargo new`, …). Do not
hand-roll what a scaffolder does correctly.

**If `ui` is `responsive-web`, then apply `graph_agents/conventions/mobile-first.md` to what
the scaffolder just generated:**

- set the viewport meta (`width=device-width, initial-scale=1`)
- establish the 360px base layer — base styles are the small-screen layout, larger screens
  added via `min-width` only
- delete any desktop-fixed-width default the scaffolder emitted (a `width: 1200px` wrapper,
  a `min-width` on `body`, a demo page that overflows at 360)

This step is not optional. Ecosystem scaffolders do not default to mobile-first; they emit
a desktop demo page. If nobody post-processes it, the app is desktop-shaped from commit one
and retrofitting it later rewrites the layout layer.

**If `ui` includes `native-mobile`, then scaffold to `graph_agents/conventions/native-mobile.md`
(§ Stack and project shape, § Updates and runtime versions):**

- `npx create-expo-app@latest` — Continuous Native Generation; add `ios/` and `android/` to
  `.gitignore`, never commit them
- create `eas.json` with `development`, `preview` and `production` profiles, each with a `channel`
- set `runtimeVersion` explicitly in `app.config` (policy `fingerprint`)
- install `expo-secure-store` and `react-native-safe-area-context`
- run `npx expo-doctor` and fix what it reports

**If `ui` includes `native-desktop`, then scaffold to `graph_agents/conventions/native-desktop.md`
(§ Capabilities and permissions, § Content Security Policy):**

- `npm create tauri-app@latest` (Tauri 2)
- trim the default capability to only what the app uses — no blanket permission sets
- set a CSP; do not leave it `null`
- add a `.github/workflows` release matrix on `windows-latest` and `macos-latest` (plus
  `ubuntu-latest` if Linux ships), copied in as a starting point and owned locally

For both: **no signing keys, EAS project, store listing or updater key is created or committed
at scaffold time.** Credentials and the first release are `ops`, behind its gate.

## Step 3 — the app's own CLAUDE.md

Every app is the authority on itself. Write `<id>/CLAUDE.md` covering:

- what it is, in one paragraph
- how to run it, test it, and deploy it — as actual commands
- its architecture in a few lines: entry point, data flow, where state lives
- its constraints — anything an agent would otherwise get wrong
- this line, verbatim:
  `Standalone app under the repos/ umbrella. Never import from a sibling app; see ../graph_agents/CLAUDE.md.`

  That line names a path outside the app, which looks like the dependency the constitution
  forbids. It is not one: it is a **prose cross-reference for a human or an agent reading
  the file**, and nothing the app builds, imports, runs or ships resolves it. The app must
  still clone, install, test and deploy with `graph_agents/` absent from the disk. If you
  ever find yourself making code read that path, you have turned a convention into an
  edge — delete it. See `CLAUDE.md` § The one invariant.

When `ui` is `responsive-web`, the app's CLAUDE.md must also carry its **own copy** of the
width tiers and the viewport / touch-target bar under a `## UI targets` heading — copied out
of `graph_agents/conventions/mobile-first.md`, then owned locally and allowed to drift, like
any other copy. The app stays the authority on itself. It may *name*
`graph_agents/conventions/mobile-first.md` alongside the copy; that is the same kind of
prose cross-reference as the line above, subject to the same test.

When `ui` includes `native-mobile` or `native-desktop`, the app's CLAUDE.md likewise carries
its **own copy** of the bar under a `## Native targets` heading — mobile: targets, secure
storage, OTA discipline; desktop: capabilities, CSP — copied out of
`graph_agents/conventions/native-mobile.md` and `graph_agents/conventions/native-desktop.md`,
then owned locally. Config and workflow files are copy-once starting points, never a shared
template package and never a path the app reads at runtime.

## Step 4 — register it

Add an entry to `graph_agents/portfolio/registry.json`, with `path` and `entry_docs` relative to `repos/`. The entry must include `ui` — the fleet routes on it; it may be a string or an array. Unregistered apps are invisible to the fleet —
the registry is the index every agent routes through.

## Step 5 — first commit

```bash
git add -A && git commit -m "Initial scaffold"
```

No Claude attribution on it, or on any commit in the new repo — see the umbrella
`CLAUDE.md` § "Commits are the owner's alone". A repo's first commit is the one that sets
the tone for its whole history.

Do not create a remote or push unless the user asks.

## Copying from a sibling app

Encouraged — copy the file, then **own it locally**. Strip anything specific to the source
app. Never symlink, never reference across the boundary, never extract it into a shared
package. Divergence between the copies later is expected and fine; that is the price of
standalone, and it is cheaper than coupling.
