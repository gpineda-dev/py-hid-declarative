from dataclasses import dataclass, field
from typing import List, Literal, Union, Optional

__doc__ = """
HID Schema Nodes module defines the abstract syntax tree (AST) nodes used to represent
the structure of HID reports in a declarative manner.
These nodes include ReportItems (fields), Collections, and ReportGroups.
"""

@dataclass
class Node:
    """Abstract base class for all nodes in the HID schema."""
    pass

@dataclass
class ReportItem(Node):
    """
    Leaf node representing a report item in the HID schema.
    """
    # What it is (Semantic)
    usage_page: int
    usages: List[int] # List to support Usage Min/Max or Array
    
    # Physical properties
    size: int  # Size in bits per element
    count: int # Number of elements
    
    # Logical properties
    logical_min: int
    logical_max: int
    
    physical_min: Optional[int] = None
    physical_max: Optional[int] = None
    
    unit_exponent: Optional[int] = None
    unit: Optional[int] = None

    report_type: Literal["input", "output", "feature"] = "input"

    # Encoding properties
    is_relative: bool = False # False=Abs, True=Rel
    is_constant: bool = False # True=Padding
    is_variable: bool = True  # True=Variable, False=Array
    
    # Metadata to assist the compiler
    name: Optional[str] = None

    @property
    def is_array(self) -> bool:
        return not self.is_variable

@dataclass
class Collection(Node):
    """
    A container node (internal).
    """
    usage_page: int
    usage: int
    type_id: int # Application(1), Physical(0), etc.
    children: List[Node] = field(default_factory=list)

    def add(self, node: Node):
        self.children.append(node)
        return self
    
@dataclass
class ReportGroup(Node):
    """
    A virtual container that assigns a Report ID to all its children.
    This is not a HID Collection (no End Collection generated).
    It is just a scope for the Report ID.
    """
    id: int
    children: List[Node] = field(default_factory=list)

    def add(self, node: Node):
        self.children.append(node)
        return self