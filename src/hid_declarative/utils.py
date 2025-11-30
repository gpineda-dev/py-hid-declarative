from pathlib import Path
import re
import urllib.parse
from typing import Optional, NamedTuple, Union


class DeviceTarget(NamedTuple):
    """Normalized result of a connection request."""
    vid: Optional[int] = None
    pid: Optional[int] = None
    interface: Optional[int] = None
    path: Optional[str] = None


def parse_hex_int(value: Union[str, int, None]) -> Optional[int]:
    """
    Converts "0x1234", "1234" (hex) or 1234 (int) to an integer.
    Utility helper for user scripts.
    """
    if value is None: return None
    if isinstance(value, int): return value
    
    val_str = value.strip()
    if not val_str: return None

    try:
        # Supports 0x... and ... (treated as hex by default for USB)
        if val_str.lower().startswith("0x"):
            return int(val_str, 16)
        return int(val_str, 16)
    except ValueError:
        # Fallback base 10
        try:
            return int(val_str)
        except ValueError:
            raise ValueError(f"Invalid hex value: {val_str}")
        
        
def parse_device_uri(uri: str) -> DeviceTarget:
    """
    Parses a URI-style connection string.
    
    Supported formats:
      - id://VID:PID[:IF]       (ex: id://046d:c077)
      - path:///dev/hidraw0     (System path)
      - /dev/hidraw0            (Implicit path)
      - VID:PID                 (Implicit ID, legacy)
    """
    # 1. Scheme detection via urllib
    # Tip: if no "://", urlparse does not fill 'scheme' correctly for our cases
    if "://" in uri:
        parsed = urllib.parse.urlparse(uri)
        scheme = parsed.scheme
        body = parsed.netloc + parsed.path # netloc for 'id://...', path for 'path:///...'
    else:
        # Implicit Mode (Fallback)
        if uri.startswith("/") or uri.startswith("."):
            scheme = "path"
            body = uri
        else:
            scheme = "id"
            body = uri

    # 2. Processing according to the scheme
    if scheme == "path":
        # Case path:///dev/hidraw0 -> body=/dev/hidraw0
        return DeviceTarget(path=body)

    elif scheme == "id":
        # Format: VID:PID[:IF]
        parts = body.split(':')
        if len(parts) < 2:
            raise ValueError(f"Invalid ID format '{body}'. Expected VID:PID")
        
        vid = parse_hex_int(parts[0])
        pid = parse_hex_int(parts[1])
        interface = parse_hex_int(parts[2]) if len(parts) > 2 else None
        
        return DeviceTarget(vid=vid, pid=pid, interface=interface)

    else:
        raise ValueError(f"Unknown scheme '{scheme}://'. Supported: id, path.")