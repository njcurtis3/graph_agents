# Convention — native desktop (Tauri 2)

A desktop binary has file-system, process and network reach that a web page never does.
This file is the bar for Tauri 2 apps: least privilege first, then the platform details. It
is prose and checklists, nothing more — see § This is a convention, not a dependency at the
bottom before you wire anything to this path. The stack choice is
`decisions/0003-native-stack.md`.

## Does this apply?

**It applies when the app's `ui` in `graph_agents/portfolio/registry.json` includes
`native-desktop`.** `ui` may be a single string or an array.

It does not apply to `responsive-web` alone, `native-mobile` (see `native-mobile.md`), or
`none`. Note that `desktop-only` is a different thing: it means a **local viewer in a browser
on `127.0.0.1`** with no installable binary. It carries none of this file's obligations.

## Build locations

There is no Mac. Windows builds locally or on a windows runner; **macOS builds, signing and
notarization run on a GitHub Actions macOS runner** in the `TelosRG` org; Linux builds on
an ubuntu runner. Never write a step that assumes the owner's machine can build macOS.

## Capabilities and permissions

Tauri 2 is deny-by-default: a webview can call only the commands and plugin permissions that
a **capability** file under `src-tauri/capabilities/` grants to its window.

- **Allowlist, not blocklist.** Grant the specific permissions a window uses.
- **File system scopes are narrow.** Scope to the app's own data directory or a named
  folder, never `$HOME/**`, `/**` or a drive root. User-chosen files come through the
  dialog plugin.
- **Shell and opener scopes are narrow.** `shell:allow-execute` / `shell:allow-spawn` are
  limited to named sidecars with fixed args; `opener` is limited to `https` URLs
  the app expects. No scope that lets the frontend run an arbitrary program or open an arbitrary path.
- **Capabilities are per window.** A window that shows remote content gets fewer
  permissions than the main window, and remote origins are listed explicitly.

## Content Security Policy

- The CSP is **set in `tauri.conf.json`** (`app.security.csp`). It is never `null` and
  never omitted.
- No `unsafe-eval`. `unsafe-inline` is not allowed for scripts; styles only when a
  framework requires it and Tauri's nonce/hash injection does not cover it.
- `connect-src` lists the origins the app talks to, not `*`.

## IPC commands

`#[tauri::command]` functions are the app's attack surface; the frontend is untrusted input.

- **Validate every argument** in Rust: lengths, ranges, enums, formats. Prefer typed
  arguments (`serde` structs, enums) over free strings.
- **No path or command passthrough.** A command never takes a path from the frontend and
  reads, writes or deletes it unchecked; it resolves against a base directory and rejects
  `..` and absolute paths. A command never builds a shell command from frontend strings.
- Commands return typed `Result`s with errors that do not leak absolute paths or secrets.
- Register only the commands a window needs, and keep each one small enough to review.

## Windows, menus and shortcuts

- **Window state persists** (size, position, maximized) with the window-state plugin, and
  restores to a visible display if the saved monitor is gone.
- **Menus follow the OS.** macOS gets an app menu (About, Preferences/Settings, Hide, Quit)
  and standard Edit menu items so copy/paste work; Windows and Linux put Settings and Exit
  under File/Edit by their own convention.
- **Shortcuts use `CmdOrCtrl`**, never a hard-coded `Ctrl` or `Cmd`.

## Webviews differ

The frontend runs in **WebView2** (Windows, Chromium-based), **WKWebView** (macOS, WebKit)
and **WebKitGTK** (Linux, WebKit, often the oldest). CSS and JS features that work in one
may be missing in another.

- Do not use a web API or CSS feature without checking it against all three engines.
- Test or at minimum review against WebKit as well as Chromium; the Linux webview is the
  floor for what the app may assume.
- The OS decides the webview version; the app cannot bundle its own.

## Updater and signing

- **Updater artifacts are signed.** The updater's **public key is in `tauri.conf.json`**
  (`plugins.updater.pubkey`); the **private key lives only in CI secrets** and is never in
  the repo, a log, or a developer machine's committed files. Update endpoints are `https`.
- **Windows: Authenticode** code signing. **macOS: Developer ID signing plus notarization**,
  done on the macOS runner with credentials from Actions secrets. **Linux:** signed
  updater artifacts; package signing as the distribution requires.
- A release that is unsigned is not a release.

## Prohibitions — each one visible in a diff

- **No broad `fs` scope** (`$HOME/**`, `/**`, a drive root) and no `fs:allow-*` without a scope.
- **No broad shell or opener scope** — no `shell:allow-execute` / `allow-spawn` without
  fixed program and args, no `opener` over arbitrary paths.
- **No `"csp": null`, no missing CSP, no `unsafe-eval`.**
- **No `#[tauri::command]` that uses a frontend path or string as a path or command
  unvalidated.**
- **No updater private key, signing certificate or notarization credential in the repo.**
- **No hard-coded `Ctrl` or `Cmd` accelerator** where `CmdOrCtrl` is meant.
- **No capability shared between a main window and a window loading remote content.**

## Reviewer checklist

Yes/no, answerable by reading a diff. `reviewer.md` points here by name.

1. Does every new or changed capability grant only the permissions the window uses, with
   fs, shell and opener scopes narrowed to named paths, programs or URLs?
2. Is the CSP set in `tauri.conf.json`, not `null`, and free of `unsafe-eval`?
3. Does every new `#[tauri::command]` validate its arguments, and avoid using a frontend
   path or string as a path or shell command?
4. Is each command registered only for windows that need it?
5. Do windows loading remote content have their own, smaller capability?
6. Is window state persisted and restored?
7. Are menus appropriate per OS (macOS app menu, Edit items) and accelerators `CmdOrCtrl`?
8. Does new frontend code avoid web features missing from WebView2, WKWebView or WebKitGTK?
9. Is the updater `pubkey` in config and the private key referenced only as a CI secret?
10. Does the release workflow sign for each OS (Authenticode; Developer ID and notarization
    on the macOS runner)?

Anything you cannot answer from the diff (actual signing, a real notarization run) is a
**note**, not a rejection.

## This is a convention, not a dependency

This file is **read and copied as guidance**. No app may import it, build against it, or
resolve this path at build, test or deploy time. An app's `CLAUDE.md` may *name* this path
for a human reader. The mechanical test: delete `graph_agents/` from disk, and every app
must still clone, install, test and build.

When a new app is born with `native-desktop` in its `ui`, the rules above get **copied into
that app's own `CLAUDE.md`** under `## Native targets`, then owned locally and allowed to
drift. Copy, don't couple.

See `graph_agents/CLAUDE.md` § The one invariant.
