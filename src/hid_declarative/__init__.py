# src/hid_declarative/__init__.py

# 1. Core / Point d'entrée
from .profile import HIDProfile
from .result import DescriptorResult

# 2. Schema (Définition API)
from .schema.nodes import Node, Collection, ReportItem
from .schema.widgets import Axis, ButtonArray, Padding

# 3. Spec (Vocabulaire & Enums)
from .spec.tables.generic_desktop import GenericDesktop
from .spec.tables.button import ButtonPage
from .spec.enums import CollectionType
from .spec.tags import ItemTag
from .spec.descriptor import ReportDescriptor

# 4. Engine (Moteur de transformation)
from .compiler import HIDCompiler
from .parser import HIDParser

# 5. Runtime (Exécution & Décodage)
from .runtime.codec import HIDReportCodec
from .runtime.context import HIDContext
from .runtime.analyzer import DescriptorAnalyzer, ScanState
from .runtime.layout import ReportLayout, FieldOp, DescriptorLayout


# Définit l'API publique explicite
__all__ = [
    # Core
    "HIDProfile",
    "DescriptorResult",

    # Schema
    "Node", "Collection", "ReportItem",
    "Axis", "ButtonArray", "Padding",

    # Spec
    "GenericDesktop",
    "ButtonPage",
    "CollectionType",
    "ItemTag",
    "ReportDescriptor",

    # Engine
    "HIDCompiler",
    "HIDParser",

    # Runtime
    "HIDReportCodec",
    "HIDContext",
    "DescriptorAnalyzer",
    "ScanState",
    "ReportLayout",
    "DescriptorLayout",
    "FieldOp",
]