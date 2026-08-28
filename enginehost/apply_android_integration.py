#!/usr/bin/env python3
"""Apply enginehost's Android wrapper to an unpacked official RAPT tree."""

import json
import shutil
import sys
from pathlib import Path


sdk = Path(sys.argv[1]).resolve()
runtime = sys.argv[2]
package = sys.argv[3]
root = Path(__file__).resolve().parent

java_dir = sdk / "rapt/prototype/renpyandroid/src/main/java/org/renpy/android"
activity = java_dir / "PythonSDLActivity.java"
source = activity.read_text(encoding="utf-8")
anchor = '        nativeSetEnv("ANDROID_OLD_PUBLIC", oldExternalStorage.getAbsolutePath());\n'
addition = '''

        String enginehostGamePath = getIntent().getStringExtra("path");
        if (enginehostGamePath != null) {
            File enginehostGameFolder = new File(enginehostGamePath);
            if (!enginehostGameFolder.isDirectory()) {
                throw new IllegalArgumentException("enginehost path is not a directory: " + enginehostGamePath);
            }
            nativeSetEnv("ENGINEHOST_GAME_PATH", enginehostGameFolder.getAbsolutePath());
            String enginehostOptions = getIntent().getStringExtra("options");
            if (enginehostOptions != null) nativeSetEnv("ENGINEHOST_OPTIONS_JSON", enginehostOptions);
        }
'''
if "ENGINEHOST_GAME_PATH" not in source:
    if anchor not in source:
        raise SystemExit("RAPT PythonSDLActivity integration anchor changed")
    activity.write_text(source.replace(anchor, anchor + addition, 1), encoding="utf-8")
shutil.copy2(root / "android/EngineHostRunActivity.java", java_dir / "EngineHostRunActivity.java")

manifest = sdk / "rapt/templates/app-AndroidManifest.xml"
source = manifest.read_text(encoding="utf-8")
activity_xml = '''

    <activity
        android:name="org.renpy.android.EngineHostRunActivity"
        android:exported="true">
      <intent-filter>
        <action android:name="dev.enginehost.plugin.RUN" />
        <category android:name="android.intent.category.DEFAULT" />
      </intent-filter>
      <meta-data android:name="dev.enginehost.plugin.engine" android:value="renpy" />
      <meta-data android:name="dev.enginehost.plugin.pluginVersion" android:value="{{ config.version }}" />
      <meta-data android:name="dev.enginehost.plugin.capabilities" android:resource="@raw/enginehost_capabilities" />
    </activity>
'''
if "dev.enginehost.plugin.RUN" not in source:
    marker = "    </activity>"
    if marker not in source:
        raise SystemExit("RAPT manifest integration anchor changed")
    manifest.write_text(source.replace(marker, marker + activity_xml, 1), encoding="utf-8")

res = sdk / "rapt/prototype/app/src/main/res"
for directory in (root / "android/res").iterdir():
    shutil.copytree(directory, res / directory.name, dirs_exist_ok=True)
raw = res / "raw"
raw.mkdir(parents=True, exist_ok=True)
(raw / "enginehost_capabilities.json").write_text(json.dumps({
    "schemaVersion": 1,
    "capabilities": [{
        "id": f"renpy-{runtime}",
        "engineContext": "python3" if runtime.startswith("8.") else "python2",
        "runtimeVersion": runtime,
    }],
}, indent=2) + "\n", encoding="utf-8")

project = root / "template"
android_json = json.loads((project / "android.json").read_text(encoding="utf-8"))
android_json["package"] = package
android_json["name"] = f"enginehost Ren'Py {runtime}"
(project / "android.json").write_text(json.dumps(android_json, indent=2) + "\n", encoding="utf-8")
