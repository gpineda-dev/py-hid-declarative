import sys
import typer
from rich import print as rprint

from hid_declarative.cli.utils import resolve_device_path
from hid_declarative.tools.device import HIDDeviceManager, DeviceError
from hid_declarative.utils import parse_device_uri

def main(
    device: str = typer.Option(..., "--device", "-d", help="Device URI (id://VID:PID[:IF] or path:///dev/...)"),
    output: str = typer.Option(None, "--output", "-o", help="Output file"),
):
    """Dump the Report Descriptor from a real device."""
    try:
        # 1. Parsing
        target_config = parse_device_uri(device)
        
        # 2. Resolution (Factored)
        final_path = resolve_device_path(target_config)
        
        # 3. Extraction
        manager = HIDDeviceManager()
        # We must re-encode the path to bytes for the low-level call
        blob = manager.dump_descriptor_from_path(final_path.encode('utf-8'))
            
        if output:
            with open(output, "wb") as f:
                f.write(blob)
            rprint(f"[green]Saved to {output}[/green]", file=sys.stderr)
        else:
            if sys.stdout.isatty():
                print(blob.hex().upper())
                rprint("[dim](Hex view. Pipe to 'inspect -' to analyze)[/dim]", file=sys.stderr)
            else:
                sys.stdout.buffer.write(blob)
    
    except DeviceError as e:
        rprint(f"[red]Error:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)
    
    except Exception as e:
        rprint(f"[red]Failed to dump descriptor:[/red] {e}", file=sys.stderr)
        raise typer.Exit(1)
