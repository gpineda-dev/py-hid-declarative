import pytest
from hid_declarative.schema.nodes import Collection, ReportItem
from hid_declarative.compiler import HIDCompiler
from hid_declarative.spec.items import (
    UsagePageItem, UsageItem, UsageMinItem, UsageMaxItem,
    CollectionItem, EndCollectionItem, InputItem,
    LogicalMinItem, LogicalMaxItem, ReportSizeItem, ReportCountItem,
    PhysicalMinItem
)
from hid_declarative.spec.enums import CollectionType

def test_compiler_state_optimization():
    """
    Checks that the compiler does not emit UsagePage or LogicalMin
    twice if the value does not change between two items.
    """
    # Two report items with the same UsagePage and LogicalMin
    item1 = ReportItem(
        usage_page=0x01, usages=[0x30], size=8, count=1, 
        logical_min=-127, logical_max=127
    )
    item2 = ReportItem(
        usage_page=0x01, usages=[0x31], size=8, count=1, 
        logical_min=-127, logical_max=127
    )
    
    root = Collection(usage_page=0x01, usage=0x01, type_id=1, children=[item1, item2])
    
    compiler = HIDCompiler()
    # We disable auto-padding to simplify the assertion
    items = compiler.compile(root, auto_pad=False)
    
    # We filter to keep only UsagePageItem
    usage_pages = [i for i in items if isinstance(i, UsagePageItem)]
    logical_mins = [i for i in items if isinstance(i, LogicalMinItem)]
    
    # EXPECTATION: Only one page definition, only one min definition
    assert len(usage_pages) == 1 
    assert len(logical_mins) == 1

def test_compiler_usage_range_generation():
    """
    Vérifie que usages=[1, 2, 3] devient UsageMin(1) + UsageMax(3).
    """
    item = ReportItem(
        usage_page=0x09, 
        usages=[1, 2, 3], # Contigu
        size=1, count=3, logical_min=0, logical_max=1
    )
    root = Collection(usage_page=0x01, usage=0x01, type_id=1, children=[item])
    
    compiler = HIDCompiler()
    items = compiler.compile(root, auto_pad=False)
    
    has_min = any(isinstance(i, UsageMinItem) and i.data == 1 for i in items)
    has_max = any(isinstance(i, UsageMaxItem) and i.data == 3 for i in items)
    
    assert has_min
    assert has_max

def test_compiler_usage_list_generation():
    """
    Checks that usages=[1, 3] (non-contiguous) generates Usage(1) + Usage(3).
    """
    item = ReportItem(
        usage_page=0x09, 
        usages=[1, 3], # Gap in the middle
        size=1, count=2, logical_min=0, logical_max=1
    )
    root = Collection(usage_page=0x01, usage=0x01, type_id=1, children=[item])
    
    compiler = HIDCompiler()
    items = compiler.compile(root, auto_pad=False)
    
    # We should NOT have Min/Max
    assert not any(isinstance(i, UsageMinItem) for i in items)
    
    # We should have two UsageItem
    usages = [i for i in items if isinstance(i, UsageItem)]
    # +1 for the collection usage
    assert len(usages) == 3 

def test_compiler_auto_padding():
    """
    Checks that the compiler adds padding to complete the byte.
    Item of 3 bits -> Should add 5 bits of padding.
    """
    item = ReportItem(
        usage_page=0x09, usages=[1, 2, 3], 
        size=1, count=3, # Total 3 bits
        logical_min=0, logical_max=1
    )
    root = Collection(usage_page=0x01, usage=0x01, type_id=1, children=[item])
    
    compiler = HIDCompiler()
    items = compiler.compile(root, auto_pad=True)
    
    # The last 3 items should form the padding
    last_input = items[-1]
    last_count = items[-2]
    last_size = items[-3]
    
    assert isinstance(last_input, InputItem)
    # Flags padding: Const(1) | Var(2) | Abs(0) -> 3
    assert (last_input.data & 0x01) # Check Constant flag
    
    assert isinstance(last_size, ReportSizeItem)
    assert last_size.data == 5 # 8 - 3 = 5 bits missing
    
    assert isinstance(last_count, ReportCountItem)
    assert last_count.data == 1

def test_compiler_physical_and_units():
    """
    Vérifie que les nouveaux champs (Unit, Physical) sont bien émis.
    """
    item = ReportItem(
        usage_page=0x01, usages=[0x30], size=8, count=1,
        logical_min=0, logical_max=255,
        physical_min=0, physical_max=100 # Added
    )
    root = Collection(usage_page=0x01, usage=0x01, type_id=1, children=[item])
    
    compiler = HIDCompiler()
    items = compiler.compile(root, auto_pad=True)
    
    has_phys_min = any(isinstance(i, PhysicalMinItem) for i in items)
    assert has_phys_min