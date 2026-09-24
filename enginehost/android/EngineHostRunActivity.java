package org.renpy.android;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
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

        launchEngine();
    }

    private void launchEngine() {
        Intent engineIntent = new Intent(this, PythonSDLActivity.class);
        engineIntent.putExtras(getIntent());
        startActivity(engineIntent);
        finish();
    }
}
