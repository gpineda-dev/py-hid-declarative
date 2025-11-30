import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from src.hid_declarative.runtime.codec import HIDCodec
from src.hid_declarative.tools.monitor import ReportEvent
from src.hid_declarative.runtime.reports import DataBaseReport

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.hid_declarative.tools.monitor import (
    HIDMonitor, 
    DeviceBackend, 
    LinuxHidrawBackend, 
    HidapiBackend, 
    HIDMonitorError
)

# --- Mocks ---
# --- Tests for ReportEvent ---

def test_report_event_raw():
    data = b'\xDE\xAD\xBE\xEF'
    event = ReportEvent(data=data)
    
    assert event.is_raw() is True
    assert event.is_decoded() is False
    assert event.hex() == "deadbeef"
    
    d = event.to_dict()
    assert d['data'] == "deadbeef"
    assert isinstance(d['timestamp'], float)

def test_report_event_decoded():
    mock_report = MagicMock(spec=DataBaseReport)
    mock_report.to_dict.return_value = {"foo": "bar"}
    
    event = ReportEvent(data=mock_report)
    
    assert event.is_raw() is False
    assert event.is_decoded() is True
    assert event.hex() == ""
    
    d = event.to_dict()
    assert d['data'] == {"foo": "bar"}

# --- Tests for HIDMonitor ---

def test_monitor_init_explicit_backend():
    mock_backend = MagicMock(spec=DeviceBackend)
    monitor = HIDMonitor(path="dummy", backend=mock_backend)
    assert monitor.backend is mock_backend

def test_monitor_init_linux_hidraw():
    # Mock sys.platform to be linux and ensure LinuxHidrawBackend is selected
    with patch("sys.platform", "linux"):
        with patch("src.hid_declarative.tools.monitor.LinuxHidrawBackend") as MockLinuxBackend:
            monitor = HIDMonitor(path="/dev/hidraw0")
            MockLinuxBackend.assert_called_once_with("/dev/hidraw0")
            assert isinstance(monitor.backend, MagicMock)

def test_monitor_init_fallback_hidapi():
    # Test fallback when not linux or not hidraw path
    with patch("src.hid_declarative.tools.monitor.HidapiBackend") as MockHidapiBackend:
        # Case 1: Not linux
        with patch("sys.platform", "win32"):
            monitor = HIDMonitor(path="/dev/hidraw0")
            MockHidapiBackend.assert_called_with("/dev/hidraw0")
        
        # Case 2: Linux but not hidraw path
        with patch("sys.platform", "linux"):
            monitor = HIDMonitor(path="USB_VID_PID")
            MockHidapiBackend.assert_called_with("USB_VID_PID")

def test_monitor_context_manager():
    mock_backend = MagicMock(spec=DeviceBackend)
    monitor = HIDMonitor(path="dummy", backend=mock_backend)
    
    with monitor as m:
        assert m is monitor
        mock_backend.open.assert_called_once()
    
    mock_backend.close.assert_called_once()

def test_monitor_stream_raw_output():
    mock_backend = MagicMock(spec=DeviceBackend)
    # Simulate one read of data, then an empty bytes (EOF/Disconnect) to stop the loop
    mock_backend.read.side_effect = [b'\x01\x02\x03', b'']
    
    monitor = HIDMonitor(path="dummy", backend=mock_backend)
    
    events = list(monitor.stream(raw_output=True))
    
    assert len(events) == 1
    assert events[0].is_raw()
    assert events[0].data == b'\x01\x02\x03'
    mock_backend.wait_for_data_ready.assert_called()

def test_monitor_stream_decoded_output():
    mock_backend = MagicMock(spec=DeviceBackend)
    mock_backend.read.side_effect = [b'\xAA\xBB', b'']
    
    mock_codec = MagicMock(spec=HIDCodec)
    mock_report = MagicMock(spec=DataBaseReport)
    mock_codec.decode.return_value = mock_report
    
    monitor = HIDMonitor(path="dummy", codec=mock_codec, backend=mock_backend)
    
    events = list(monitor.stream(raw_output=False))
    
    assert len(events) == 1
    mock_codec.decode.assert_called_once_with(b'\xAA\xBB')
    assert events[0].is_decoded()
    assert events[0].data == mock_report

def test_monitor_stream_missing_codec_error():
    mock_backend = MagicMock(spec=DeviceBackend)
    monitor = HIDMonitor(path="dummy", backend=mock_backend) # No codec provided
    
    # Should raise error immediately if raw_output is False and no codec
    with pytest.raises(HIDMonitorError, match="No codec available"):
        next(monitor.stream(raw_output=False))

def test_monitor_stream_decoding_exception():
    mock_backend = MagicMock(spec=DeviceBackend)
    mock_backend.read.return_value = b'\x00'
    
    mock_codec = MagicMock(spec=HIDCodec)
    mock_codec.decode.side_effect = ValueError("Invalid data")
    
    monitor = HIDMonitor(path="dummy", codec=mock_codec, backend=mock_backend)
    
    gen = monitor.stream(raw_output=False)
    
    with pytest.raises(HIDMonitorError, match="Decoding error: Invalid data"):
        next(gen)

def test_monitor_stream_os_error_stops_iteration():
    mock_backend = MagicMock(spec=DeviceBackend)
    # Simulate OSError on read (e.g. device unplugged)
    mock_backend.read.side_effect = OSError("Device lost")
    
    monitor = HIDMonitor(path="dummy", backend=mock_backend)
    
    # The generator should simply stop yielding, not raise the OSError
    events = list(monitor.stream(raw_output=True))
    assert len(events) == 0

def test_monitor_has_codec():
    monitor = HIDMonitor(path="dummy", backend=MagicMock())
    assert monitor.has_codec() is False
    
    monitor.codec = MagicMock()
    assert monitor.has_codec() is True