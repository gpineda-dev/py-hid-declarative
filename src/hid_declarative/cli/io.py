import sys
import base64
import binascii
from pathlib import Path
from typing import Optional, Union
import typer
from rich import print as rprint

from hid_declarative.profile import HIDProfile
from hid_declarative.loader import load_profile, parse_source_profile_uri

def read_input_bytes(
    source: Optional[str], 
    is_base64: bool = False, 
    is_hex: bool = False
) -> bytes:
    """
    Reads binary data from:
    1. Stdin (Pipe) if source is '-' or None
    2. A file (if source is an existing path)
    3. A Hexadecimal string (cleaned)
    4. A Base64 string
    """
    content: Union[str, bytes] = b""

    # A. Read from the raw source
    if source is None or source == "-":
        if sys.stdin.isatty():
            rprint("[yellow]Waiting for input from stdin... (Press Ctrl+D to end)[/yellow]")
        content = sys.stdin.buffer.read()

    elif Path(source).exists() and Path(source).is_file():
        content = Path(source).read_bytes()

    else:
        content = source

    try:
        # B. Decode based on the specified format
        if is_base64:
            if isinstance(content, bytes): content = content.decode('utf-8')
            return base64.b64decode(content)
        
        if is_hex or (isinstance(content, str) and all(c in "0123456789abcdefABCDEF, \n\t" for c in content)):
            if isinstance(content, bytes): content = content.decode('utf-8')
            cleaned_hex:str  = ''.join(c for c in content if c.isalnum())
            cleaned_hex = cleaned_hex.replace('0x', '')
            return bytes.fromhex(cleaned_hex)
        
        if isinstance(content, bytes):
            return content
        
        return content.encode('utf-8')
    
    except Exception as e:
        rprint(f"[red]Error decoding input data: {e}[/red]")
        raise typer.Exit(code=1)
    
def load_profile_from_input(
    source: Optional[str],
    allow_none: bool = False
) -> Optional[HIDProfile]:
    
    
    try:
        source_profile = parse_source_profile_uri(source)
    except Exception as e:
        if allow_none:
            return None
        rprint(f"[red]Error parsing source profile URI:[/red] {e}")
        raise typer.Exit(1)
    
    if isinstance(source_profile, Path):
        if not source_profile.exists() or not source_profile.is_file():
            rprint(f"[red]Error:[/red] File {source_profile} not found.")
            raise typer.Exit(1)
    
    try: 
        profile = load_profile(source_profile)
        return profile
    except Exception as e:
        rprint(f"[red]Error loading profile:[/red] {e}")
        raise typer.Exit(1)