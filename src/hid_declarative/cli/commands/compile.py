import sys
import typer
from pathlib import Path
from typing import Optional
from rich import print as rprint

from hid_declarative.loader import load_engine, load_profile, load_profile_from_script, LoaderError
from hid_declarative.compiler import HIDCompiler
from hid_declarative.spec.descriptor import ReportDescriptor


def main(
    target: str = typer.Argument(..., help="Path to 'script.py:profile'"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path (default: stdout hex)"),
):
    """
    Compile a Python HID Profile into a binary descriptor (Hex or raw .bin).
    """
    # 1. Load the profile
    try:
        profile = load_profile_from_script(target)
    except LoaderError as e:
        rprint(f"[red]Loader Error:[/red] {e}")
        raise typer.Exit(1)

    rprint(f"[dim]Compiling profile '{profile.name}'...[/dim]", file=sys.stderr)
    _, _, profile = load_engine(profile)

    # 2. Compilation
    if not profile.has_compiled_descriptor():
        rprint(f"[red]Error:[/red] Profile does not have a compiled descriptor.", file=sys.stderr)
        raise typer.Exit(1)
    
    descriptor: ReportDescriptor = profile.descriptor
    rprint(f"[green]Success! Generated {descriptor.size_in_bytes} bytes.[/green]", file=sys.stderr)
    
    # 3. Export Binary / Hex (Simplified logic)
    blob = descriptor.bytes

    if output:
        output.write_bytes(blob)
        rprint(f"[bold]Wrote binary to {output}[/bold]", file=sys.stderr)
    else:
        # Stdout: Print Hex for copy-pasting
        if sys.stdout.isatty():
            print(descriptor.hex)
            rprint("[dim](Hex view. Use -o to save to a binary file)[/dim]", file=sys.stderr)
        else:
            # Pipe: Send raw bytes
            sys.stdout.buffer.write(blob)