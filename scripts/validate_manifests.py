#!/usr/bin/env python3
"""
AnimeBridge Extension Manifest Validator
Validates extension manifests, package names, version boundaries, and file structures under src/<lang>/<extension>.
"""

import sys
import json
import argparse
from pathlib import Path
from PIL import Image
import jsonschema


def get_extension_directories(src_dir: Path):
    """Finds all extension submodules in src/<lang>/<extension>."""
    ext_dirs = []
    if not src_dir.exists():
        return ext_dirs
    for lang_dir in sorted(src_dir.iterdir(), key=lambda x: x.name):
        if lang_dir.is_dir() and not lang_dir.name.startswith("."):
            for ext_dir in sorted(lang_dir.iterdir(), key=lambda x: x.name):
                if ext_dir.is_dir() and not ext_dir.name.startswith("."):
                    ext_dirs.append(ext_dir)
    return ext_dirs


def validate_manifests(src_dir: Path, schema_file: Path, verbose: bool = False) -> bool:
    print(f"[+] Scanning extension manifests in: {src_dir}")

    if not src_dir.exists():
        print(f"[!] ERROR: Source extensions directory does not exist: {src_dir}", file=sys.stderr)
        return False

    if not schema_file.exists():
        print(f"[!] ERROR: Manifest schema file does not exist: {schema_file}", file=sys.stderr)
        return False

    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except Exception as e:
        print(f"[!] ERROR: Failed to load manifest schema: {e}", file=sys.stderr)
        return False

    validator = jsonschema.Draft202012Validator(schema)
    ext_dirs = get_extension_directories(src_dir)

    if not ext_dirs:
        print(f"[!] WARNING: No extension directories found under {src_dir}", file=sys.stderr)
        return False

    seen_ids = set()
    seen_pkgs = set()
    seen_source_ids = set()
    all_passed = True
    validated_count = 0

    for ext_dir in ext_dirs:
        manifest_path = ext_dir / "manifest.json"
        if not manifest_path.exists():
            print(f"[!] ERROR: Extension directory '{ext_dir}' is missing manifest.json", file=sys.stderr)
            all_passed = False
            continue

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[!] ERROR: Malformed JSON in manifest '{manifest_path}':\n{e}", file=sys.stderr)
            all_passed = False
            continue

        # 1. Schema check
        errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
        if errors:
            print(f"[!] ERROR: Schema validation failed for '{ext_dir.name}/manifest.json':", file=sys.stderr)
            for err in errors:
                path = " -> ".join([str(p) for p in err.path]) or "root"
                print(f"    - [{path}]: {err.message}", file=sys.stderr)
            all_passed = False
            continue

        # 2. Identifier checks
        c_id = manifest["id"]
        if c_id in seen_ids:
            print(f"[!] ERROR: Duplicate extension ID: '{c_id}' in {ext_dir}", file=sys.stderr)
            all_passed = False
        seen_ids.add(c_id)

        # 3. Package name check
        pkg = manifest["pkg"]
        if pkg in seen_pkgs:
            print(f"[!] ERROR: Duplicate Android package name: '{pkg}'", file=sys.stderr)
            all_passed = False
        seen_pkgs.add(pkg)

        # 4. Dantotsu LibVersion boundary check
        # Version format: <libVersion>.<extVersion>
        version_str = manifest["version"]
        parts = version_str.split(".")
        if len(parts) < 2:
            print(f"[!] ERROR: Version '{version_str}' must be formatted as <libVersion>.<extVersion>", file=sys.stderr)
            all_passed = False
        else:
            try:
                lib_ver = float(parts[0])
                if lib_ver < 12.0 or lib_ver > 15.0:
                    print(
                        f"[!] ERROR: Extension '{c_id}' libVersion {lib_ver} is outside Dantotsu supported range (12 - 15).",
                        file=sys.stderr
                    )
                    all_passed = False
            except ValueError:
                print(f"[!] ERROR: Invalid numeric libVersion in '{version_str}'", file=sys.stderr)
                all_passed = False

        # 5. Icon file verification
        icon_rel = manifest.get("icon", "res/mipmap-xxxhdpi/ic_launcher.png")
        icon_path = ext_dir / icon_rel
        if not icon_path.exists():
            print(f"[!] ERROR: Extension '{c_id}' declared icon not found: {icon_path}", file=sys.stderr)
            all_passed = False
        else:
            try:
                with Image.open(icon_path) as img:
                    if img.format != "PNG":
                        print(f"[!] ERROR: Icon '{icon_path}' is not a PNG file (format: {img.format})", file=sys.stderr)
                        all_passed = False
                    width, height = img.size
                    if width != height:
                        print(f"[!] WARNING: Icon '{icon_path}' is not square ({width}x{height})", file=sys.stderr)
            except Exception as e:
                print(f"[!] ERROR: Failed to read image '{icon_path}': {e}", file=sys.stderr)
                all_passed = False

        # 6. Source ID uniqueness
        for src in manifest.get("sources", []):
            s_id = src.get("id")
            if s_id in seen_source_ids:
                print(f"[!] ERROR: Duplicate source ID across catalog: {s_id}", file=sys.stderr)
                all_passed = False
            seen_source_ids.add(s_id)

        # 7. AndroidManifest.xml verification
        manifest_xml = ext_dir / "AndroidManifest.xml"
        if not manifest_xml.exists():
            print(f"[!] ERROR: AndroidManifest.xml missing in extension directory: {ext_dir}", file=sys.stderr)
            all_passed = False

        validated_count += 1
        if verbose:
            print(f"    * Extension '{c_id}' (pkg: {pkg}, v{version_str}, sources: {len(manifest.get('sources', []))}) [VALID]")

    if all_passed:
        print(f"[OK] Successfully validated {validated_count} extension manifest(s).")
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Validate AnimeBridge extension manifests.")
    parser.add_argument("--src", "-s", type=Path, default=Path("src"), help="Source extensions directory")
    parser.add_argument("--schema", type=Path, default=Path("src/manifest.schema.json"), help="Manifest schema")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    success = validate_manifests(args.src, args.schema, args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
