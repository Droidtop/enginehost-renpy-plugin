# Enginehost: a link the game opens is offered to the person by Enginehost, never opened by the
# engine itself (Enginehost docs/SPEC.md, "Links a game opens"; Droidtop/tracker#635; owner,
# 2026-10-23: "Enginehost should parse the link type (safely), and then OFFER to open it").
# renpy.open_url and a game script's own webbrowser calls both end in webbrowser's preferred
# browser, which under Enginehost is this one. It hands the link to the activity's
# enginehostOpenLink (apply_android_integration.py), which asks Enginehost to offer it.
from __future__ import print_function

import os
import webbrowser


class EnginehostBrowser(webbrowser.BaseBrowser):

    def open(self, url, new=0, autoraise=True):
        try:
            from jnius import autoclass  # type: ignore
            activity = autoclass("org.renpy.android.PythonSDLActivity")
            return bool(activity.enginehostOpenLink(url))
        except Exception as e:
            # Nothing opens rather than the link opening unasked.
            print("Enginehost: the link was not offered:", e)
            return False


def install():
    """Makes Enginehost's offer the browser every webbrowser call uses, under Enginehost only."""
    if not os.environ.get("ENGINEHOST_GAME_PATH"):
        return
    browser = EnginehostBrowser("enginehost")
    try:
        webbrowser.register("enginehost", None, browser, preferred=True)
    except TypeError:
        # Python 2 (Ren'Py 7): a negative update_tryorder puts it first.
        webbrowser.register("enginehost", None, browser, -1)
