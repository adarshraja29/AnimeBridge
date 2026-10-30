#!/usr/bin/env python3
"""
AnimeBridge Site Configuration Validator
Validates config/sites.yaml against config/schema.json and checks structural integrity against src/ extension modules.
"""

import sys
import json
import argparse
from pathlib import Path
from urllib.parse import urlparse
import yaml
import jsonschema


def find_extension_module(src_dir: Path, connector_id: str) -> bool:
    """Finds an extension module matching connector_id across all language directories."""
    if not src_dir.exists():
        return False
    for lang_dir in src_dir.iterdir():
        if lang_dir.is_dir() and not lang_dir.name.startswith("."):
            ext_dir = lang_dir / connector_id
            if ext_dir.exists() and ext_dir.is_dir():
                return True
    return False


def validate_sites(config_file: Path, schema_file: Path, src_dir: Path, verbose: bool = False) -> bool:
    print(f"[+] Validating site configuration: {config_file}")

    if not config_file.exists():
        print(f"[!] ERROR: Configuration file does not exist: {config_file}", file=sys.stderr)
        return False

    if not schema_file.exists():
        print(f"[!] ERROR: Schema file does not exist: {schema_file}", file=sys.stderr)
        return False

    # 1. Parse YAML
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"[!] ERROR: YAML Syntax Error in {config_file}:\n{e}", file=sys.stderr)
        return False

    # 2. Parse Schema
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[!] ERROR: Schema JSON Syntax Error in {schema_file}:\n{e}", file=sys.stderr)
        return False

    # 3. JSON Schema Validation
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        print(f"[!] ERROR: Schema validation failed with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            path = " -> ".join([str(p) for p in err.path]) or "root"
            print(f"    - At [{path}]: {err.message}", file=sys.stderr)
        return False

    # 4. Semantic Integrity Checks
    sites = data.get("sites", [])
    seen_ids = set()
    seen_homepages = set()
    all_passed = True

    for idx, site in enumerate(sites):
        site_id = site.get("id", f"<index-{idx}>")
        site_name = site.get("name", "Unknown")

        # Check unique IDs
        if site_id in seen_ids:
            print(f"[!] ERROR: Duplicate site ID detected: '{site_id}'", file=sys.stderr)
            all_passed = False
        seen_ids.add(site_id)

        # Check valid URL format
        homepage = site.get("homepage", "")
        parsed = urlparse(homepage)
        if not parsed.scheme or not parsed.netloc:
            print(f"[!] ERROR: Invalid homepage URL '{homepage}' in site '{site_id}'", file=sys.stderr)
            all_passed = False

        if homepage in seen_homepages:
            print(f"[!] WARNING: Multiple sites share homepage '{homepage}'", file=sys.stderr)
        seen_homepages.add(homepage)

        # Check extension module reference under src/<lang>/<connector_id>
        connector_id = site.get("connector_id")
        if site.get("enabled", False) and not find_extension_module(src_dir, connector_id):
            print(
                f"[!] ERROR: Site '{site_id}' is enabled but corresponding extension module does not exist under {src_dir}/*/{connector_id}",
                file=sys.stderr
            )
            all_passed = False

        if verbose:
            print(f"    * Site '{site_id}' ({site_name}) - status: {site.get('status')}, enabled: {site.get('enabled')}")

    if all_passed:
        print(f"[OK] Successfully validated {len(sites)} site entries in {config_file.name}.")
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Validate AnimeBridge site configurations against schema.")
    parser.add_argument("--file", "-f", type=Path, default=Path("config/sites.yaml"), help="Path to sites.yaml")
    parser.add_argument("--schema", "-s", type=Path, default=Path("config/schema.json"), help="Path to schema.json")
    parser.add_argument("--src", type=Path, default=Path("src"), help="Source directory containing extension modules")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    success = validate_sites(args.file, args.schema, args.src, args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
