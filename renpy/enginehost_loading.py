# Enginehost: Ren'Py's start-up progress goes to Enginehost's loading screen, which draws the
# game's presplash_background and presplash_foreground as desktop Ren'Py's presplash draws them
# (Droidtop/tracker#821). On Android Ren'Py opens no presplash window, so pump_window returns
# before it counts anything; this counts as each Ren'Py version's own presplash counts, and sends
# the fraction its bar would show to Enginehost's named bridge, dev.enginehost.ActivityLoading,
# through the activity's enginehostLoading (apply_android_integration.py). The same kind of route
# as the links' and the text's, until Ren'Py moves onto the plugin transport.
#
# How each version counts, from renpy/display/presplash.py:
# - 7.4 to 8.0 (ProgressBar.update): one step per pump once the script is known, over the script
#   files plus 23;
# - 7.6 to 8.3 (module pump_count): one step per pump from the start, over the script files plus
#   23;
# - 8.4 on (pump_count, pump_clock): the same, over the common and the game's script files plus
#   pump_clock.
# 7.3 draws no bar; counting there is harmless, and a 7.3 game has no foreground picture.
from __future__ import division, print_function

import os
import time

import renpy

_activity = None
_original_pump = None
_original_end = None
_count = [0]
_sent = [-1.0]
_last = [0.0]
_ended = [False]


def _total(presplash):
    script = renpy.game.script
    if not script:
        return 0
    clock = getattr(presplash, "pump_clock", None)
    if clock is not None:
        return len(getattr(script, "common_script_files", ())) + len(script.script_files) + clock
    return len(script.script_files) + 23


def _pump():
    _original_pump()
    if _ended[0]:
        return
    presplash = renpy.display.presplash
    # 7.4 to 8.0 count only once the script is known; later versions count every pump.
    if hasattr(presplash, "pump_count") or renpy.game.script:
        _count[0] += 1
    now = time.time()
    if _last[0] + 1.0 / 24 > now:
        return
    total = _total(presplash)
    if not total:
        return
    done = min(_count[0] / float(total), 1.0)
    if done == _sent[0]:
        return
    _last[0] = now
    _sent[0] = done
    try:
        _activity.enginehostLoading(done)
    except Exception as e:
        print("Enginehost: the loading progress was not sent:", type(e).__name__)


def _end(*args, **kwargs):
    _ended[0] = True
    return _original_end(*args, **kwargs)


def install():
    """Reports Ren'Py's start-up progress to Enginehost, under Enginehost only."""
    global _activity, _original_pump, _original_end
    if not os.environ.get("ENGINEHOST_GAME_PATH"):
        return
    try:
        from jnius import autoclass  # type: ignore
        _activity = autoclass("org.renpy.android.PythonSDLActivity")
    except Exception as e:
        print("Enginehost: the loading progress is not reported:", type(e).__name__)
        return
    presplash = renpy.display.presplash
    if presplash.pump_window is not _pump:
        _original_pump = presplash.pump_window
        presplash.pump_window = _pump
    if presplash.end is not _end:
        _original_end = presplash.end
        presplash.end = _end
