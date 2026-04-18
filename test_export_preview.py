import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from preview_server import generate_preview

SIMPLE_PATCH_YAML = """
name: Test Patch
description: A test tone
tags: []
chain:
  - type: pedal
    model: Tube Screamer
    settings:
      gain: 0.5
      tone: 0.6
      level: 0.8
  - type: amp
    model: Fender Super Reverb
    settings:
      gain: 0.4
      treble: 0.6
      bass: 0.4
"""

def test_export_preview_podgo_returns_json():
    result, error = generate_preview(SIMPLE_PATCH_YAML, "podgo")
    assert error is None
    data = json.loads(result)
    assert data["version"] == 6
    assert data["data"]["meta"]["name"] == "Test Patch"

def test_export_preview_biasfx_returns_json():
    result, error = generate_preview(SIMPLE_PATCH_YAML, "biasfx")
    assert error is None
    data = json.loads(result)
    assert data["patch_name"] == "Test Patch"
    assert len(data["components"]) > 0

def test_export_preview_amplitube_returns_xml():
    result, error = generate_preview(SIMPLE_PATCH_YAML, "amplitube")
    assert error is None
    assert "<AmpliTubePreset" in result
    assert 'name="Test Patch"' in result

def test_export_preview_invalid_yaml_returns_error():
    result, error = generate_preview(": bad yaml ][{ unclosed", "podgo")
    assert result is None
    assert error is not None
    assert len(error) > 0

def test_export_preview_unknown_platform_returns_error():
    result, error = generate_preview(SIMPLE_PATCH_YAML, "nonexistent_daw")
    assert result is None
    assert error is not None
    assert len(error) > 0

def test_export_preview_empty_chain_returns_valid_output():
    yaml_content = """
name: Empty
description: No chain
tags: []
chain: []
"""
    result, error = generate_preview(yaml_content, "podgo")
    assert error is None
    data = json.loads(result)
    assert data["data"]["meta"]["name"] == "Empty"
