import sys
from typing import Any, Dict, List
import typer
from dataclasses import asdict
from rich import print as rprint

from hid_declarative.tools.device import HIDDeviceManager, DeviceError
from hid_declarative.cli.utils import print_json

def main(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON list"),
):
    """
    List connected HID devices and their interfaces.
    """
    try:
        manager = HIDDeviceManager()
    except DeviceError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(1)

    all_devs = manager.find_devices()

    # --- MODE JSON ---
    if json_output:
        exportable = [d.to_dict() for d in all_devs]
        print_json(exportable)
        raise typer.Exit(0)

    # --- MODE HUMAN ---
    if not all_devs:
        rprint("[yellow]No HID devices found.[/yellow]")
        raise typer.Exit(0)

    rprint(f"[bold blue]Found {len(all_devs)} interfaces across devices:[/bold blue]")

    # Grouping by VID:PID
    grouped: Dict[str, List] = {}
    for d in all_devs:
        key = f"{d.vid:04x}:{d.pid:04x}"
        if key not in grouped: grouped[key] = []
        grouped[key].append(d)

    key: str
    for key, interfaces in grouped.items():
        first = interfaces[0]
        rprint(f"\n📦 [bold green]{first.product_string}[/bold green] [dim]({first.manufacturer_string})[/dim]")
        
        for i, d in enumerate(interfaces):
            is_last = (i == len(interfaces) - 1)
            branch = "└──" if is_last else "├──"
            pipe   = "    " if is_last else "│   "
            
            rprint(f"   {branch} Interface [bold yellow]{d.interface}[/bold yellow]")
            
            path_str = d.path.decode(errors='replace')
            # We construct the dump command for the user to copy-paste
            dump_id_cmd = f"hid-declarative dump --device id://{d.vid:04x}:{d.pid:04x}:{d.interface}"
            dump_path_cmd = f"hid-declarative dump --device path://{path_str}"
            
            rprint(f"   {pipe} Path: [dim]{path_str}[/dim]")
            rprint(f"   {pipe} VID:PID: [cyan]{d.vid:04x}:{d.pid:04x}[/cyan]")
            rprint(f"   {pipe} Dump (via id): [cyan]{dump_id_cmd}[/cyan]")
            rprint(f"   {pipe} Dump (via path): [cyan]{dump_path_cmd}[/cyan]")