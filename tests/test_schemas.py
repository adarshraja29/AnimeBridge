"""
Unit tests for YAML/JSON parsing and site configuration schema validation.
"""

import json
from pathlib import Path
import pytest
import yaml
import jsonschema


REPO_ROOT = Path(__file__).parent.parent
SITES_SCHEMA_PATH = REPO_ROOT / "config" / "schema.json"
SITES_YAML_PATH = REPO_ROOT / "config" / "sites.yaml"
SITES_EXAMPLE_PATH = REPO_ROOT / "config" / "sites.example.yaml"


@pytest.fixture
def schema():
    with open(SITES_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_schema_itself_is_valid_json_schema(schema):
    """Ensure config/schema.json is a valid Draft 2020-12 schema."""
    jsonschema.Draft202012Validator.check_schema(schema)


def test_sites_yaml_valid(schema):
    """Ensure active config/sites.yaml validates cleanly against the schema."""
    with open(SITES_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    assert not errors, f"sites.yaml schema errors: {[e.message for e in errors]}"


def test_sites_example_yaml_valid(schema):
    """Ensure config/sites.example.yaml validates cleanly against the schema."""
    with open(SITES_EXAMPLE_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    assert not errors, f"sites.example.yaml schema errors: {[e.message for e in errors]}"


def test_schema_rejects_missing_required_fields(schema):
    """Ensure validation fails if required fields like id or homepage are missing."""
    invalid_data = {
        "version": "1.0",
        "sites": [
            {
                "id": "bad-site",
                # missing homepage, connector_id, enabled, etc.
            }
        ]
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(invalid_data))
    assert len(errors) > 0


def test_schema_rejects_invalid_url(schema):
    """Ensure invalid homepage URLs (non-HTTP/HTTPS) fail validation."""
    invalid_data = {
        "version": "1.0",
        "sites": [
            {
                "id": "bad-url-site",
                "name": "Bad URL Site",
                "homepage": "not-a-valid-url",
                "connector_id": "badconnector",
                "enabled": True,
                "authorization": {
                    "type": "open_api",
                    "notes": "Testing URL validation rejection"
                },
                "capabilities": ["search"],
                "language": {"code": "en", "name": "English"},
                "connector_version": "14.1",
                "status": "active"
            }
        ]
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(invalid_data))
    assert any("homepage" in str(e.path) for e in errors)


def test_schema_rejects_invalid_capability(schema):
    """Ensure undeclared capability enums are rejected."""
    invalid_data = {
        "version": "1.0",
        "sites": [
            {
                "id": "bad-cap-site",
                "name": "Bad Cap Site",
                "homepage": "https://example.org",
                "connector_id": "test",
                "enabled": True,
                "authorization": {
                    "type": "open_api",
                    "notes": "Testing capability rejection"
                },
                "capabilities": ["non_existent_capability"],
                "language": {"code": "en", "name": "English"},
                "connector_version": "14.1",
                "status": "active"
            }
        ]
    }
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(invalid_data))
    assert len(errors) > 0
