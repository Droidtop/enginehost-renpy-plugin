# enginehost integration

This fork preserves the upstream engine and adds a small interoperability
seam: `renpy.bootstrap` honors `ENGINEHOST_GAME_PATH` as the game's base
directory while keeping Ren'Py's runtime inside the separately installed
Android plugin. Game scripts and assets continue to be read in place.

## Branch model

`master` follows upstream Ren'Py. `plugin-core` contains the portable
enginehost bootstrap, Android entry point, RAPT integration, and build
workflow. Release branches such as `plugin/8.5`, `plugin/8.3`, and
`plugin/8.2` start at exact upstream releases and receive that changeset.
Engine fixes remain within the appropriate release line; plugin integration
fixes originate in `plugin-core` and are then applied to supported lines.

Each release branch owns `enginehost/runtime.json`. Engine runtime version,
Android package identity, and plugin release version are separate values. This
allows different engine lines and multiple plugin slots to remain installed
together while enginehost's optional `pluginVersion` allowlist can exclude a
bad integration release.

Upstream Ren'Py: https://github.com/renpy/renpy
enginehost: https://github.com/bi0shacker001/enginehost
