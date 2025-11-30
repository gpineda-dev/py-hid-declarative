# HID Declarative

<p align="center">
  <strong>The modern, type-safe Python stack for USB HID development.</strong>
  <br>
  <em>Define in Python. Compile to Binary. Run anywhere.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/hid-declarative" target="_blank">
    <img src="https://img.shields.io/pypi/v/hid-declarative?color=%2334D058&label=pypi%20package&style=flat-square" alt="Package version">
  </a>
  <a href="https://pypi.org/project/hid-declarative" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/hid-declarative.svg?color=%2334D058&style=flat-square" alt="Supported Python versions">
  </a>
  <a href="https://github.com/gpineda-dev/py-hid-declarative/actions" target="_blank">
    <img src="https://img.shields.io/github/actions/workflow/status/gpineda-dev/py-hid-declarative/ci.yml?label=tests&style=flat-square" alt="Tests">
  </a>
</p>

> ⚠️ **Early Access / Alpha**: This library is currently under active development. The API (especially `schema` and `runtime`) is subject to breaking changes until version **0.1.0** is officially released. Use with caution.

---

**HID Declarative** solves the pain of working with USB Human Interface Devices. 
Instead of manipulating obscure byte arrays, you define your device structure using clean, declarative Python objects.

It acts as a bridge between **High-Level Logic** and **Low-Level Protocol**.

## ✨ Key Features

* 🏗️ **Declarative Schema**: Define complex devices (Mouse, Gamepad, Keyboard) in pure Python.
* ⚡ **Zero-Dependency Runtime**: Decode and Encode USB reports with a lightweight codec.
* 🛠️ **Powerful CLI**: Inspect binary descriptors, dump from hardware (`/dev/hidraw`), and monitor live inputs.
* 📦 **DevOps Ready**: Automate hardware testing by simulating inputs and validating outputs.

## 🛠️ Installation

```bash
# 1. Core library (Zero dependencies for embedded usage)
pip install hid-declarative

# 2. With CLI tools (Recommended for development)
pip install "hid-declarative[cli]"

# 3. With Hardware support (Linux/Mac/Windows)
pip install "hid-declarative[cli,hidapi]"
````

## 🚀 Quick Start

### 1\. Define your Device

Instead of writing hex bytes, write Python. Save this as `my_mouse.py`.

```python
import hid_declarative as hid
from hid_declarative import schema, widgets, spec

# Define the structure
profile = hid.HIDProfile(
    root=schema.Collection(
        usage_page=spec.GenericDesktop.PAGE_ID,
        usage=spec.GenericDesktop.MOUSE,
        children=[
            widgets.ButtonArray(3),           # 3 Buttons
            widgets.Axis(spec.GenericDesktop.X), # X Axis
            widgets.Axis(spec.GenericDesktop.Y), # Y Axis
        ]
    ),
    name="MyMouse",
    auto_pad=True # Automatically adds padding to align bytes
)
```

### 2\. Compile & Inspect

Use the CLI to generate the binary descriptor and verify its layout.

```bash
# Compile Python -> Binary
hid-declarative compile py://my_mouse.py:profile -o mouse.bin

# Inspect the layout
hid-declarative inspect file://mouse.bin
```

**Output:**

```text
=== Memory Layout (3 bytes) ===
Bits   Byte  Mask  Name      Type   Min   Max
0..0   0     0x1   Button_1  input    0     1
1..1   0     0x1   Button_2  input    0     1
2..2   0     0x1   Button_3  input    0     1
8..15  1     0xFF  X         input -127   127
16..23 2     0xFF  Y         input -127   127
```

### 3\. Live Monitoring

Connect your real device and see what happens under the hood.

```bash
# Dump from Linux kernel & Monitor
sudo hid-declarative live --device path:///dev/hidraw0
```

## 📚 Documentation

Full documentation is available at **[https://gpineda-dev.github.io/py-hid-declarative](https://gpineda-dev.github.io/py-hid-declarative)** 

## 🤝 Contributing

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Setup environment
uv sync --all-extras --dev

# Run tests
uv run pytest
```

## 🚧 Roadmap to v1.0
* [x] Core Spec & Parser
* [x] Compiler & Schema Engine
* [x] Runtime Codec (encode/decode)
* [x] CLI Tools (compile, inspect, live, encode/decode, list, dump)
* [ ] Comprehensive documentation
* [ ] More Examples & Tutorials
* [ ] Community feedback & testing
* [ ] Stable API (v1.0 release)
* [ ] Codegen (overwriting .c source file with code injection). -- Future

> Main priority is stabilizing the core API and runtime before adding codegen features.


## 📄 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
