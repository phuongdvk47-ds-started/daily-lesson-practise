"""Tests for schema validation — verify all schemas are valid JSON Schema."""
import json
import sys
from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


class TestSchemaFiles:
    """Verify all schema files exist and are valid JSON."""

    EXPECTED_SCHEMAS = [
        "request.schema.json",
        "canonical-source.schema.json",
        "level-assessment.schema.json",
        "lesson-manifest.schema.json",
        "pipeline-state.schema.json",
        "qa-report.schema.json",
        "execution-contract.schema.json",
        "routing-decision.schema.json",
        "execution-metadata.schema.json",
    ]

    def test_all_schemas_exist(self):
        for name in self.EXPECTED_SCHEMAS:
            path = SCHEMAS_DIR / name
            assert path.exists(), f"Schema not found: {name}"

    def test_all_schemas_valid_json(self):
        for name in self.EXPECTED_SCHEMAS:
            path = SCHEMAS_DIR / name
            data = json.loads(path.read_text(encoding="utf-8"))
            assert isinstance(data, dict), f"{name} is not a JSON object"

    def test_all_schemas_have_type(self):
        for name in self.EXPECTED_SCHEMAS:
            path = SCHEMAS_DIR / name
            data = json.loads(path.read_text(encoding="utf-8"))
            assert "type" in data or "$schema" in data, \
                f"{name} missing 'type' or '$schema'"

    def test_all_schemas_have_properties_or_items(self):
        for name in self.EXPECTED_SCHEMAS:
            path = SCHEMAS_DIR / name
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("type") == "object":
                assert "properties" in data, f"{name} object has no properties"

    def test_schema_count(self):
        """Exactly 9 schemas expected."""
        assert len(self.EXPECTED_SCHEMAS) == 9
        schema_files = list(SCHEMAS_DIR.glob("*.schema.json"))
        assert len(schema_files) == 9, f"Found {len(schema_files)} schemas"
