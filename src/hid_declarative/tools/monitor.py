from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import os
import select
import sys
import time
from typing import Optional, Generator, Dict, Any, Union

from hid_declarative.runtime.reports import DataReportType, DataBaseReport
from ..runtime.codec import HIDCodec

__doc__ = """
HID Monitor module provides functionality to monitor HID devices in real-time.
It supports reading raw reports from devices and decoding them using a provided HIDCodec.
"""

@dataclass
class ReportEvent:
    """
    Represents a single HID report event, either raw or decoded attached with a timestamp.
    """

    data: Union[bytes, DataReportType]
    timestamp: float = field(default_factory=time.time)

    def is_decoded(self) -> bool:
        return isinstance(self.data, DataBaseReport)    
    
    def is_raw(self) -> bool:
        return isinstance(self.data, bytes)
    
    def hex(self) -> str:
        if self.is_raw():
            return self.data.hex()
        else:
            return ""  # Decoded data does not have a raw hex representation
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "data": self.data.to_dict() if self.is_decoded() else self.data.hex()
        }

class HIDMonitorError(Exception):
    pass


class DeviceBackend(ABC):
    @abstractmethod
    def open(self): ...
    
    @abstractmethod
    def close(self): ...
    
    @abstractmethod
    def read(self, size: int) -> Optional[bytes]: ...

    @abstractmethod
    def write(self, data: bytes) -> int: ...

    @abstractmethod
    def wait_for_data_ready(self, timeout: float) -> bool: ...


class LinuxHidrawBackend(DeviceBackend):
    """
    Backend for Linux hidraw devices using direct file operations and select."""


    def __init__(self, path: str):
        self.path = path
        self._fd: Optional[int] = None

    def open(self):
        try:
            # Open the device file with read-write and non-blocking flags
            self._fd = os.open(self.path, os.O_RDWR | os.O_NONBLOCK)
        except OSError as e:
            if e.errno == 13:
                raise HIDMonitorError(f"Permission denied: {self.path}. Try 'sudo'.")
            raise HIDMonitorError(f"Could not open {self.path}: {e}")

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def read(self, size: int) -> Optional[bytes]:
        if self._fd is None:
            raise HIDMonitorError("Device not opened")
        try:
            return os.read(self._fd, size)
        except BlockingIOError:
            return None # Nothing to read for now
        except OSError:
            return b'' # EOF / Fatal error (unplugged)
        
    def write(self, data: bytes) -> int:
        if self._fd is None:
            raise HIDMonitorError("Device not opened")
        try:
            return os.write(self._fd, data)
        except OSError as e:
            raise HIDMonitorError(f"Write error: {e}")
        
    def wait_for_data_ready(self, timeout: float) -> bool:
        if self._fd is not None:
            rlist, _, _ = select.select([self._fd], [], [], timeout)
            return bool(rlist)
        return False
        


class HidapiBackend(DeviceBackend):
    """
    Backend using the hidapi library for cross-platform HID access.
    """

    def __init__(self, path: str):
        self.path = path
        self.device = None
        try:
            import hid
            self._hid_mod = hid
        except ImportError:
            raise HIDMonitorError("Missing 'hidapi'.")

    def open(self):
        try:
            self.device = self._hid_mod.device()
            encoded_path = self.path.encode('utf-8') if isinstance(self.path, str) else self.path
            self.device.open_path(encoded_path)
            self.device.set_nonblocking(True)
        except Exception as e:
            raise HIDMonitorError(f"hidapi open failed: {e}")

    def close(self):
        if self.device:
            try:
                self.device.close()
            except: pass
            self.device = None

    def read(self, size: int) -> Optional[bytes]:
        if not self.device:
            raise HIDMonitorError("Device not opened")
        try:
            # hidapi returns a list of integers
            data = self.device.read(size)
            if data:
                return bytes(data)
            return None
        except OSError:
            return b'' # Fatal error
        
    def write(self, data: bytes) -> int:
        if not self.device:
            raise HIDMonitorError("Device not opened")
        try:
            return self.device.write(data)
        except OSError as e:
            raise HIDMonitorError(f"Write error: {e}")
        
    def wait_for_data_ready(self, timeout: float) -> bool:
        # hidapi does not support select, so we use polling
        start_time = time.time()
        while time.time() - start_time < timeout:
            data = self.read(1)
            if data is not None:
                return True
            time.sleep(0.01)  # Sleep briefly to avoid busy waiting
        return False

    
class HIDMonitor:
    """
    Monitors an HID device for incoming reports, decoding them if a codec is provided.
    The monitor uses a backend to handle device I/O.
    """

    def __init__(self, path: str, codec: HIDCodec = None, backend: Optional[DeviceBackend] = None):
        self.codec = codec
        self.backend: DeviceBackend

        # Simple Factory: Strategy choice
        if backend is not None:
            self.backend = backend
        elif sys.platform == "linux" and "hidraw" in path:
            self.backend = LinuxHidrawBackend(path)
        else:
            self.backend = HidapiBackend(path)

    def __enter__(self):
        self.backend.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.backend.close()

    def stream(self, poll_interval: float = 0.005, raw_output: bool = False,) -> Generator[ReportEvent, None, None]:
        """Infinite generator of decoded events."""

        if not self.has_codec() and not raw_output:
            raise HIDMonitorError("No codec available for decoding reports.")

        while True:

            self.backend.wait_for_data_ready(timeout=poll_interval)

            try:
                raw_bytes = self.backend.read(64)  # Assuming max report size of 64 bytes
            except OSError:
                break # Can not rely on the device anymore

            if raw_bytes == b'': 
                break # Disconnection detected by the backend

            if raw_bytes:
                current_time = time.time()
                if raw_output:
                    yield ReportEvent(data=raw_bytes, timestamp=current_time)
                    continue

                try:
                    decoded = self.codec.decode(raw_bytes)
                    yield ReportEvent(data=decoded, timestamp=current_time)
                except Exception as e:
                    raise HIDMonitorError(f"Decoding error: {e}")


    def has_codec(self) -> bool:
        return self.codec is not None