import sys
from typing import Optional, Union
import typer
from rich import print as rprint

from hid_declarative.cli.io import load_profile_from_input
from hid_declarative.cli.utils import resolve_device_path
from hid_declarative.loader import LoaderError, load_engine, load_profile
from hid_declarative.runtime.reports import DataReportType
from hid_declarative.tools.device import HIDDeviceManager
from hid_declarative.tools.monitor import HIDMonitor, HIDMonitorError, ReportEvent
from hid_declarative.utils import DeviceTarget, parse_device_uri

def main(
    device: str = typer.Option(None, "--device", "-d", help="URI: id://VID:PID or path:///dev/hidrawX"),

    target: Optional[str] = typer.Option(None, "--target", "-t", help="Path to configuration file or target name."),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw report bytes instead of decoded reports."),
):
    """
    Connect to a real USB device and view decoded reports live.
    Requires 'hidapi' installed.
    """

    # 1. Read I/O
    try:
        profile = load_profile_from_input(target, allow_none=True)
    except Exception:
        raise typer.Exit(1)
    
    # 2. Load Engine from Profile
    codec = None
    if profile is not None:
        try:
            codec, layout, profile = load_engine(profile)
        except Exception as e:
            rprint(f"[red]Error loading engine:[/red] {e}")
            raise typer.Exit(1)


    # 2. Resolve Device uri
    final_path = None
    if device:
        try:
            target_config = parse_device_uri(device)
        except ValueError as e:
            rprint(f"[red]Argument Error:[/red] {e}")
            raise typer.Exit(1)
    elif profile and profile.vendor_id and profile.product_id:
        # Fallback Profil
        target_config = DeviceTarget(vid=profile.vendor_id, pid=profile.product_id)
    else:
        # Error: No device specified
        rprint("[yellow]No device specified via --device or Profile.[/yellow]")
        raise typer.Exit(0)

    # 3. Resolve Path
    final_path = resolve_device_path(target_config)
    if not final_path:
        rprint(f"[red]Error:[/red] Could not resolve device path for target {target_config}.")
        raise typer.Exit(1)

    # 4. Run Loop
    try:
        with HIDMonitor(final_path, codec) as monitor:
            rprint("[green]Connected! Listening for reports... (Ctrl+C to stop)[/green]")
            event: ReportEvent
            for event in monitor.stream(raw_output=raw):
                if raw:
                    rprint(f"[blue]Raw Report:[/blue] {event.to_dict()}")
                    # flush
                    sys.stdout.flush()
                else:
                    rprint(f"[green]Decoded Report:[/green] {event.to_dict()}")
                
                    
    except HIDMonitorError as e:
        rprint(f"[red]Monitor Error:[/red] {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        rprint("\n[dim]Exiting...[/dim]")