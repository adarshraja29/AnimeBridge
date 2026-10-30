"""
Unit tests for deterministic repository registry generation and Dantotsu index validation.
"""

import json
import hashlib
from pathlib import Path
import pytest

from scripts.build_registry import build_registry


REPO_ROOT = Path(__file__).parent.parent
SITES_YAML = REPO_ROOT / "config" / "sites.yaml"
SITES_SCHEMA = REPO_ROOT / "config" / "schema.json"
SRC_DIR = REPO_ROOT / "src"
MANIFEST_SCHEMA = REPO_ROOT / "src" / "manifest.schema.json"
REPO_DIR = REPO_ROOT / "repo"


def sha256_of_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def test_registry_generation_succeeds():
    """Ensure build_registry completes successfully."""
    success = build_registry(
        sites_file=SITES_YAML,
        sites_schema=SITES_SCHEMA,
        src_dir=SRC_DIR,
        manifest_schema=MANIFEST_SCHEMA,
        repo_dir=REPO_DIR,
        verbose=False
    )
    assert success is True


def test_registry_determinism(tmp_path):
    """Ensure building registry twice results in byte-for-byte identical output."""
    out_a = tmp_path / "run_a"
    out_b = tmp_path / "run_b"

    build_registry(SITES_YAML, SITES_SCHEMA, SRC_DIR, MANIFEST_SCHEMA, out_a, verbose=False)
    build_registry(SITES_YAML, SITES_SCHEMA, SRC_DIR, MANIFEST_SCHEMA, out_b, verbose=False)

    hash_a = sha256_of_file(out_a / "index.min.json")
    hash_b = sha256_of_file(out_b / "index.min.json")
    assert hash_a == hash_b, "index.min.json must be deterministic"


def test_index_min_json_structure():
    """Verify index.min.json contains all required Dantotsu ExtensionJsonObject fields."""
    index_min_file = REPO_DIR / "index.min.json"
    assert index_min_file.exists()

    with open(index_min_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    assert isinstance(items, list)
    assert len(items) >= 1

    item = items[0]
    required_keys = [
        "name",
        "pkg",
        "apk",
        "lang",
        "code",
        "version",
        "nsfw",
        "hasReadme",
        "hasChangelog",
        "sources"
    ]
    for k in required_keys:
        assert k in item, f"Missing required key '{k}' in index.min.json item"

    # Name must have 'Aniyomi: ' prefix
    assert item["name"].startswith("Aniyomi: ")

    # Sources must have id, name, lang, baseUrl
    assert len(item["sources"]) >= 1
    src = item["sources"][0]
    assert "id" in src and "name" in src and "lang" in src and "baseUrl" in src


def test_apk_and_icon_artifacts_exist():
    """Verify that every APK and icon referenced in index.min.json exists on disk."""
    index_min_file = REPO_DIR / "index.min.json"
    with open(index_min_file, "r", encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        apk_file = REPO_DIR / "apk" / item["apk"]
        assert apk_file.exists(), f"Referenced APK file missing: {apk_file}"

        icon_file = REPO_DIR / "icon" / f"{item['pkg']}.png"
        assert icon_file.exists(), f"Referenced Icon file missing: {icon_file}"
