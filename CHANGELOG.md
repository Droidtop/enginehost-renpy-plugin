# Changelog

All notable changes to this repository's wrapper are documented here,
grouped by kind and in plain language. Only wrapper work is listed: the
engine is upstream Ren'Py, and its history stays on the engine branches.
The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The wrapper's
declared version is 0.1, the line before the first stable build, so
everything released so far is listed under that one heading.

## [Unreleased]

### Fixed
- Ren'Py games load faster from a folder on the console's storage (Droidtop/tracker#853): of "Loading script"'s 52.8 s on the RP5, 36.6 s were 3,490 stats, about 10.5 ms each through the sandbox broker and the SD card. Until the end of that phase, the path checks Ren'Py's own folder scan already answered (a `.rpy` or `_ren.py` beside each `.rpyc`, the same `.rpyc` asked about twice) are answered from that scan instead of the card. Anything Ren'Py writes, renames or removes drops what is kept for its folder (patch 0011; 1.0.18, 7.3's 0.9.17, 7.8's 1.0.20).
- A game with Live2D models (Love & Sex: Second Base) crashed the Ren'Py 7.5+ and 8.x cores with a segfault when the Live2D Cubism Core library was not present: the loader remembered a failed load as a success, so the second attempt called a NULL function. A failed load now stays an error the game can show, and 8.5 no longer swallows it.

### Changed
- The build's signing job is pinned to the Enginehost tooling that refuses a build whose sources changed under an already published declared version (Droidtop/tracker#126). A revision of the plugin's code now has to bump `pluginVersion` in `enginehost/bundle-metadata.json`, the one place the version is declared.
- The version baked into the APK (Ren'Py's `config.version` and `android.json`) is read from `enginehost/bundle-metadata.json` too, instead of a second copy in `enginehost/runtime.json` that had drifted from it.

## [0.1] - 2026-09-03

### Added
- Initial wrapper changeset: enginehost metadata and integration hooks, the plugin build workflow, and the repository signing key document.
- Build support for the Python 2 lines (Ren'Py 7.3 to 7.6): the JDK each line's Gradle needs, the older project-settings filename those RAPTs read, and 7.3's onCreate, which opens without the line the patch anchors to.
- A slim SDK carrying only the platform, build-tools and NDK versions the older lines' Android Gradle plugins can read.
- The Gradle project and signing property files that older RAPTs expect their installer to write, laid down by the build.
- A virtual display and silent audio for the older lines' builds, since Ren'Py 7.3's launcher opens a window to dump its settings.
- A log line reporting the save path each launch hands over.
- Licence files: an MIT licence for the wrapper and a third-party notice indexing Ren'Py's own licence.
- A publish step that tells the plugin catalog a release is out, so the catalog offers it at once instead of on its next scheduled rebuild.

### Changed
- Re-certified the repository's signing key under the new enginehost root.
- Install each line's SDK parts with the runner's JDK, through the shell, before switching to the JDK the line builds with.
- Ren'Py 7.3's APK-expansion dependency is gone, since nothing serves it any more and expansion APKs are never built; older RAPTs also ask Maven Central for their libraries.
- Ren'Py 7.3's RAPT builds with the Gradle and Android Gradle plugin that 7.4 ships, because the 2018 pair could only build resources at the package id the host app reserves.
- An older line's release build no longer fails on lint findings in Ren'Py's own Android project.
- Release tags point at the commit that built the bundle, and the testing channel rolls forward like unstable.
- Bundles are signed in enginehost's pinned reusable signing job instead of beside the build, which no longer holds the signing key; workflow actions are pinned by commit.
- Re-pinned the enginehost workflow reference after enginehost's history was rewritten.
- Re-pinned the signing job and wired its channel input, and the publish and unstable jobs now validate artifact SHAs.
- Bundles are numbered from the repository's release count instead of the CI run number, so a rerun cannot repeat a version.

### Fixed
- The bare-onCreate fallback now escapes its newline instead of writing it literally.
- The SDK path is written without a stray line break.
- The Gradle property files are written with echo; the printf format had picked up literal line breaks.
- Extension-level entries that sdkmanager now writes into package.xml are stripped, since the 2018 Android Gradle plugin rejects the whole platform over them.
- Ren'Py 7.3's RAPT compiles against API 30, where the resource-attachment API it needs is available.
- The version string that decides whether RAPT re-unpacks the engine now moves with the engine build instead of staying at the plugin version, so devices pick up engine changes instead of running their first extraction forever.
- Each Ren'Py line unpacks its engine into its own directory, created only when that line is launched, so lines no longer re-extract over each other or run another line's engine.
