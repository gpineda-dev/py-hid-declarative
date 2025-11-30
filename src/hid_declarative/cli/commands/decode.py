import sys
from typing import Optional
import typer
from rich import print as rprint

from hid_declarative import runtime
from hid_declarative.cli.utils import print_json
from hid_declarative.cli.io import read_input_bytes
from hid_declarative.loader import load_engine


def main(
    # Source of truth (The Descriptor)
    descriptor: str = typer.Argument(..., help="Path to 'script.py:profile' OR binary descriptor file"),
    
    # Data to decode (The Report)
    data: str = typer.Option(None, "--data", "-d", help="Hex string, file path, or '-' for stdin"),
    
    # Options
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON"),
    ignore_errors: bool = typer.Option(False, "--ignore-errors", help="Continue stream even if decoding fails"),
    field_index: Optional[int] = typer.Option(None, "--field-index", "-f", help="Index of the field to decode (for raw field decoding only)"),
):
    """
    Decode HID reports using a profile or descriptor.
    """
    # 1. Engine Initialization (Codec)
    # We support either a raw binary file or a Python profile
    codec, layout, profile = load_engine(descriptor)


    # 2. Unit processing function
    def process_data(raw_bytes: bytes):
        # return
        try:
            decoded: runtime.DataReportType = codec.decode(raw_bytes)
            msg = {
                "raw": raw_bytes.hex(),
                "report_id": decoded.report_id,
                "fields": decoded.to_dict()
            }
            if json_output:
                print_json(msg)
            else:
                rprint(msg)
        except Exception as e:
            if not ignore_errors:
                rprint(f"[red]Decode Error ({raw_bytes.hex()}): {e}[/red]")

    # 3. Input Handling (Single Shot vs Stream)
    
    # Case A: Argument --data (Single Shot)
    if data:
        # Use our smart reader to support "05 01" or a file
        payload = read_input_bytes(data, is_hex=True) # Force hex if it's a string
        print("source payload:", payload.hex())
        process_data(payload)
        return

    # Case B: Pipe (Streaming stdin)
    if not sys.stdin.isatty():
        if not json_output:
            rprint("[dim]Listening on stdin...[/dim]")
            
        for line in sys.stdin:
            line = line.strip()

            if not line or line.startswith("#"): continue

            if field_index is not None:
                _line = line.split()
                line = _line[min(field_index, len(_line)-1)]
            
            # Basic cleanup to support logs like "timestamp hex hex"
            # Take everything hexadecimal in the line
            clean_hex = "".join(c for c in line if c in "0123456789abcdefABCDEF")
            # Need at least one byte
            if len(clean_hex) >= 2 and len(clean_hex) % 2 == 0:
                try:
                    payload = bytes.fromhex(clean_hex)
                    process_data(payload)
                except ValueError as e:
                    
                    rprint(f"[red]Input Error ({line}): {e}[/red]")
                except Exception as e:
                    
                    rprint(f"[red]Decode Error ({line}): {e}[/red]")
    else:
        rprint("[yellow]No data provided. Use --data '05 01...' or pipe content.[/yellow]")