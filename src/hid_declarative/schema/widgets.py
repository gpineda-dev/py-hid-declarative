from hid_declarative.spec.tables.consumer import ConsumerPage
from hid_declarative.spec.tables.keyboard import KeyboardPage
from hid_declarative.spec.tables.led import LedPage
from .nodes import ReportItem
from ..spec.tables.generic_desktop import GenericDesktop
from ..spec.tables.button import ButtonPage

__doc__ = """
Predefined HID Widgets for common controls like Axis, Buttons, DPad, Keyboard Keys, LEDs, Media Keys...
These widgets are built on top of ReportItem (node) and can be used to simplify the creation of HID report layouts.
"""

class Axis(ReportItem):
    """
    Widget for an axis (X, Y, Z, Rx...).
    Default: 8 bits, signed (-127..127), Absolute.
    """
    def __init__(self, usage: int, size=8, min_val=-127, max_val=127, relative=False):
        super().__init__(
            usage_page=GenericDesktop.PAGE_ID,
            usages=[usage],
            size=size,
            count=1,
            logical_min=min_val,
            logical_max=max_val,
            is_relative=relative
        )

class ButtonArray(ReportItem):
    """
    Widget for a group of buttons (1 bit each).
    """
    def __init__(self, count: int, start_index=1):
        # Generate the usage range [1, 2, 3...]
        usage_list = list(range(start_index, start_index + count))
        
        super().__init__(
            usage_page=ButtonPage.PAGE_ID,
            usages=usage_list,
            size=1, # 1 bit per button
            count=count,
            logical_min=0,
            logical_max=1,
            is_variable=True
        )

class Padding(ReportItem):
    """
    Explicit widget to fill gaps.
    Usage = 0, Const = True.
    """
    def __init__(self, bits: int):
        super().__init__(
            usage_page=0,
            usages=[], # No usage
            size=bits,
            count=1,
            logical_min=0,
            logical_max=0,
            is_constant=True
        )

class DPad(ReportItem):
    """
    Hat Switch (Directional Pad).
    4 bits, values 0-7 (North, North-East, East...), 8 = Neutral.
    """
    def __init__(self, count: int = 1):
        super().__init__(
            usage_page=GenericDesktop.PAGE_ID,
            usages=[GenericDesktop.HAT_SWITCH],
            size=4, # 4 bits are enough for 0-8
            count=count,
            logical_min=0,
            logical_max=7,
            physical_min=0,
            physical_max=315, # 360 degrees
            unit=0x14, # Degrees (English Rotation) - Raw code or Enum Unit
            is_variable=True
        )

class KeyboardKeys(ReportItem):
    """
    Standard 6-Key Rollover array (Boot Protocol).
    Sends key indices (not a bitmask).
    """
    def __init__(self, count: int = 6):
        super().__init__(
            usage_page=KeyboardPage.PAGE_ID,
            # Define the valid key range (e.g., 0 to 101)
            # Note: Usage Min/Max here defines the possible RANGE, not active usages
            usages=[0, 101], # Min=0, Max=101 (Application)
            # Or leave usages empty and handle min/max manually if precision is needed
            
            size=8, # 1 byte per key
            count=count, # 6 simultaneous keys
            logical_min=0,
            logical_max=101, # Must match Max Usage
            is_variable=False # <--- THIS IS THE KEY
        )
        # Small trick: to generate UsageMin/Max instead of Usage List,
        # we must pass a contiguous list or handle it in the compiler.
        # Here we force a list [0...101] virtually for the compiler?
        # Better: pass usages=[0, 101] and ensure the compiler
        # generates UsageMin(0) UsageMax(101) if is_array=True.
        # (The current compiler handles contiguity, we can pass an explicit list of 2 elements
        # and modify the compiler to use UsageMin/Max if Array).
        # To simplify V1, we pass a contiguous list (range):
        self.usages = list(range(0, 102))


class LedArray(ReportItem):
    """
    LED Indicators (Num Lock, Caps Lock...).
    This is an OUTPUT Report.
    """
    def __init__(self):
        super().__init__(
            usage_page=LedPage.PAGE_ID,
            usages=[
                LedPage.NUM_LOCK, 
                LedPage.CAPS_LOCK, 
                LedPage.SCROLL_LOCK, 
                LedPage.COMPOSE, 
                LedPage.KANA
            ],
            size=1,
            count=5,
            logical_min=0,
            logical_max=1,
            report_type="output" # <--- This is an Output!
        )

class MediaKeys(ReportItem):
    """
    Multimedia keys (Volume, Play/Pause).
    Often implemented as a bitmask (Variable).
    """
    def __init__(
        self,
        with_volume=True,
        with_playback=True
    ):
        
        usages = []
        if with_playback:
            usages.extend([
                ConsumerPage.SCAN_NEXT_TRACK,
                ConsumerPage.SCAN_PREV_TRACK,
                ConsumerPage.STOP
            ])
        if with_volume:
            usages.extend([
                ConsumerPage.MUTE,
                ConsumerPage.VOLUME_INCREMENT,
                ConsumerPage.VOLUME_DECREMENT
            ])

        super().__init__(
            usage_page=ConsumerPage.PAGE_ID,
            usages=usages,
            size=1,
            count=len(usages),
            logical_min=0,
            logical_max=1,
            is_relative=False # Simple buttons
        )