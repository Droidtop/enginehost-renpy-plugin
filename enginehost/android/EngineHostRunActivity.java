package org.renpy.android;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.system.ErrnoException;
import android.system.Os;
import android.widget.Toast;

import java.io.File;

/**
 * Programmatic enginehost entry point. It never imports or copies a game;
 * it forwards the caller's live folder to the bundled Ren'Py runtime. Android
 * still enforces the normal app storage sandbox; this activity does not request
 * broad storage access on the user's behalf.
 */
public class EngineHostRunActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        String path = getIntent().getStringExtra("path");
        if (path == null || !new File(path).isDirectory()) {
            Toast.makeText(this, "enginehost did not provide a valid game folder", Toast.LENGTH_LONG).show();
            finish();
            return;
        }

        exportGamePath(path);
        launchEngine();
    }

    /**
     * Tell Ren'Py which folder it was handed, in the environment.
     *
     * savelocation.py only adds the game-local saves directory when it is not
     * running on mobile OR when ENGINEHOST_GAME_PATH is set, because enginehost
     * runs a desktop game tree in place on Android. Nothing was setting that
     * variable, so the guard was never true on a device and the branch it
     * guards had never once executed: a game's existing game/saves directory
     * was invisible, and saves silently went to app storage only. Setting it
     * here, before PythonSDLActivity starts the interpreter in this same
     * process, is what makes the read/write MultiLocation actually include the
     * game's own saves.
     */
    private void exportGamePath(String path) {
        try {
            Os.setenv("ENGINEHOST_GAME_PATH", path, true);
        } catch (ErrnoException error) {
            // Not fatal. The game still runs; saves fall back to app storage,
            // which is exactly the behaviour we had before this existed.
            Toast.makeText(this, "Could not expose the game folder for saves", Toast.LENGTH_LONG).show();
        }
    }

    private void launchEngine() {
        Intent engineIntent = new Intent(this, PythonSDLActivity.class);
        engineIntent.putExtras(getIntent());
        startActivity(engineIntent);
        finish();
    }
}
