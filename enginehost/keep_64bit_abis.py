#!/usr/bin/env python3
"""Keep only arm64-v8a and x86_64 in a packed Ren'Py bundle payload.

Every Enginehost core ships those two ABIs and no others (Droidtop/tracker#646),
and Enginehost's signing job refuses a bundle with any other one
(scripts/check-bundle-conformance.py, Droidtop/tracker#27). RAPT's build still
produces armeabi-v7a (and, on some lines, x86) libraries: the 8.5 bundle 1.0.13-1
carried lib/armeabi-v7a/ and an armeabi-v7a library inside runtime.apk.

Usage: keep_64bit_abis.py <payload-dir>

- lib/<abi>/ folders for any other ABI are moved out of the payload, to
  <payload-dir>/../dropped-abis/, so nothing is deleted and the build log can list them.
- runtime.apk is rewritten without lib/<abi>/ entries for any other ABI, then
  zipaligned (4-byte, page-aligned libraries) with the newest build-tools'
  zipalign, because a rewritten zip loses the alignment Android expects of its
  stored entries.
"""
import os
import shutil
import subprocess
import sys
import zipfile

KEEP = {"arm64-v8a", "x86_64"}


def drop_lib_folders(payload):
    lib = os.path.join(payload, "lib")
    if not os.path.isdir(lib):
        return []
    dropped_root = os.path.join(os.path.dirname(os.path.abspath(payload)), "dropped-abis")
    dropped = []
    for abi in sorted(os.listdir(lib)):
        if abi in KEEP:
            continue
        os.makedirs(dropped_root, exist_ok=True)
        os.replace(os.path.join(lib, abi), os.path.join(dropped_root, abi))
        dropped.append(abi)
    return dropped


def strip_apk(apk):
    rewritten = apk + ".partial"
    dropped = set()
    with zipfile.ZipFile(apk) as source, zipfile.ZipFile(rewritten, "w") as target:
        for info in source.infolist():
            parts = info.filename.split("/")
            if len(parts) > 2 and parts[0] == "lib" and parts[1] not in KEEP:
                dropped.add(parts[1])
                continue
            target.writestr(info, source.read(info.filename), compress_type=info.compress_type)
    if not dropped:
        os.remove(rewritten)
        return []
    aligned = apk + ".aligned"
    subprocess.run([zipalign(), "-f", "-p", "4", rewritten, aligned], check=True)
    os.replace(aligned, apk)
    os.remove(rewritten)
    return sorted(dropped)


def zipalign():
    found = shutil.which("zipalign")
    if found:
        return found
    tools = os.path.join(os.environ.get("ANDROID_HOME", ""), "build-tools")
    versions = sorted(
        (v for v in os.listdir(tools) if os.path.isfile(os.path.join(tools, v, "zipalign"))),
        key=lambda v: [int(p) if p.isdigit() else 0 for p in v.replace("-", ".").split(".")],
    )
    if not versions:
        raise SystemExit("no zipalign under $ANDROID_HOME/build-tools")
    return os.path.join(tools, versions[-1], "zipalign")


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    payload = argv[1]
    folders = drop_lib_folders(payload)
    apk = os.path.join(payload, "runtime.apk")
    entries = strip_apk(apk) if os.path.isfile(apk) else []
    print("dropped lib folders:", ", ".join(folders) or "none")
    print("dropped runtime.apk libraries for:", ", ".join(entries) or "none")


if __name__ == "__main__":
    main(sys.argv)
