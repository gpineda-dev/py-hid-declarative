import sys
import json
import importlib.util
from pathlib import Path
from enum import Enum
from dataclasses import asdict, is_dataclass
from typing import Any, Optional, Union

from hid_declarative.tools.device import DeviceError, HIDDeviceManager
from hid_declarative.utils import DeviceTarget

try:
    import typer
    from rich import print as rprint
except ImportError:
    raise ImportError("Please install with hid-declarative[cli] to use CLI utilities or 'typer' and 'rich' packages.")

from hid_declarative import runtime
from hid_declarative.profile import HIDProfile
import hid_declarative as hid

def json_serializer(obj):
    """Converts objects to JSON-serializable formats."""
    if isinstance(obj, bytes):
        return obj.hex().upper()
    if isinstance(obj, Enum):
        return obj.name  # Displays "APPLICATION" instead of 1
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

def print_json(data):
    """Prints data as formatted JSON."""
    print(json.dumps(data, default=json_serializer, indent=2))




def resolve_device_path(target: DeviceTarget) -> str:
    """
    Resolves a DeviceTarget (Path or ID) into a concrete system path.
    Handles UI (search, errors, ambiguity) and exits (typer.Exit) on failure.
    """
    # Case A: Direct Path (Already resolved)
    if target.path:
        rprint(f"[dim]Using direct path: {target.path}[/dim]", file=sys.stderr)
        return target.path

    # Case B: Search by ID
    if target.vid is None:
        # Should not happen if parse_device_uri is used, but safety check
        rprint("[red]Invalid target: VID is missing.[/red]", file=sys.stderr)
        raise typer.Exit(1)

    try:
        manager = HIDDeviceManager()
        candidates = manager.find_devices(target.vid, target.pid, target.interface)

        # 1. Not found
        if not candidates:
            rprint(f"[red]Device id:{target.vid:04x}:{target.pid:04x} not found.[/red]", file=sys.stderr)
            raise typer.Exit(1)

        # 2. Ambiguous
        if len(candidates) > 1:
            rprint(f"[red]Ambiguous: {len(candidates)} interfaces found.[/red]", file=sys.stderr)
            # Help the user by constructing the suggested command
            base_uri = f"id:{target.vid:04x}:{target.pid:04x}"
            rprint(f"Please specify interface (e.g. [bold]--device {base_uri}:<IF>[/bold]):", file=sys.stderr)
            
            for d in candidates:
                rprint(f" - Interface [cyan]{d.interface}[/cyan] ({d.path.decode()})", file=sys.stderr)
            raise typer.Exit(1)

        # 3. Found!
        selected = candidates[0]
        final_path = selected.path.decode('utf-8')
        rprint(f"[green]Resolved:[/green] {selected.product_string} -> [cyan]{final_path}[/cyan]", file=sys.stderr)
        return final_path

    except DeviceError as e:
        rprint(f"[red]Discovery Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)