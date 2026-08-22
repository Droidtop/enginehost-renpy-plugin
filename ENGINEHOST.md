# This fork's real purpose

This is a fork of the real [Ren'Py engine](https://github.com/renpy/renpy),
being adapted into an [enginehost](https://github.com/bi0shacker001/enginehost)
plugin -- a generic Ren'Py player that loads a game folder at runtime
(handed a real, live folder path via enginehost's own Intent contract),
rather than each Ren'Py game shipping its own baked-in Android export.

## Branch convention

- **`master`** carries no local patches. It's kept fast-forwarded to real
  upstream `renpy/renpy` automatically (see
  `.github/workflows/sync-upstream.yml`, runs daily). Nothing ever commits
  to it directly.
- **`plugin/<version>`** branches carry the real Android plugin-contract
  patches (the `dev.enginehost.plugin.RUN` activity, meta-data, runtime
  folder loading instead of a baked-in game) for one real Ren'Py engine
  lineage. `plugin/renpy8` is the current Python 3 lineage, branched from
  `master`. A `plugin/renpy7` branch (the older Python 2 lineage, real
  compatibility need for older games) is real, planned follow-up work --
  it needs to branch from the actual last Ren'Py 7.x-era commit, not
  `master`, and hasn't been done yet.

Updating a `plugin/<version>` branch with upstream fixes is a deliberate,
manual merge/rebase from `master` -- not automated, since blindly
rebasing a patched branch risks silently mis-resolving a real conflict.
