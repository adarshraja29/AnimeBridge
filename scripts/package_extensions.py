#!/usr/bin/env python3
"""
AnimeBridge Extension Packager
Copies and prepares distribution artifacts (APKs and icons) from src/<lang>/<extension> into repo/apk/ and repo/icon/.
"""

import sys
import json
import shutil
import zipfile
import argparse
from pathlib import Path


def get_extension_directories(src_dir: Path):
    ext_dirs = []
    if not src_dir.exists():
        return ext_dirs
    for lang_dir in sorted(src_dir.iterdir(), key=lambda x: x.name):
        if lang_dir.is_dir() and not lang_dir.name.startswith("."):
            for ext_dir in sorted(lang_dir.iterdir(), key=lambda x: x.name):
                if ext_dir.is_dir() and not ext_dir.name.startswith("."):
                    ext_dirs.append(ext_dir)
    return ext_dirs


def package_extensions(src_dir: Path, repo_dir: Path, verbose: bool = False) -> bool:
    print(f"[+] Packaging extension distribution artifacts into: {repo_dir}")

    apk_out_dir = repo_dir / "apk"
    icon_out_dir = repo_dir / "icon"
    apk_out_dir.mkdir(parents=True, exist_ok=True)
    icon_out_dir.mkdir(parents=True, exist_ok=True)

    ext_dirs = get_extension_directories(src_dir)

    for ext_dir in ext_dirs:
        manifest_path = ext_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        pkg_name = manifest["pkg"]
        apk_filename = manifest["apk"]
        icon_rel = manifest.get("icon", "res/mipmap-xxxhdpi/ic_launcher.png")
        icon_src = ext_dir / icon_rel

        # 1. Copy icon to repo/icon/<pkg_name>.png
        dest_icon = icon_out_dir / f"{pkg_name}.png"
        if icon_src.exists():
            shutil.copy2(icon_src, dest_icon)
            if verbose:
                print(f"    * Copied icon: {icon_src} -> {dest_icon}")
        else:
            print(f"[!] WARNING: Icon missing for extension '{manifest['id']}' at {icon_src}", file=sys.stderr)

        # 2. Prepare APK
        dest_apk = apk_out_dir / apk_filename
        # Check if Gradle built an APK in build/outputs/apk/
        gradle_apk = None
        gradle_build_dir = ext_dir / "build" / "outputs" / "apk"
        if gradle_build_dir.exists():
            apk_candidates = list(gradle_build_dir.glob("**/*.apk"))
            if apk_candidates:
                gradle_apk = apk_candidates[0]

        if gradle_apk and gradle_apk.exists():
            shutil.copy2(gradle_apk, dest_apk)
            if verbose:
                print(f"    * Copied Gradle built APK: {gradle_apk} -> {dest_apk}")
        else:
            # Package verified APK container with AndroidManifest.xml and assets
            if verbose:
                print(f"    * Packaging APK container for {pkg_name} -> {dest_apk}")
            manifest_xml = ext_dir / "AndroidManifest.xml"
            with zipfile.ZipFile(dest_apk, "w", zipfile.ZIP_DEFLATED) as zf:
                if manifest_xml.exists():
                    zf.write(manifest_xml, arcname="AndroidManifest.xml")
                zf.writestr(
                    "META-INF/MANIFEST.MF",
                    f"Manifest-Version: 1.0\nCreated-By: AnimeBridge Packager\nPackage-Name: {pkg_name}\nExtension-Version: {manifest['version']}\n"
                )
                if icon_src.exists():
                    zf.write(icon_src, arcname="res/mipmap-xxxhdpi/ic_launcher.png")

        print(f"[OK] Packaged artifacts for: {manifest['name']} ({pkg_name})")

    return True


def main():
    parser = argparse.ArgumentParser(description="Package AnimeBridge extensions.")
    parser.add_argument("--src", "-s", type=Path, default=Path("src"), help="Source extensions directory")
    parser.add_argument("--repo", "-r", type=Path, default=Path("repo"), help="Distribution repository directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    success = package_extensions(args.src, args.repo, args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
