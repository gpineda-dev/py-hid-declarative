from typing import List, Iterator, Union
from pathlib import Path
from dataclasses import dataclass, field

from .items import SpecItem

@dataclass
class ReportDescriptor:
    """
    Represents the final linear sequence of HID instructions (Spec Items).
    This is the result of compilation or parsing.
    """
    _items: List[SpecItem] = field(default_factory=list)
    
    # Cache for the binary blob (Lazy loading)
    _cached_bytes: Union[bytes, None] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        # If a raw list is passed, invalidate the cache for safety
        self._cached_bytes = None

    # --- List Behavior (Sequence Protocol) ---
    
    def __iter__(self) -> Iterator[SpecItem]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def append(self, item: SpecItem):
        self._items.append(item)
        self._cached_bytes = None  # Cache invalidation

    def extend(self, items: List[SpecItem]):
        self._items.extend(items)
        self._cached_bytes = None

    # --- Business Methods (Value Added) ---

    @property
    def bytes(self) -> bytes:
        """Generates (or returns cached) the binary blob."""
        if self._cached_bytes is None:
            self._cached_bytes = b''.join(item.to_bytes() for item in self._items)
        return self._cached_bytes

    @property
    def size(self) -> int:
        return len(self.bytes)
    
    @property
    def size_in_bytes(self) -> int:
        return self.size

    @property
    def hex(self) -> str:
        """Returns a clean hexadecimal string."""
        return self.bytes.hex().upper()

    def save(self, path: Union[str, Path]):
        """Writes the binary directly to a file."""
        p = Path(path)
        p.write_bytes(self.bytes)

    def to_dict(self) -> List[dict]:
        """Converts the descriptor into a list of dictionaries."""
        return [
            {
                "tag_code": item.tag,
                "tag_name": item.__class__.__name__.replace("Item", ""),
                "data": item.data
            }
            for item in self._items
        ]