# Third-party components

This branch (`plugin-core`) carries Enginehost's Ren'Py wrapper only. The
Ren'Py engine source itself is merged in per release line (`plugin/7.3`
through `plugin/8.5`), each of which extracts its own engine directory (see
`git log --oneline plugin-core..plugin/8.1`). `enginehost/LICENSES.md`
documents the notice that ships inside the built bundle and is authoritative
for what is actually distributed; this table indexes it.

| Component | Version / commit | Licence | Source | Where in tree |
|---|---|---|---|---|
| Ren'Py | matches each `plugin/<line>` branch (7.3-8.5) | MIT, with LGPL-licensed portions | https://github.com/renpy/renpy | merged into each `plugin/<line>` branch, not present on `plugin-core` |
| RAPT (Ren'Py Android Packaging Tool) | matches the Ren'Py release it ships with | MIT | https://github.com/renpy/renpy (`rapt/`) | unmodified RAPT runtime APK inside the built Enginehost bundle |
| Pygame_SDL2 | as vendored by the Ren'Py release in use | MIT / LGPL | https://github.com/renpy/pygame_sdl2 | inside the Ren'Py binaries that Ren'Py itself bundles |
| SDL2 | as vendored by the Ren'Py release in use | zlib | https://www.libsdl.org | inside the Ren'Py binaries that Ren'Py itself bundles |
| Python | as vendored by the Ren'Py release in use | PSF License | https://www.python.org | inside the Ren'Py binaries that Ren'Py itself bundles |

## Obligations

The LGPL-licensed portions inside Ren'Py require that a distributed *game*
remain re-linkable against a replacement LGPL library. That obligation falls
on whoever distributes a game built with Ren'Py, not on this wrapper
repository, which does not redistribute Ren'Py or any game itself.
