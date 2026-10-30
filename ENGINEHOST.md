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

## The game's text goes to Enginehost (2026-10-28)

Enginehost can read a game's lines aloud and translate them (Enginehost docs/text-services.md,
Droidtop/tracker#490). Every line reports its text with `renpy/enginehost_text.py` (series patch
`0008-report-text-to-enginehost.patch`), which `enginehost_platform.present()` installs beside
the link route, under Enginehost only. It has two hooks, the same from Ren'Py 7.3 to 8.5.

- **`display_say`**, which every line passes through: ADV characters through
  `renpy.character.display_say`, NVL through `renpy.display_say`. Both are wrapped. Each line is
  sent as an ehtext/1 `line` event with its speaker, its text without Ren'Py's text tags,
  whether the game voices it (`_get_voice_info()`, which covers `config.auto_voice`) and its
  window (`adv` or `nvl`). `advance` follows when the line's interaction ends.
- **`config.say_menu_text_filter`**, which a say statement runs on its text before it is shown.
  It prints the line's translation in Ren'Py's own text box when Enginehost already has it, and
  the original otherwise: it never waits. A game's own filter still runs first. Ours is kept
  around it at every interaction, because a game sets its filter during init, after ours is
  installed. Menu choices keep their text for now.

A say statement's line id is its translation identifier: Ren'Py sets it for the statement and
clears it after, so both hooks name the line alike. A line without one (`renpy.say` from Python)
is named by its text.

The lines reach Enginehost through `PythonSDLActivity.enginehostText` and
`enginehostReplaceText`, which `apply_android_integration.py` adds. They call Enginehost's
`dev.enginehost.ActivityText` by reflection: the same kind of named bridge as the links', chosen
by the owner on 2026-10-28 until Ren'Py moves onto the plugin transport. On an Enginehost without
it, nothing is sent and every line prints as the game wrote it. Game text is never logged.

## The presplash fills as the game loads (2026-10-30)

Desktop Ren'Py draws `presplash_background` and `presplash_foreground` as a progress bar while
the game loads; on Android Ren'Py opens no presplash window, so it counts nothing. Enginehost
draws the game's presplash before the core starts, and Series patch 0009
(`renpy/enginehost_loading.py`, installed by `enginehost_platform.present()` beside the links and
the text) wraps `renpy.display.presplash.pump_window` to count as that line's Ren'Py counts and
send the fraction its bar would draw (Droidtop/tracker#821):

- 7.4 to 8.0: one step per pump once the script is known, over the script files plus 23;
- 7.6 to 8.3: one step per pump from the start, over the script files plus 23;
- 8.4 on: the same, over the common and the game's script files plus `pump_clock`.

It sends at most 24 times a second, only when the fraction changes, and stops at
`presplash.end()`. `apply_android_integration.py` adds `PythonSDLActivity.enginehostLoading`,
which calls Enginehost's `dev.enginehost.ActivityLoading.progress` by reflection, looked up once;
on an Enginehost without it, nothing is sent. Enginehost also counts each report as a sign the
game is still loading, so it does not ask about a black screen while it fills.

## File calls are counted per start-up phase (2026-10-30)

Series patch 0010 (`renpy/enginehost_files.py`, installed by `enginehost_platform.present()`)
counts the file calls Ren'Py makes in each start-up phase and prints them after Ren'Py's own
`<phase> took N ms` line, as `Enginehost: file calls in <phase>: N stat (ms), N listdir (ms),
...`, plus one line for "interface start to ready" at `presplash.end()`, the stretch Ren'Py times
as a whole (Droidtop/tracker#821: Bare Witness took 176 s on the console's SD card). It wraps
`os.stat`, `os.lstat`, `os.listdir`, `os.scandir`, `os.open` and `open`, which every path check
goes through; reads on an open file are not counted, since they do not cross Enginehost's
sandbox broker. It prints no paths. The numbers say which calls a slow start is made of, so the
start is cut at its cause rather than guessed at.

## 32-bit engines only on request, never published (2026-10-30)

Official Ren'Py cores ship arm64-v8a and x86_64 only. RAPT still builds armeabi-v7a, and
`enginehost/keep_64bit_abis.py` removes it before signing (Droidtop/tracker#646). For someone who
needs a 32-bit engine, the owner kept a way to build one: dispatch `android-plugin.yml` on a line
with `include_32_bit` on. That build keeps RAPT's 32-bit libraries and ends as the unsigned bundle
inputs artifact (`enginehost-renpy-<runtime>-v1-unsigned`). It is never signed or published, and
`publish` does nothing with it. Enginehost's signing gate refuses 32-bit libraries anyway.
