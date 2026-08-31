#!/usr/bin/env python3
"""Apply enginehost's Android wrapper to an unpacked official RAPT tree."""

import json
import shutil
import sys
from pathlib import Path


sdk = Path(sys.argv[1]).resolve()
runtime = sys.argv[2]
package = sys.argv[3]
plugin_version = sys.argv[4]
root = Path(__file__).resolve().parent

java_dir = sdk / "rapt/prototype/renpyandroid/src/main/java/org/renpy/android"
resource_manager = java_dir / "ResourceManager.java"
resource_source = resource_manager.read_text(encoding="utf-8")
resource_anchor = '        return res.getIdentifier(name, kind, act.getPackageName());\n'
resource_replacement = f'''        String enginehostPackage = act.getIntent().getStringExtra(
            "dev.enginehost.runtime.RESOURCE_PACKAGE");
        return res.getIdentifier(name, kind,
            enginehostPackage != null ? enginehostPackage : "{package}");
'''
if "dev.enginehost.runtime.RESOURCE_PACKAGE" not in resource_source:
    if resource_anchor not in resource_source:
        raise SystemExit("RAPT ResourceManager integration anchor changed")
    resource_manager.write_text(
        resource_source.replace(resource_anchor, resource_replacement, 1), encoding="utf-8")

activity = java_dir / "PythonSDLActivity.java"
source = activity.read_text(encoding="utf-8")
if "ENGINEHOST_RESOURCE_APKS" not in source:
    source = source.replace(
        "import android.os.VibrationEffect;\n",
        """import android.os.VibrationEffect;
import android.os.ParcelFileDescriptor;
import android.content.res.loader.ResourcesLoader;
import android.content.res.loader.ResourcesProvider;
""",
        1,
    )
    marker = '''    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Log.v("python", "onCreate()");
'''
    replacement = '''    // ENGINEHOST_RESOURCE_APKS: attach the signed RAPT resource APK before SDL
    // asks AssetManager to unpack Python and Ren'Py runtime files.
    private void attachEnginehostResources() {
        java.util.ArrayList<String> paths = getIntent().getStringArrayListExtra(
            "dev.enginehost.runtime.RESOURCE_APKS");
        if (paths == null) return;
        for (String path : paths) {
            try {
                if (Build.VERSION.SDK_INT >= 30) {
                    ParcelFileDescriptor descriptor = ParcelFileDescriptor.open(
                        new File(path), ParcelFileDescriptor.MODE_READ_ONLY);
                    ResourcesProvider provider = ResourcesProvider.loadFromApk(descriptor);
                    ResourcesLoader loader = new ResourcesLoader();
                    loader.addProvider(provider);
                    getResources().addLoaders(loader);
                } else {
                    java.lang.reflect.Method method = getAssets().getClass().getMethod(
                        "addAssetPath", String.class);
                    if (((Integer) method.invoke(getAssets(), path)) == 0) {
                        throw new IllegalStateException("could not attach " + path);
                    }
                }
            } catch (Exception e) {
                throw new IllegalStateException("Could not attach Enginehost runtime resources", e);
            }
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        attachEnginehostResources();
        Log.v("python", "onCreate()");
'''
    if marker not in source:
        raise SystemExit("RAPT resource attachment anchor changed")
    source = source.replace(marker, replacement, 1)
apk_anchor = '''        try {
            appInfo = packMgmr.getApplicationInfo(getPackageName(), 0);
            apkFilePath = appInfo.sourceDir;
        } catch (NameNotFoundException e) {
            apkFilePath = "";
        }
'''
apk_replacement = '''        java.util.ArrayList<String> enginehostResourceApks = getIntent().getStringArrayListExtra(
            "dev.enginehost.runtime.RESOURCE_APKS");
        if (enginehostResourceApks != null && !enginehostResourceApks.isEmpty()) {
            apkFilePath = enginehostResourceApks.get(0);
        } else {
            try {
                appInfo = packMgmr.getApplicationInfo(getPackageName(), 0);
                apkFilePath = appInfo.sourceDir;
            } catch (NameNotFoundException e) {
                apkFilePath = "";
            }
        }
'''
if apk_anchor not in source:
    raise SystemExit("RAPT APK path integration anchor changed")
source = source.replace(apk_anchor, apk_replacement, 1)
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
            String enginehostSavePath = getIntent().getStringExtra("dev.enginehost.runtime.SAVE_PATH");
            if (enginehostSavePath != null) {
                File enginehostSaveFolder = new File(enginehostSavePath);
                if (!enginehostSaveFolder.isDirectory() && !enginehostSaveFolder.mkdirs()) {
                    throw new IllegalArgumentException("enginehost save path is not writable: " + enginehostSavePath);
                }
                nativeSetEnv("ENGINEHOST_SAVE_PATH", enginehostSaveFolder.getAbsolutePath());
            }
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
android_json["version"] = plugin_version
(project / "android.json").write_text(json.dumps(android_json, indent=2) + "\n", encoding="utf-8")

options = project / "game/options.rpy"
source = options.read_text(encoding="utf-8")
source = source.replace('define config.version = "0.1.0"', f'define config.version = "{plugin_version}"')
source = source.replace('build.version = "0.1.0"', f'build.version = "{plugin_version}"')
options.write_text(source, encoding="utf-8")
