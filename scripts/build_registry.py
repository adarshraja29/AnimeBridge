#!/usr/bin/env python3
"""
AnimeBridge Repository Registry Generator
Compiles index.min.json, index.json, and repo.json deterministically after rigorous validation.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from validate_sites import validate_sites
from validate_manifests import validate_manifests, get_extension_directories
from package_extensions import package_extensions


def build_registry(
    sites_file: Path,
    sites_schema: Path,
    src_dir: Path,
    manifest_schema: Path,
    repo_dir: Path,
    verbose: bool = False
) -> bool:
    print("=" * 72)
    print("AnimeBridge Deterministic Repository Registry Generator")
    print("=" * 72)

    # STEP 1: Validate site configuration
    print("\n[Stage 1/4] Validating Site Configuration...")
    if not validate_sites(sites_file, sites_schema, src_dir, verbose=verbose):
        print("[!] FATAL: Site configuration validation failed. Registry generation aborted.", file=sys.stderr)
        return False

    # STEP 2: Validate extension manifests
    print("\n[Stage 2/4] Validating Extension Manifests...")
    if not validate_manifests(src_dir, manifest_schema, verbose=verbose):
        print("[!] FATAL: Extension manifest validation failed. Registry generation aborted.", file=sys.stderr)
        return False

    # STEP 3: Package artifacts
    print("\n[Stage 3/4] Packaging Extension Artifacts...")
    if not package_extensions(src_dir, repo_dir, verbose=verbose):
        print("[!] FATAL: Extension artifact packaging failed. Registry generation aborted.", file=sys.stderr)
        return False

    # STEP 4: Build deterministic index
    print("\n[Stage 4/4] Generating Deterministic Repository Registry...")
    registry_items: List[Dict[str, Any]] = []

    # Read enabled sites
    with open(sites_file, "r", encoding="utf-8") as f:
        sites_data = yaml.safe_load(f)

    enabled_connector_ids = {
        s["connector_id"] for s in sites_data.get("sites", []) if s.get("enabled", False)
    }

    ext_dirs = get_extension_directories(src_dir)

    for ext_dir in ext_dirs:
        manifest_path = ext_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        c_id = manifest["id"]
        if c_id not in enabled_connector_ids:
            if verbose:
                print(f"    - Skipping extension '{c_id}' (not enabled in sites configuration)")
            continue

        # Verify APK and Icon are present in repo
        apk_path = repo_dir / "apk" / manifest["apk"]
        icon_path = repo_dir / "icon" / f"{manifest['pkg']}.png"

        if not apk_path.exists():
            print(f"[!] ERROR: Target APK missing from repository directory: {apk_path}", file=sys.stderr)
            return False

        if not icon_path.exists():
            print(f"[!] ERROR: Target Icon missing from repository directory: {icon_path}", file=sys.stderr)
            return False

        # Format item according to Dantotsu ExtensionJsonObject
        item = {
            "name": f"Aniyomi: {manifest['name']}",
            "pkg": manifest["pkg"],
            "apk": manifest["apk"],
            "lang": manifest["lang"],
            "code": int(manifest["code"]),
            "version": str(manifest["version"]),
            "nsfw": int(manifest["nsfw"]),
            "hasReadme": int(manifest.get("hasReadme", 0)),
            "hasChangelog": int(manifest.get("hasChangelog", 0)),
            "sources": [
                {
                    "id": int(src["id"]),
                    "name": str(src["name"]),
                    "lang": str(src["lang"]),
                    "baseUrl": str(src["baseUrl"])
                }
                for src in sorted(manifest.get("sources", []), key=lambda s: s["id"])
            ]
        }
        registry_items.append(item)

    # Sort deterministically by package name
    registry_items.sort(key=lambda x: x["pkg"])

    # Output paths
    index_min_path = repo_dir / "index.min.json"
    index_json_path = repo_dir / "index.json"
    repo_meta_path = repo_dir / "repo.json"

    # Write index.min.json (compact, sorted keys)
    with open(index_min_path, "w", encoding="utf-8") as f:
        json.dump(registry_items, f, separators=(",", ":"), sort_keys=True)

    # Write index.json (pretty printed)
    with open(index_json_path, "w", encoding="utf-8") as f:
        json.dump(registry_items, f, indent=2, sort_keys=True)

    # Write repo.json
    repo_meta = {
        "meta": {
            "name": "AnimeBridge",
            "shortName": "AnimeBridge",
            "website": "https://github.com/animebridge/animebridge"
        }
    }
    with open(repo_meta_path, "w", encoding="utf-8") as f:
        json.dump(repo_meta, f, indent=2, sort_keys=True)

    print("\n" + "-" * 72)
    print(f"[SUCCESS] Registry generation complete!")
    print(f"  - Indexed Extensions: {len(registry_items)}")
    print(f"  - Output Index Min:   {index_min_path} ({index_min_path.stat().st_size} bytes)")
    print(f"  - Output Index Form:  {index_json_path} ({index_json_path.stat().st_size} bytes)")
    print(f"  - Output Repo Meta:   {repo_meta_path}")
    print("-" * 72)
    return True


def main():
    parser = argparse.ArgumentParser(description="Build AnimeBridge repository index files.")
    parser.add_argument("--sites", type=Path, default=Path("config/sites.yaml"), help="Sites configuration file")
    parser.add_argument("--sites-schema", type=Path, default=Path("config/schema.json"), help="Sites schema")
    parser.add_argument("--src", type=Path, default=Path("src"), help="Source directory containing extension modules")
    parser.add_argument("--manifest-schema", type=Path, default=Path("src/manifest.schema.json"), help="Manifest schema")
    parser.add_argument("--repo", type=Path, default=Path("repo"), help="Distribution repository directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    success = build_registry(
        args.sites,
        args.sites_schema,
        args.src,
        args.manifest_schema,
        args.repo,
        args.verbose
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
