# Enginehost: games do not get to refuse our wrapper (owner, 2026-10-22:
# "If the test game refuses android, we need to fix our wrapper to fix that.
# Games don't GET to say no to us").
#
# A game's own script sees the platform it was shipped for, as a desktop
# build would see it: renpy.android, renpy.mobile and the other platform
# flags in renpy.exports (the "renpy" every script uses), and no "android",
# "mobile" or device variant in config.variants, with "pc" added. The
# engine itself keeps reading its own flags (renpy.android on the package),
# so it still runs as the Android build it is. "touch" stays (owner,
# 2026-10-23: "Desktop flags, keep touch layouts"), but the screen-size
# variants a desktop build never has (small, medium, phone, tablet, tv) give
# way to the "large" a desktop build gets: a desktop game's GUI template still
# carries Ren'Py's untested phone overrides, which on a screen under 6.95
# inches enlarged its text and narrowed its menus. A game's options can
# choose Android instead: {"platform": "android"}.
from __future__ import print_function

import json
import os

import renpy
import renpy.enginehost_links
import renpy.enginehost_text
import renpy.enginehost_loading
import renpy.enginehost_files
import renpy.enginehost_listings

# Variants that say which platform this is, not how big or touchable it is.
PLATFORM_VARIANTS = ("android", "mobile", "ios", "firetv", "chromeos")

# Variants that say how big the screen is. A desktop build has only "large"
# (renpy/main.py choose_variants), so these are replaced by it.
SIZE_VARIANTS = ("small", "medium", "large", "phone", "tablet", "tv")

FLAGS = ("android", "ios", "emscripten", "mobile", "windows", "macintosh", "linux")


def shipped_platform(game_path):
    """The desktop platform the game folder was shipped for: windows for a .exe, linux for a .sh, macintosh for a .app."""
    try:
        names = [n.lower() for n in os.listdir(game_path)]
    except OSError:
        names = []
    if any(n.endswith(".exe") for n in names):
        return "windows"
    if any(n.endswith(".sh") for n in names):
        return "linux"
    if any(n.endswith(".app") for n in names):
        return "macintosh"
    return "windows"


def presented_variants(variants):
    """config.variants as a desktop build has them: the platform's and the screen size's own names
    taken out, then "large" and "pc" before the final None. "touch" is kept."""
    kept = [v for v in variants if v not in PLATFORM_VARIANTS and v not in SIZE_VARIANTS and v != "pc"]
    at = kept.index(None) if None in kept else len(kept)
    kept[at:at] = ["large", "pc"]
    return kept


def chosen(options_json):
    try:
        options = json.loads(options_json or "{}")
    except ValueError:
        return None
    return options.get("platform") if isinstance(options, dict) else None


def present():
    game_path = os.environ.get("ENGINEHOST_GAME_PATH")
    if not renpy.android or not game_path:
        return
    # Links the game opens go to Enginehost's offer, whatever platform the game is shown.
    renpy.enginehost_links.install()
    renpy.enginehost_text.install()
    renpy.enginehost_loading.install()
    renpy.enginehost_files.install()
    renpy.enginehost_listings.install()
    if chosen(os.environ.get("ENGINEHOST_ENGINE_OPTIONS")) == "android":
        print("Enginehost: presenting Android to the game, as chosen for it")
        return
    platform = shipped_platform(game_path)
    for name in FLAGS:
        setattr(renpy.exports, name, name == platform)
    renpy.config.variants = presented_variants(renpy.config.variants)
    print("Enginehost: presenting", platform, "to the game; variants", renpy.config.variants)
