from unittest.mock import MagicMock, patch

import pytest
import typer
from hid_declarative.cli.utils import resolve_device_path
from hid_declarative.tools.device import DeviceError
from hid_declarative.utils import DeviceTarget


def test_resolve_device_path_direct_path():
    """Verifies that if a path is provided in the target, it is returned directly."""
    target = DeviceTarget(path="/dev/hidraw0")
    # Should not instantiate HIDDeviceManager
    with patch("hid_declarative.cli.utils.HIDDeviceManager") as mock_manager:
        result = resolve_device_path(target)
        assert result == "/dev/hidraw0"
        mock_manager.assert_not_called()

def test_resolve_device_path_missing_vid():
    """Verifies that if no path and no VID are provided, it exits."""
    target = DeviceTarget(path=None, vid=None)
    with pytest.raises(typer.Exit) as excinfo:
        resolve_device_path(target)
    assert excinfo.value.exit_code == 1

@patch("hid_declarative.cli.utils.HIDDeviceManager")
def test_resolve_device_path_not_found(mock_manager_cls):
    """Verifies that if no devices are found, it exits."""
    mock_instance = mock_manager_cls.return_value
    mock_instance.find_devices.return_value = []
    
    target = DeviceTarget(vid=0x1234, pid=0x5678)
    
    with pytest.raises(typer.Exit) as excinfo:
        resolve_device_path(target)
    assert excinfo.value.exit_code == 1

@patch("hid_declarative.cli.utils.HIDDeviceManager")
def test_resolve_device_path_ambiguous(mock_manager_cls):
    """Verifies that if multiple devices are found, it exits."""
    mock_instance = mock_manager_cls.return_value
    dev1 = MagicMock(interface=0, path=b"/dev/hidraw1")
    dev2 = MagicMock(interface=1, path=b"/dev/hidraw2")
    mock_instance.find_devices.return_value = [dev1, dev2]
    
    target = DeviceTarget(vid=0x1234, pid=0x5678)
    
    with pytest.raises(typer.Exit) as excinfo:
        resolve_device_path(target)
    assert excinfo.value.exit_code == 1

@patch("hid_declarative.cli.utils.HIDDeviceManager")
def test_resolve_device_path_success(mock_manager_cls):
    """Verifies that if exactly one device is found, its path is returned."""
    mock_instance = mock_manager_cls.return_value
    dev = MagicMock()
    dev.path = b"/dev/hidraw_found"
    dev.product_string = "Test Device"
    mock_instance.find_devices.return_value = [dev]
    
    target = DeviceTarget(vid=0x1234, pid=0x5678)
    
    result = resolve_device_path(target)
    assert result == "/dev/hidraw_found"
    mock_instance.find_devices.assert_called_with(0x1234, 0x5678, None)

@patch("hid_declarative.cli.utils.HIDDeviceManager")
def test_resolve_device_path_discovery_error(mock_manager_cls):
    """Verifies that DeviceError during discovery causes an exit."""
    mock_instance = mock_manager_cls.return_value
    mock_instance.find_devices.side_effect = DeviceError("Access denied")
    
    target = DeviceTarget(vid=0x1234)
    
    with pytest.raises(typer.Exit) as excinfo:
        resolve_device_path(target)
    assert excinfo.value.exit_code == 1