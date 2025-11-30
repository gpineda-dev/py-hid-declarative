import os
import pytest
from typer.testing import CliRunner
from pathlib import Path

from hid_declarative.cli import app
from hid_declarative.profile import HIDProfile
from hid_declarative.schema.nodes import Collection
from hid_declarative.spec.tables.generic_desktop import GenericDesktop

runner = CliRunner()

# --- Fixture: Create a temporary user script ---
@pytest.fixture
def profile_script(tmp_path):
    script_content = """
from hid_declarative import HIDProfile, Collection, GenericDesktop

profile = HIDProfile(
    root=Collection(GenericDesktop.PAGE_ID, GenericDesktop.MOUSE, 1),
    name="TestMouse",
    variable_name="test_mouse"
)
"""
    script_file = tmp_path / "my_device.py"
    script_file.write_text(script_content)
    return script_file



# --- Test 1 : Hex Inspection ---
def test_cli_inspect_hex_string():
    # A minimal valid blob (Usage Page + Usage)
    blob_hex = "05010902" 
    
    result = runner.invoke(app, ["inspect", blob_hex])
    
    assert result.exit_code == 0
    assert "UsagePage: 1" in result.stdout
    assert "Usage: 2" in result.stdout
    

# --- Test 3 : JSON Inspection ---
def test_cli_inspect_json_output():
    blob_hex = "05010902"
    
    result = runner.invoke(app, ["inspect", blob_hex, "--json"])
    
    assert result.exit_code == 0
    # The output must be parsable
    import json
    data = json.loads(result.stdout)
    
    assert data["meta"]["hex"] == blob_hex
    assert len(data["structure"]) == 2
    assert data["structure"][0]["tag_name"] == "UsagePage"

# --- Test 4 : JSON Listing ---
# Note: This test requires hidapi to be installed, or mocked.
# For CI integration, we can skip if hidapi is missing.
try:
    import hid
    HIDAPI_AVAILABLE = True
except ImportError:
    HIDAPI_AVAILABLE = False

@pytest.mark.skipif(not HIDAPI_AVAILABLE, reason="hidapi not installed")
def test_cli_list_json():
    result = runner.invoke(app, ["list", "--json"])
    
    # Even if no device, it must return a valid JSON list (empty)
    assert result.exit_code == 0
    import json
    devices = json.loads(result.stdout)
    assert isinstance(devices, list)