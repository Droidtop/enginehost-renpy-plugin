# enginehost integration

This branch is pinned to Ren'Py's official `8.5.3.26051504` release tag.
It preserves the upstream engine and adds one interoperability seam:
`renpy.bootstrap` honors `ENGINEHOST_GAME_PATH` as the game's base
directory while keeping Ren'Py's runtime inside the separately installed
plugin. Game scripts and assets continue to be read in place.

Upstream Ren'Py: https://github.com/renpy/renpy
enginehost: https://github.com/bi0shacker001/enginehost
