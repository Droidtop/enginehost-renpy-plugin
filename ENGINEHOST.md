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

## The game sees its own platform (2026-10-23)

Games do not get to refuse Enginehost's wrapper. The owner, 2026-10-22: "If
the test game refuses android, we need to fix our wrapper to fix that. Games
don't GET to say no to us." (NekoParadise 0.18 raised "Android not
supported!" from its own script on the Ren'Py 7.5 core.)

So every line shows a game's own script the desktop platform the game was
shipped for: Windows when its folder has a `.exe`, Linux for a `.sh`, macOS
for a `.app`, and Windows otherwise (`renpy/enginehost_platform.py`, series
patch `0006-present-shipped-platform.patch`). It runs right after Ren'Py
chooses its variants, and it changes two things.

- **The platform flags in `renpy.exports`**, the `renpy` a script sees:
  `android`, `mobile`, `ios` and `emscripten` are false, and the shipped
  platform's flag is true. The engine's own flags (`renpy.android` on the
  package) are unchanged, so it still runs as the Android build it is.
- **`config.variants`**: the variants that name a platform (`android`,
  `mobile`, `ios`, `firetv`, `chromeos`) are taken out, and `pc` is added
  last. The layout variants (`touch`, `small`, `medium`, `phone`, `tablet`,
  `tv`) stay, so screens still fit the device (owner, 2026-10-23).

A game's options can choose Android instead: `"platform": "android"` in its
enginehost.json `options`, which the activity passes as
`ENGINEHOST_ENGINE_OPTIONS`. The log says which platform was shown
("Enginehost: presenting windows to the game").

## Links the game opens are offered by Enginehost (2026-10-24)

The owner, 2026-10-23: "Enginehost should parse the link type (safely), and then OFFER to open
it" (Droidtop/tracker#635). Ren'Py opens a link through Python's `webbrowser`: `renpy.open_url`,
and a game script's own `webbrowser` calls. Under Enginehost, every line registers
`renpy/enginehost_links.py`'s browser as `webbrowser`'s preferred one (series patch
`0007-offer-links-through-enginehost.patch`, installed from `enginehost_platform.present()`). It
hands the link to the activity's `enginehostOpenLink`, which `apply_android_integration.py` adds.
That calls Enginehost's `dev.enginehost.ActivityLinks.offer` by name, since a core on the
activity transport has no `EngineHost`. Enginehost checks the link, says what it is, and offers
to open it or copy it. On an Enginehost without that route nothing opens, rather than the link
opening unasked.
