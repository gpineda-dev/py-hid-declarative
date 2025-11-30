import sys
import importlib.util
from pathlib import Path
from typing import Tuple, Union

import urllib.parse
from hid_declarative.spec.descriptor import ReportDescriptor

from .profile import HIDProfile
from .compiler import HIDCompiler
from .parser import HIDParser
from .runtime.analyzer import DescriptorAnalyzer
from .runtime.codec import HIDCodec
from .runtime.layout import DescriptorLayout
import base64

__doc__ = """
HID Loader module provides functionality to load HID profiles from various sources,
including Python scripts, binary files, hex/base64 strings, and stdin.
It supports parsing, compiling, and preparing HID profiles for runtime usage.
"""


class LoaderError(Exception):
    pass

def load_profile_from_script(reference: str) -> HIDProfile:
    """
    Load a HIDProfile from a Python script reference.

    The reference should be in the format: "path/to/script.py:variable_name"

    Returns:
        HIDProfile instance
    Raises:
        LoaderError if loading fails
    """
    
    if ':' not in reference:
        raise LoaderError("Reference must be in the format 'script.py:variable_name'")

    path_str, var_name = reference.split(':', 1)
    file_path = Path(path_str).resolve()

    if not file_path.exists():
        raise LoaderError(f"File {file_path} not found.")
    
    
    sys.path.insert(0, str(file_path.parent))
    try:
        spec = importlib.util.spec_from_file_location("user_config", file_path)
        if spec is None or spec.loader is None:
            raise LoaderError("Failed to load module spec.")
        user_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_mod)

        obj = getattr(user_mod, var_name)
        if not isinstance(obj, HIDProfile):
            raise LoaderError(f"'{var_name}' is not a HIDProfile instance (got {type(obj)}).")
        return obj
    except AttributeError:
        raise LoaderError(f"Variable '{var_name}' not found in {file_path}.")
    except Exception as e:
        raise LoaderError(f"Error loading profile: {e}")
    finally:
        if sys.path[0] == str(file_path.parent):
            sys.path.pop(0)

def parse_source_profile_uri(uri: str) -> Union[bytes, HIDProfile, Path]:
    """
    Parses a source URI for HID Profile input.
    
    Supported formats:
      - py://path/to/script.py:variable_name   (HIDProfile from script)
      - file://path/to/binary/file             (Binary HID Descriptor file)
      - hex://0123ABCD...                      (Hexadecimal string)
      - b64://...                              (Base64 string)
      - stdin://                               (Read from stdin as hex)
      - stdin+bin://                           (Read raw bytes from stdin)
      - 0123ABCD...                            (Implicit Hex string)
      - \-                                     (Read from stdin)
    Returns:
        - HIDProfile instance (for py://)
        - bytes (for binary, hex, b64)
        - Path (for file://)
    """

    # 1. Scheme detection via urllib
    # Tip: if no "://", urlparse does not fill 'scheme' correctly for our cases
    if "://" in uri:
        parsed = urllib.parse.urlparse(uri)
        scheme = parsed.scheme
        body = parsed.netloc + parsed.path # netloc for 'file://...', path for others
    else:
        # Implicit Mode (Fallback to hex)
        if uri == "-" :
            scheme = "stdin"
            body = ""
        else:
            scheme = "hex"
            body = uri.strip()

    # 2. Processing according to the scheme
    if scheme == "py":
        # HIDProfile from script
        return load_profile_from_script(body)

    elif scheme == "file":
        # Binary file path
        return Path(body)

    elif scheme == "hex":
        # Hex String
        ## ensure body is only hex chars
        if not all(c in "0123456789abcdefABCDEF" for c in body):
            raise ValueError(f"Hex string contains invalid characters. Got: {body}")

        cleaned_hex:str  = ''.join(c for c in body if c.isalnum())
        cleaned_hex = cleaned_hex.replace('0x', '')
        return bytes.fromhex(cleaned_hex)

    elif scheme == "b64":
        # Base64 String
        return base64.b64decode(body)

    elif scheme.startswith("stdin"):
        # Read raw bytes from stdin
        if sys.stdin.isatty():
            print("Waiting for binary input from stdin... (Press Ctrl+D to end)")
        data = sys.stdin.buffer.read()

        if scheme == "stdin":
            # treat as hex by default
            cleaned_hex:str  = ''.join(c for c in data.decode('utf-8') if c.isalnum())
            cleaned_hex = cleaned_hex.replace('0x', '')
            return bytes.fromhex(cleaned_hex)
        elif scheme == "stdin+bin":   
            return data
    else:
        raise ValueError(f"Unknown scheme '{scheme}://'. Supported: py, file, hex, b64, stdin.")



def load_profile(target: Union[bytes, Path, HIDProfile]) -> HIDProfile:
    """
    Load a HIDProfile from a target reference.

    The target can be:
        - HIDProfile instance
        - Raw descriptor bytes
        - Path to binary descriptor file

    Returns:
        HIDProfile instance
    Raises:
        LoaderError if loading fails
    """
    if isinstance(target, HIDProfile):
        return target

    profile = HIDProfile()

    if isinstance(target, bytes):
        profile.raw_descriptor = target
        return profile

    if isinstance(target, Path):
        if not target.exists() or not target.is_file():
            raise LoaderError(f"File {target} not found.")
        try:
            raw_bytes = target.read_bytes()
            profile.raw_descriptor = raw_bytes
            return profile
        except Exception as e:
            raise LoaderError(f"Error reading file {target}: {e}")

    raise LoaderError("Unsupported target type for loading HIDProfile.")

def load_engine(target: Union[str, HIDProfile]) -> Tuple[HIDCodec, DescriptorLayout, HIDProfile]:
    """
    Universal Factory.
    Takes a target (.bin or .py:var), HIDProfile and returns the codec, layout and profile.
    Arguments:
        target: Path to binary descriptor file, script reference, or HIDProfile instance.
    Returns:
        Tuple of (HIDCodec, ReportLayout, HIDProfile)
    Raises:
        LoaderError if loading fails
    """

    if not isinstance(target, HIDProfile):
        profile = load_profile(target)
    else:
        profile = target

    if profile is None:
        raise LoaderError("Could not load HIDProfile from target.")
    
    if profile.has_compiled_descriptor():
        items: ReportDescriptor = profile.descriptor
    elif profile.is_compilable():
        compiler = HIDCompiler()
        items: ReportDescriptor = compiler.compile(profile.root, auto_pad=profile.auto_pad)
        profile.descriptor = items
    elif profile.is_parsable():
        parser = HIDParser()
        items: ReportDescriptor = parser.parse(profile.raw_descriptor)
        profile.descriptor = items
    else:
        raise LoaderError("Profile is neither compilable nor parsable.")
    
    analyzer = DescriptorAnalyzer()
    layout = analyzer.analyze(items)
    codec = HIDCodec(layout)

    return codec, layout, profile

