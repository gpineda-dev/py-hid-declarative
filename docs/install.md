# Installation

**HID Declarative** is modular. You can install only what you need to keep your environment lightweight.

## 1. Core Library (Runtime & Compiler)

For embedded scripts, `py-usb-gadget` integration, or purely generating binary files. 
**Zero dependencies.**

<!-- termynal -->
```bash
pip install hid-declarative
---> 100%  Installing collected packages: hid-declarative
Successfully installed hid-declarative-1.2.3
```
## 2. With CLI Tools (Recommended)
If you want to use the hid-declarative command line tool (inspect, compile, decode). Adds dependencies on typer and rich.

```bash
pip install "hid-declarative[cli]"
```
    
## 3. Full Hardware Support (Linux/Mac/Windows)
If you want to Monitor live devices or Dump descriptors from hardware. Adds dependency on hidapi (C bindings).

```bash
pip install "hid-declarative[cli,hidapi]"
```
## 4. For Contributors
If you want to run tests and build documentation locally:

```bash
# Using uv (Recommended)
uv sync --all-extras --dev

# Using pip
pip install -e ".[cli,hidapi,test,docs]"
```