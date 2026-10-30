# Enginehost: how many file calls each of Ren'Py's start-up phases makes, and how long they take,
# printed beside Ren'Py's own "<phase> took N ms" lines (Droidtop/tracker#821). Under Enginehost
# every call that names a file crosses the sandbox broker and, for a game on removable storage,
# Android's FUSE layer, so a slow start is read here as calls times cost per call before anything
# is cut. Counts Python's own calls (os.stat, os.lstat, os.listdir, os.scandir, os.open and open), which
# every path check Ren'Py makes goes through; reads on a file already open are not counted, as
# they do not cross the broker. Game paths are never printed.
from __future__ import print_function

import os
import time

import renpy

try:
    import __builtin__ as _builtins  # Python 2 (Ren'Py 7)
except ImportError:
    import builtins as _builtins  # Python 3 (Ren'Py 8)

_KINDS = ("stat", "lstat", "listdir", "scandir", "os.open", "open")
_count = dict((k, 0) for k in _KINDS)
_seconds = dict((k, 0.0) for k in _KINDS)
_installed = [False]


def _counted(kind, call):
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return call(*args, **kwargs)
        finally:
            _count[kind] += 1
            _seconds[kind] += time.time() - start
    wrapper.__name__ = getattr(call, "__name__", kind)
    return wrapper


def _report(phase):
    parts = []
    for kind in _KINDS:
        if _count[kind]:
            parts.append("%d %s (%.0f ms)" % (_count[kind], kind, _seconds[kind] * 1000))
        _count[kind] = 0
        _seconds[kind] = 0.0
    print("Enginehost: file calls in %s: %s" % (phase, ", ".join(parts) if parts else "none"))


def install():
    """Counts file calls per start-up phase, under Enginehost only."""
    if _installed[0] or not os.environ.get("ENGINEHOST_GAME_PATH"):
        return
    _installed[0] = True
    os.stat = _counted("stat", os.stat)
    os.lstat = _counted("lstat", os.lstat)
    os.listdir = _counted("listdir", os.listdir)
    if hasattr(os, "scandir"):  # Python 3: Ren'Py 8's folder walk
        os.scandir = _counted("scandir", os.scandir)
    os.open = _counted("os.open", os.open)
    _builtins.open = _counted("open", _builtins.open)

    original_clock = renpy.main.log_clock

    def log_clock(s):
        original_clock(s)
        _report(s)

    renpy.main.log_clock = log_clock

    presplash = renpy.display.presplash
    original_end = presplash.end

    def end(*args, **kwargs):
        # From "Creating interface object" to the first screen: Ren'Py times no phase there.
        _report("interface start to ready")
        return original_end(*args, **kwargs)

    presplash.end = end
