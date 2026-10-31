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

## Search path on the 7.3 line

Ren'Py 7.3's `renpy.main` empties `config.searchpath` on Android and searches
only `$ANDROID_PUBLIC/game`, so archives in the Enginehost game folder were
never found (`Couldn't find file 'fullgame.rpa'`). When `ENGINEHOST_GAME_PATH`
is set, 7.3 searches only `config.gamedir` (the game folder's own `game/`,
chosen by bootstrap); the app's public folder is not a game source, matching
the loader's rule that game files come from the game folder only. Lines 7.4+
keep `config.gamedir` in their Android searchpath and guard the APK game
assets in `renpy.loader` instead.

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
- **`config.variants`**: what a desktop build has. The variants that name a
  platform (`android`, `mobile`, `ios`, `firetv`, `chromeos`) and the
  screen-size variants (`small`, `medium`, `phone`, `tablet`, `tv`) are taken
  out, and `large` and `pc` are added last, as desktop Ren'Py has them. `touch`
  stays (owner, 2026-10-23: "Desktop flags, keep touch layouts"). Until
  2026-10-31 the size variants stayed too. Then a desktop game's GUI template
  applied Ren'Py's phone overrides, which nobody shipping a desktop build had
  laid out, on the RP5's 5.5-inch screen (Ren'Py calls anything under 6.95
  inches `small`; BlueStacks reports `medium`): bigger interface text, a 400px
  preferences column, and labels that wrapped under their buttons (Love & Sex:
  Second Base's Options and Drug Store screens). Series patch
  `0012-desktop-size-variants.patch`.

A game's options can choose Android instead: `"platform": "android"` in its
enginehost.json `options`, which the activity passes as
`ENGINEHOST_ENGINE_OPTIONS`. The log says which platform was shown
("Enginehost: presenting windows to the game").
