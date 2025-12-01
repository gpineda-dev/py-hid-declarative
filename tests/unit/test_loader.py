import pytest
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path
from hid_declarative.loader import load_profile_from_script, LoaderError
from hid_declarative.profile import HIDProfile
from hid_declarative.loader import parse_source_profile_uri
import base64

# Mock the HIDProfile class for isinstance checks
class MockHIDProfile(HIDProfile):
    pass

@pytest.fixture
def mock_path_exists():
    with patch("pathlib.Path.exists") as mock_exists:
        yield mock_exists

@pytest.fixture
def mock_importlib():
    with patch("importlib.util.spec_from_file_location") as mock_spec:
        yield mock_spec

@pytest.fixture
def mock_module_from_spec():
    with patch("importlib.util.module_from_spec") as mock_mod:
        yield mock_mod

def test_load_profile_from_script_invalid_format():
    """Test that a reference without a colon raises LoaderError."""
    with pytest.raises(LoaderError, match="Reference must be in the format"):
        load_profile_from_script("script.py")

def test_load_profile_from_script_file_not_found(mock_path_exists):
    """Test that a non-existent file raises LoaderError."""
    mock_path_exists.return_value = False
    
    with pytest.raises(LoaderError, match="File .* not found"):
        load_profile_from_script("missing.py:profile")

def test_load_profile_from_script_success(mock_path_exists, mock_importlib, mock_module_from_spec):
    """Test successful loading of a HIDProfile from a script."""
    mock_path_exists.return_value = True
    
    # Setup mock module and spec
    mock_spec = MagicMock()
    mock_loader = MagicMock()
    mock_spec.loader = mock_loader
    mock_importlib.return_value = mock_spec
    
    # Create a fake module with a HIDProfile instance
    fake_module = MagicMock()
    expected_profile = MockHIDProfile(name="Test", root=None)
    setattr(fake_module, "my_profile", expected_profile)
    mock_module_from_spec.return_value = fake_module

    result = load_profile_from_script("script.py:my_profile")
    
    assert result is expected_profile
    mock_loader.exec_module.assert_called_once_with(fake_module)
    # Verify sys.path manipulation happened (though it's cleaned up in finally)
    # We can't easily check the intermediate state of sys.path without more complex mocking,
    # but we can ensure the function completed successfully.

def test_load_profile_from_script_variable_not_found(mock_path_exists, mock_importlib, mock_module_from_spec):
    """Test that a missing variable in the module raises LoaderError."""
    mock_path_exists.return_value = True
    
    mock_spec = MagicMock()
    mock_spec.loader = MagicMock()
    mock_importlib.return_value = mock_spec
    
    fake_module = MagicMock()
    # Ensure the variable is NOT on the module
    del fake_module.missing_var 
    # MagicMock creates attributes on access by default, so we need to be careful or let getattr fail naturally
    # However, getattr on a MagicMock returns another MagicMock usually.
    # We need to simulate AttributeError.
    
    # A cleaner way with MagicMock is to use spec=object or configure side_effect for getattr, 
    # but since the code uses getattr(user_mod, var_name), we can just return an empty object
    class EmptyModule:
        pass
    
    mock_module_from_spec.return_value = EmptyModule()

    with pytest.raises(LoaderError, match="Variable 'missing_var' not found"):
        load_profile_from_script("script.py:missing_var")

def test_load_profile_from_script_wrong_type(mock_path_exists, mock_importlib, mock_module_from_spec):
    """Test that a variable of the wrong type raises LoaderError."""
    mock_path_exists.return_value = True
    
    mock_spec = MagicMock()
    mock_spec.loader = MagicMock()
    mock_importlib.return_value = mock_spec
    
    fake_module = MagicMock()
    setattr(fake_module, "not_a_profile", "just a string")
    mock_module_from_spec.return_value = fake_module

    with pytest.raises(LoaderError, match="is not a HIDProfile instance"):
        load_profile_from_script("script.py:not_a_profile")

def test_load_profile_from_script_import_error(mock_path_exists, mock_importlib):
    """Test that errors during module execution are caught."""
    mock_path_exists.return_value = True
    
    mock_spec = MagicMock()
    mock_loader = MagicMock()
    mock_loader.exec_module.side_effect = Exception("Syntax error in script")
    mock_spec.loader = mock_loader
    mock_importlib.return_value = mock_spec

    with pytest.raises(LoaderError, match="Error loading profile: Syntax error in script"):
        load_profile_from_script("script.py:profile")

def test_load_profile_from_script_sys_path_cleanup(mock_path_exists, mock_importlib, mock_module_from_spec):
    """Test that sys.path is cleaned up even if an error occurs."""
    mock_path_exists.return_value = True
    
    # Force an error during loading
    mock_importlib.side_effect = Exception("Boom")
    
    original_sys_path = list(sys.path)
    
    with pytest.raises(LoaderError):
        load_profile_from_script("path/to/script.py:var")
        
    assert sys.path == original_sys_path

def test_parse_source_profile_uri_py_scheme():
    """Test parsing a py:// URI delegates to load_profile_from_script."""
    with patch("hid_declarative.loader.load_profile_from_script") as mock_load:
        mock_profile = MagicMock(spec=HIDProfile)
        mock_load.return_value = mock_profile
        
        uri = "py://path/to/script.py:my_profile"
        result = parse_source_profile_uri(uri)
        
        assert result is mock_profile
        mock_load.assert_called_once_with("path/to/script.py:my_profile")

def test_parse_source_profile_uri_file_scheme():
    """Test parsing a file:// URI returns a Path object."""
    uri = "file://path/to/descriptor.bin"
    result = parse_source_profile_uri(uri)
    assert isinstance(result, Path)
    # Note: urlparse behavior might vary slightly on windows vs posix regarding slashes,
    # but the implementation concatenates netloc and path.
    # file://path/to... -> netloc=path, path=/to... -> path/to...
    assert str(result).replace("\\", "/") == "path/to/descriptor.bin"

def test_parse_source_profile_uri_hex_scheme():
    """Test parsing a hex:// URI returns bytes."""
    # Test standard hex
    uri = "hex://01020304"
    result = parse_source_profile_uri(uri)
    assert result == b'\x01\x02\x03\x04'
    

def test_parse_source_profile_uri_b64_scheme():
    """Test parsing a b64:// URI returns decoded bytes."""
    data = b'\x01\x02\x03\x04'
    encoded = base64.b64encode(data).decode('ascii')
    uri = f"b64://{encoded}"
    
    result = parse_source_profile_uri(uri)
    assert result == data


def test_parse_source_profile_uri_implicit_hex():
    """Test that a string without scheme is treated as hex."""
    uri = "0A0B0C"
    result = parse_source_profile_uri(uri)
    assert result == b'\x0A\x0B\x0C'


def test_parse_source_profile_uri_unknown_scheme():
    """Test that an unknown scheme raises ValueError."""
    uri = "ftp://example.com/file.bin"
    with pytest.raises(ValueError, match="Unknown scheme"):
        parse_source_profile_uri(uri)