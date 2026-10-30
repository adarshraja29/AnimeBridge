"""
Unit tests for extension manifest schema, Dantotsu libVersion boundaries, and package constraints.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from scripts.validate_manifests import validate_manifests, get_extension_directories


REPO_ROOT = Path(__file__).parent.parent
MANIFEST_SCHEMA_PATH = REPO_ROOT / "src" / "manifest.schema.json"
SRC_DIR = REPO_ROOT / "src"


@pytest.fixture
def manifest_schema():
    with open(MANIFEST_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_manifest_schema_is_valid(manifest_schema):
    """Ensure src/manifest.schema.json is a valid Draft 2020-12 schema."""
    jsonschema.Draft202012Validator.check_schema(manifest_schema)


def test_openmovies_manifest_valid(manifest_schema):
    """Ensure src/en/openmovies/manifest.json complies with schema and Dantotsu constraints."""
    openmovies_manifest = SRC_DIR / "en" / "openmovies" / "manifest.json"
    with open(openmovies_manifest, "r", encoding="utf-8") as f:
        data = json.load(f)

    validator = jsonschema.Draft202012Validator(manifest_schema)
    errors = list(validator.iter_errors(data))
    assert not errors, f"Manifest schema errors: {[e.message for e in errors]}"

    # Verify libVersion boundary
    lib_ver = float(data["version"].split(".")[0])
    assert 12.0 <= lib_ver <= 15.0, f"libVersion {lib_ver} must be between 12 and 15"

    # Verify package name convention
    assert data["pkg"].startswith("eu.kanade.tachiyomi.animeextension.en.")


def test_validator_script_succeeds_on_current_src():
    """Ensure validate_manifests() succeeds on repository src/ directory."""
    assert validate_manifests(SRC_DIR, MANIFEST_SCHEMA_PATH, verbose=False) is True


def test_manifest_rejects_out_of_bounds_libversion(manifest_schema):
    """Ensure versions outside 12-15 fail schema regex pattern ^(1[2-5])\\.[0-9]+$."""
    validator = jsonschema.Draft202012Validator(manifest_schema)

    # Test version 10.1 (below minimum 12)
    invalid_manifest = {
        "id": "test",
        "name": "Test",
        "pkg": "eu.kanade.tachiyomi.animeextension.en.test",
        "version": "10.1",
        "code": 1,
        "lang": "en",
        "nsfw": 0,
        "class": "eu.kanade.tachiyomi.animeextension.en.test.Test",
        "sources": [{"id": 1, "name": "Test", "lang": "en", "baseUrl": "https://example.org"}],
        "capabilities": ["search"],
        "apk": "test.apk",
        "icon": "icon.png"
    }
    errors = list(validator.iter_errors(invalid_manifest))
    assert any("version" in str(e.path) for e in errors)

    # Test version 18.0 (above maximum 15)
    invalid_manifest["version"] = "18.0"
    errors = list(validator.iter_errors(invalid_manifest))
    assert any("version" in str(e.path) for e in errors)


def test_manifest_rejects_invalid_pkg_format(manifest_schema):
    """Ensure packages not matching eu.kanade.tachiyomi.animeextension.<lang>.<id> fail."""
    validator = jsonschema.Draft202012Validator(manifest_schema)
    invalid_manifest = {
        "id": "test",
        "name": "Test",
        "pkg": "com.random.package.test",
        "version": "14.1",
        "code": 1,
        "lang": "en",
        "nsfw": 0,
        "class": "eu.kanade.tachiyomi.animeextension.en.test.Test",
        "sources": [{"id": 1, "name": "Test", "lang": "en", "baseUrl": "https://example.org"}],
        "capabilities": ["search"],
        "apk": "test.apk",
        "icon": "icon.png"
    }
    errors = list(validator.iter_errors(invalid_manifest))
    assert any("pkg" in str(e.path) for e in errors)
