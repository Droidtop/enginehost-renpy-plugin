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

# A loaded resource APK can share package id 0x7f with Enginehost. Android then
# exposes its assets but may not resolve its string resources by name. RAPT only
# uses private_version to decide whether private.mp3 needs extracting, so bind
# that value to this signed plugin build instead of depending on package ids.
resource_source = resource_manager.read_text(encoding="utf-8")
version_anchor = '''    public String getString(String name) {

        try {
'''
version_replacement = f'''    public String getString(String name) {{

        if ("private_version".equals(name) &&
                act.getIntent().hasExtra("dev.enginehost.runtime.RESOURCE_APKS")) {{
            return "{plugin_version}";
        }}

        try {{
'''
if "dev.enginehost.runtime.RESOURCE_APKS" not in resource_source:
    if version_anchor not in resource_source:
        raise SystemExit("RAPT ResourceManager version anchor changed")
    resource_manager.write_text(
        resource_source.replace(version_anchor, version_replacement, 1), encoding="utf-8")

activity = java_dir / "PythonSDLActivity.java"
source = activity.read_text(encoding="utf-8")
if "ENGINEHOST_RESOURCE_APKS" not in source:
    # Anchor on an import every supported RAPT has. VibrationEffect was the
    # old anchor and 8.1's RAPT does not import it, so the replace quietly
    # did nothing while the code below still went in, and the build failed
    # much later saying it could not find ParcelFileDescriptor. Vibrator is
    # present in every RAPT this wrapper targets. Check it, so a future move
    # fails here and says so rather than as a mystery symbol error.
    import_anchor = "import android.os.Vibrator;\n"
    if import_anchor not in source:
        raise SystemExit("RAPT PythonSDLActivity import anchor changed")
    source = source.replace(
        import_anchor,
        """import android.os.Vibrator;
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
        Log.i("EnginehostRenPy", "Attaching runtime resources");
        java.util.ArrayList<String> paths = getIntent().getStringArrayListExtra(
            "dev.enginehost.runtime.RESOURCE_APKS");
        if (paths == null) {
            Log.e("EnginehostRenPy", "Runtime resource APK list is missing");
            return;
        }
        for (String path : paths) {
            try {
                if (Build.VERSION.SDK_INT >= 30) {
                    ParcelFileDescriptor descriptor = ParcelFileDescriptor.open(
                        new File(path), ParcelFileDescriptor.MODE_READ_ONLY);
                    ResourcesProvider provider = ResourcesProvider.loadFromApk(descriptor);
                    ResourcesLoader loader = new ResourcesLoader();
                    loader.addProvider(provider);
                    getResources().addLoaders(loader);
                    Log.i("EnginehostRenPy", "Attached runtime resource APK " + path);
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
        Log.i("EnginehostRenPy", "PythonSDLActivity.onCreate class=" + getClass().getName());
        attachEnginehostResources();
        Log.i("EnginehostRenPy", "Calling SDLActivity.onCreate");
        Log.v("python", "onCreate()");
'''
    if marker not in source:
        # Older RAPTs (7.3) open onCreate without the python log line; attach
        # the resources as the first statement there instead.
        bare_marker = '''    @Override
    protected void onCreate(Bundle savedInstanceState) {
'''
        if bare_marker not in source:
            raise SystemExit("RAPT resource attachment anchor changed")
        marker = bare_marker
        replacement = replacement.replace('        Log.v("python", "onCreate()");' + chr(10), '')
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

        String enginehostGamePath = getIntent().getStringExtra("dev.enginehost.runtime.PATH");
        if (enginehostGamePath != null) {
            File enginehostGameFolder = new File(enginehostGamePath);
            if (!enginehostGameFolder.isDirectory()) {
                throw new IllegalArgumentException("enginehost path is not a directory: " + enginehostGamePath);
            }
            nativeSetEnv("ENGINEHOST_GAME_PATH", enginehostGameFolder.getAbsolutePath());
            String enginehostOptions = getIntent().getStringExtra("dev.enginehost.runtime.CALLER_CONFIG");
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

# Enginehost attaches this APK's resources to the host's own Resources
# object and refuses a bundle compiled at 0x7f, the host's own id, because
# the host's table would win every lookup. RAPT generates app/build.gradle
# from this template; compile the plugin's resources where the host will
# never be, as the Godot bundle does.
# Ren'Py 7.3's RAPT pulls Google's APK-expansion helpers from jcenter, which
# stopped serving them; nothing else hosts them, so the build cannot resolve
# com.danikula.expansion at all. Enginehost never builds an expansion APK: the
# game is read from its own folder. Drop the dependency and the three classes
# that use it. SDLActivity reaches the same library reflectively and copes with
# it being absent, and the manifest entries sit behind RAPT's own expansion
# switch, so nothing else has to change.
library_gradle = sdk / "rapt/prototype/renpyandroid/build.gradle"
if library_gradle.is_file():
    source = library_gradle.read_text(encoding="utf-8")
    if "com.danikula.expansion" in source:
        kept = [line for line in source.splitlines(keepends=True) if "com.danikula.expansion" not in line]
        library_gradle.write_text("".join(kept), encoding="utf-8")
        for name in ("DownloaderActivity", "DownloaderService", "DownloaderAlarmReceiver"):
            downloader = sdk / f"rapt/prototype/renpyandroid/src/main/java/org/renpy/android/{name}.java"
            if downloader.is_file():
                downloader.unlink()

# jcenter is read-only and increasingly incomplete; the artifacts these older
# RAPTs want are on Maven Central. Ask for both rather than only the dead one.
for build_file in (sdk / "rapt/prototype/build.gradle", sdk / "rapt/templates/build.gradle"):
    if build_file.is_file():
        source = build_file.read_text(encoding="utf-8")
        if "jcenter()" in source and "mavenCentral()" not in source:
            build_file.write_text(source.replace("jcenter()", "mavenCentral()\n        jcenter()"), encoding="utf-8")

# Ren'Py 7.3's RAPT builds with the 2018 Android Gradle plugin, whose AAPT2
# has no --allow-reserved-package-id: it cannot compile this plugin's
# resources anywhere but 0x7f, the one id Enginehost refuses. Give that line
# the plugin and Gradle versions 7.4's own RAPT ships, which do support it.
prototype_gradle = sdk / "rapt/prototype/build.gradle"
if prototype_gradle.is_file():
    source = prototype_gradle.read_text(encoding="utf-8")
    if "com.android.tools.build:gradle:3." in source:
        import re as _re
        prototype_gradle.write_text(
            _re.sub(r"com\.android\.tools\.build:gradle:3\.[0-9.]+", "com.android.tools.build:gradle:4.0.1", source),
            encoding="utf-8")
        wrapper = sdk / "rapt/prototype/gradle/wrapper/gradle-wrapper.properties"
        if wrapper.is_file():
            wrapper.write_text(
                _re.sub(r"gradle-[0-9.]+-(all|bin)\.zip", "gradle-6.1.1-all.zip", wrapper.read_text(encoding="utf-8")),
                encoding="utf-8")

gradle = sdk / "rapt/templates/app-build.gradle"
source = gradle.read_text(encoding="utf-8")
gradle_anchor = "android {\n"
assert source.count(gradle_anchor) == 1, "RAPT app-build.gradle template changed shape"
if "allow-reserved-package-id" not in source:
    package_id_block = (
        "    aaptOptions {\n"
        "        additionalParameters \"--package-id\", \"0x80\", \"--allow-reserved-package-id\"\n"
        "    }\n"
    )
    gradle.write_text(source.replace(gradle_anchor, gradle_anchor + package_id_block, 1), encoding="utf-8")

res = sdk / "rapt/prototype/app/src/main/res"
for directory in (root / "android/res").iterdir():
    shutil.copytree(directory, res / directory.name, dirs_exist_ok=True)
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
