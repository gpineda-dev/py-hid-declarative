from dataclasses import dataclass
import sys
import os
import glob
import struct
from typing import List, Dict, Optional

__doc__ = """
HID Device module provides classes and methods for discovering and managing HID devices
connected to the system. It supports device enumeration, filtering, and descriptor extraction.
"""

class DeviceError(Exception):
    pass

@dataclass
class DeviceCandidate:
    """Represent a low-level HID device candidate."""
    vid: int
    pid: int
    interface: int
    path: bytes  # System path (e.g., b'/dev/hidraw0')
    hidapi_path: bytes  # hidapi-specific path (eg. 1-2:1.0)
    product_string: str
    manufacturer_string: str

    def to_dict(self, bytes_to_str: bool = True) -> Dict:
        result = {
            "vid": self.vid,
            "pid": self.pid,
            "interface": self.interface,
            "path": self.path.decode('utf-8', errors='replace') if bytes_to_str else self.path,
            "hidapi_path": self.hidapi_path.decode('utf-8', errors='replace') if bytes_to_str else self.hidapi_path,
            "product_string": self.product_string,
            "manufacturer_string": self.manufacturer_string,
            "hex_id": f"{self.vid:04x}:{self.pid:04x}:{self.interface}"
        }
        return result

class HIDDeviceManager:
    """
    Centralizes hardware discovery and access logic.
    Handles the subtleties of composite devices (multiple interfaces).
    """
    
    # IOCTL Constants (Linux)
    HIDIOCGRDESCSIZE = 0x80044801
    HIDIOCGRDESC     = 0x90044802

    def __init__(self):
        try:
            import hid
            self._hid = hid
        except ImportError:
            raise DeviceError("Missing dependency 'hidapi'. Install with pip install 'hid-declarative[hidapi]'")

    def find_devices(self, vid: Optional[int] = None, pid: Optional[int] = None, interface: Optional[int] = None) -> List[DeviceCandidate]:
        """
        Smart search with optional filters.
        """
        candidates = []
        # enumerate(0,0) lists everything
        raw_list = self._hid.enumerate(vid or 0, pid or 0)
        
        for d in raw_list:
            # Interface filter (if requested)
            if interface is not None and d['interface_number'] != interface:
                continue
            
            raw_path = d['path']
            resolved_path = raw_path
            
            # If the path does not look like /dev/, try to resolve it via sysfs
            if sys.platform == "linux" and not raw_path.startswith(b'/dev'):
                resolved_path = self._resolve_linux_hidraw(raw_path)
            
            candidates.append(DeviceCandidate(
                vid=d['vendor_id'],
                pid=d['product_id'],
                interface=d['interface_number'],
                path=resolved_path,
                hidapi_path=raw_path,
                product_string=d['product_string'],
                manufacturer_string=d['manufacturer_string']
            ))
            
        return candidates

    def dump_descriptor_from_path(self, path: bytes) -> bytes:
        """
        Extracts the binary descriptor via IOCTL (Linux) from a path.
        """
        if sys.platform != "linux":
            raise DeviceError("Dump is currently Linux-only via hidraw.")
            
        try:
            import fcntl
            # os.open accepts bytes paths on Linux
            fd = os.open(path, os.O_RDONLY)
            try:
                # A. Size
                size_buffer = struct.pack('I', 0)
                size_res = fcntl.ioctl(fd, self.HIDIOCGRDESCSIZE, size_buffer)
                desc_size = struct.unpack('I', size_res)[0]

                if desc_size == 0:
                    raise DeviceError("Descriptor size is 0.")

                # B. Content (Mutable Buffer)
                buf_size = 4096 + 4
                buffer = bytearray(buf_size)
                struct.pack_into('I', buffer, 0, desc_size)
                
                fcntl.ioctl(fd, self.HIDIOCGRDESC, buffer, True)
                return bytes(buffer[4 : 4 + desc_size])

            finally:
                os.close(fd)

        except OSError as e:
            path_str = path.decode(errors='replace')
            if e.errno == 13:
                raise DeviceError(f"Permission denied: {path_str}. Try 'sudo'.")
            raise DeviceError(f"IO Error on {path_str}: {e}")
        

    def _resolve_linux_hidraw(self, bus_path: bytes) -> bytes:
        """
        Attempts to find the /dev/hidrawN node corresponding to a USB bus path (e.g., 1-2:1.1).
        Looks into /sys/class/hidraw/.
        """
        try:
            bus_str = bus_path.decode('utf-8')
            # Scan all system hidraw
            for sys_path in glob.glob("/sys/class/hidraw/hidraw*"):
                # sys_path ex: /sys/class/hidraw/hidraw0
                # Its 'device' link points to the USB bus
                try:
                    # realpath resolves the symbolic link
                    # ex: .../devices/pci0000:00/.../1-2:1.1/hidraw/hidraw0
                    real_device_path = os.path.realpath(os.path.join(sys_path, "device"))
                    
                    # If the bus identifier is in the real path, we found it!
                    if bus_str in real_device_path:
                        dev_name = os.path.basename(sys_path) # hidraw0
                        return f"/dev/{dev_name}".encode('utf-8')
                except OSError:
                    continue
        except Exception:
            pass # If it fails, return the original path
            
        return bus_path