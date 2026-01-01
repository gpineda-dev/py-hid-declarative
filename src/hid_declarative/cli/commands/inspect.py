import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint, box

# I/O Imports
from hid_declarative.cli.io import load_profile_from_input
from hid_declarative.cli.utils import print_json

# Engine Imports (Facade)
import hid_declarative as hid
from hid_declarative import spec, runtime
from hid_declarative.loader import load_engine
from hid_declarative.result import DescriptorResult
from hid_declarative.runtime.context import HIDContext

app = typer.Typer()

@app.callback(invoke_without_command=True)
def main(
    source: str = typer.Argument(None, help="Source of HID Descriptor: file://path.bin, hex://..., b64://..., stdin://, stdin+bin://, py://script.py:profile, or '-' for stdin everything else is treated as hex"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """
    Inspect a HID Descriptor from ANY source (File, Hex, B64, Pipe, HID Profile).
    """
    # 1. Read I/O
    try:
        profile = load_profile_from_input(source)
    except Exception:
        raise typer.Exit(1)
    
    # 2. Load Engine from Profile
    context: HIDContext = load_engine(profile)
    layout = context.descriptor_layout
    

    # 4. Create Unified Result
    result = DescriptorResult.from_context(context)

    # --- JSON OUTPUT ---
    if json_output:
        print_json(result.to_dict())
        raise typer.Exit(0)

    # --- RICH OUTPUT (HUMAN) ---
    rprint(f"\n[bold blue]=== 0. Hex inline representation ({result.descriptor.size_in_bytes} bytes) ===[/bold blue]")
    rprint(f"[dim]{result.as_hex}[/dim]")
    
    # A. Logical Tree
    rprint(f"\n[bold blue]=== 1. Logical Structure ({len(result.descriptor)} items) ===[/bold blue]")
    
    tree = Tree("HID Report Descriptor", guide_style="blue")
    node_stack = [tree]
    
    # Mini-State for name resolution in the tree
    current_usage_page = 0

    for item in result.descriptor:
        current_node = node_stack[-1]
        
        hex_tag = f"[dim]{item.tag:02X}[/dim]"
        name = item.__class__.__name__.replace("Item", "")
        
        # Data Formatting
        val_str = str(item.data)
        if isinstance(item.data, list) or isinstance(item.data, bytes):
            val_str = bytes(item.data).hex().upper()

        # --- Structural Logic ---
        if item.tag == spec.ItemTag.COLLECTION:
            col_name = spec.HIDLookup.get_collection_type(item.data)
            branch = current_node.add(f"{hex_tag} [bold magenta]Collection[/] ({col_name})")
            node_stack.append(branch)

        elif item.tag == spec.ItemTag.END_COLLECTION:
            current_node.add(f"{hex_tag} [magenta]End Collection[/]")
            if len(node_stack) > 1: node_stack.pop()

        # --- Item Logic ---
        else:
            extra_info = ""
            
            # Active Page Tracking
            if item.tag == spec.ItemTag.USAGE_PAGE:
                current_usage_page = item.data
                page_name = spec.HIDLookup.get_page_name(item.data)
                extra_info = f" ([italic]{page_name}[/])"
            
            # Usage Resolution (Using the current page tracker!)
            elif item.tag in (spec.ItemTag.USAGE, spec.ItemTag.USAGE_MIN, spec.ItemTag.USAGE_MAX):
                usage_name = spec.HIDLookup.get_usage_name(current_usage_page, item.data)
                # Display "Usage: 48 (X)"
                extra_info = f" ([bold cyan]{usage_name}[/])"

            # Style
            style = "cyan"
            if "Input" in name or "Output" in name or "Feature" in name: style = "bold green"
            elif "Usage" in name: style = "yellow"
            
            current_node.add(f"{hex_tag} [{style}]{name}[/]: {val_str}{extra_info}")

    rprint(tree)

    # B. Layout Table (Using DescriptorResult / Objects)
    sorted_ids = sorted(result.layout.list_report_ids())

    for report_id in sorted_ids:

        rprint(f"\n[bold blue]=== REPORT ID {report_id} Memory Layout ===[/bold blue]")
        report_layout = result.layout.get_report_layout(report_id)
        for report_type in runtime.ReportLayout.list_group_types():
            layout = report_layout.get_group(report_type)
            fields = layout.fields
            size = layout.size_bytes

            # Title of the section
            rprint(f"\n[bold blue]====== {report_type.capitalize()} Report (Size: {size} bytes) ======[/bold blue]")
             
            table = Table(box=box.ASCII)
            table.add_column("Bits", style="cyan")
            table.add_column("Byte", style="dim")
            table.add_column("Mask", style="bold blue")
            table.add_column("Name", style="magenta")
            table.add_column("Page", style="dim")
            table.add_column("Type", style="green")
            table.add_column("Min", justify="right", style="yellow")
            table.add_column("Max", justify="right", style="yellow")
            table.add_column("Signed", justify="center", style="red")

            if not fields:
                rprint("[italic dim]Empty report (No data fields)[/italic dim]")
                continue

            for op in fields:
                if op.usage_id == 0: continue
                
                start = op.bit_offset
                end = start + op.bit_size - 1
                
                mask_str = f"0x{op.mask:X}"
                
                # We use op.byte_offset directly (if relevant for the start)
                # But for the 'Byte' display, we often want the range (e.g., 0, or 0-1)
                byte_idx = str(op.byte_offset)
                
                l_min = str(op.logical_min)
                l_max = str(op.logical_max)
                is_signed = "Yes" if op.is_signed else "-"
                
                table.add_row(
                    f"{start}..{end}",
                    byte_idx,
                    mask_str,
                    op.name,
                    op.usage_page_name,
                    op.report_type,
                    l_min,
                    l_max,
                    is_signed,
                )

            Console().print(table)