import sys
import json
from typing import Optional
import typer
from pathlib import Path
from rich import print as rprint

from hid_declarative.loader import load_engine


def main(
    # Source
    descriptor: str = typer.Argument(..., help="Path to 'script.py:profile'"),
    report_id: Optional[int] = typer.Option(None, "--report-id", "-r", help="Report ID to encode (if multiple)"),
    force_validation: bool = typer.Option(False, "--validate/--no-validate", help="Force validation of input data before encoding"),
    report_type: Optional[str] = typer.Option("input", "--report-type", "-t", help="Report type to encode (input/output/feature)"),
    
    # Data (JSON String)
    data: str = typer.Argument(..., help="JSON string of values (e.g. '{\"X\": 50}')"),
):
    """
    Encode a JSON object into a HID binary report.
    """
    # 1. Setup Engine (Only via Profile for now, simpler)
    try:
        # We use our unified helper
        codec, _, profile = load_engine(descriptor)
    except Exception as e:
        rprint(f"[red]Engine Error:[/red] Could not prepare runtime from '{descriptor}'. {e}")
        raise typer.Exit(1)

    # 2. Parsing Input
    try:
        # Support JSON file or JSON string
        if Path(data).exists():
            input_dict = json.loads(Path(data).read_text())
        else:
            input_dict = json.loads(data)
    except json.JSONDecodeError as e:
        rprint(f"[red]Invalid JSON input: {e}[/red]")
        raise typer.Exit(1)

    # 3. Encoding
    try:
        report_bytes = codec.encode(
            data = input_dict, 
            report_id=report_id, 
            report_type=report_type,
            validate=force_validation
        )
        
        # Clean Hexadecimal Output
        print(report_bytes.hex().upper())
        
        # Debug display on stderr to avoid polluting the pipe
        rprint(f"[dim]Encoded {len(report_bytes)} bytes[/dim]", file=sys.stderr)
        
    except Exception as e:
        rprint(f"[red]Encode Error: {e}[/red]")
        raise typer.Exit(1)