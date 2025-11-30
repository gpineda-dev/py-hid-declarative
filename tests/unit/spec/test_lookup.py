import pytest
import hid_declarative.spec as spec

def test_get_page_name_known():
	"""
	Verifies that known usage pages return their correct names.
	"""
	# Generic Desktop Page is 0x01
	assert spec.HIDLookup.get_page_name(0x01) == "Generic Desktop"
	# Button Page is 0x09
	assert spec.HIDLookup.get_page_name(0x09) == "Button"

def test_get_page_name_vendor_defined():
	"""
	Verifies that vendor defined pages (0xFF00-0xFFFF) are formatted correctly.
	"""
	assert spec.HIDLookup.get_page_name(0xFF00) == "Vendor Defined (0xFF00)"
	assert spec.HIDLookup.get_page_name(0xFFFF) == "Vendor Defined (0xFFFF)"

def test_get_page_name_unknown():
	"""
	Verifies that unknown pages return the fallback string.
	"""
	# Assuming 0x00 is not in KNOWN_USAGE_PAGES or is treated as unknown here
	# or picking an arbitrary unassigned page like 0x0A (if unassigned in tables)
	# Based on typical HID, 0x00 is Undefined.
	assert spec.HIDLookup.get_page_name(0x00) == "Unknown Page 0x0"

def test_get_usage_name_padding():
	"""
	Verifies that usage ID 0 returns 'Padding / Reserved'.
	"""
	assert spec.HIDLookup.get_usage_name(0x01, 0) == "Padding / Reserved"

def test_get_usage_name_known_enum():
	"""
	Verifies that usages present in the associated IntEnum are resolved.
	"""
	# Generic Desktop (0x01), Usage 0x02 is Mouse
	# The code does .name.replace(' ','_').title()
	# Assuming GenericDesktop.MOUSE exists and name is "MOUSE" -> "Mouse"
	# Or if name is "MOUSE" -> "Mouse"
	
	# Let's test with a standard one. Generic Desktop (1), Keyboard (6)
	# Expected: "Keyboard"
	assert spec.HIDLookup.get_usage_name(0x01, 0x06) == "Keyboard"

def test_get_usage_name_button_page():
	"""
	Verifies special handling for the Button page (0x09).
	"""
	# Button 1
	assert spec.HIDLookup.get_usage_name(0x09, 0x01) == "Button_1"

def test_get_usage_name_unknown_usage_in_known_page():
	"""
	Verifies fallback when the page is known but the usage ID is not in the Enum.
	"""
	# Generic Desktop (0x01), Usage 0xFF (likely not defined)
	assert spec.HIDLookup.get_usage_name(0x01, 0xFF) == "Usage 0xFF"

def test_get_usage_name_unknown_page():
	"""
	Verifies fallback when the page itself is unknown.
	"""
	# Page 0xFE, Usage 0x01
	assert spec.HIDLookup.get_usage_name(0xFE, 0x01) == "Usage 0x01"

def test_get_collection_type_known():
	"""
	Verifies that known collection types are resolved correctly.
	"""
	# CollectionType.PHYSICAL is usually 0x00
	# Code does .name.replace('_', ' ').title()
	# PHYSICAL -> "Physical"
	assert spec.HIDLookup.get_collection_type(0x00) == "Physical"
	
	# CollectionType.APPLICATION is usually 0x01
	assert spec.HIDLookup.get_collection_type(0x01) == "Application"

def test_get_collection_type_unknown():
	"""
	Verifies fallback for unknown collection types.
	"""
	assert spec.HIDLookup.get_collection_type(0xFF) == "Unknown Collection Type 0xff"