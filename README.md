# Meta-Patch: Standardized Guitar Tone Stack Metadata

Meta-Patch is a succinct, metadata-style notation for documenting guitar amplifier and pedal settings. It is designed to be platform-agnostic, allowing you to recreate similar "tones" across different tools like Bias FX, Amplitube, POD GO, or even real hardware.

## Why Meta-Patch?
- **Platform Agnostic:** Describe the *intent* (e.g., "Tube Screamer gain at zero") rather than platform-specific binary files.
- **Human Readable:** Uses YAML for easy reading and writing.
- **Machine Validatable:** Includes a JSON schema for consistency.
- **Succinct:** Captures only the essential settings needed to approximate a sound.

## Web Previewer
You can visualize your patch library using the built-in web previewer. It provides a visual signal chain and settings inspector.

```bash
# Start the preview server
python3 preview_server.py
```
Then visit **http://localhost:8000** in your browser.

## Getting Started

### 1. Requirements
- Python 3.x
- `PyYAML`
- `jsonschema`

```bash
pip install PyYAML jsonschema
```

### 2. Usage
Use the `meta_patch.py` script to manage your patch library or export to specific platforms.

```bash
# List all available patches in ./patches/
python3 meta_patch.py list

# Search patches by name or tag
python3 meta_patch.py search blues

# Batch export all patches to a target platform (e.g., biasfx, podgo)
python3 meta_patch.py batch-export biasfx

# Describe a specific patch file
python3 meta_patch.py patches/texas-blues.yaml describe

# Export a single patch to a platform
python3 meta_patch.py patches/texas-blues.yaml export amplitube
```

## Patch Library
Patches are stored in the `./patches/` directory as YAML files. Each patch includes metadata like `name`, `description`, and `tags`, followed by an ordered `chain` of components.

## Platform Adapters & Mappings
The project supports exporting Meta-Patches to platform-specific formats. This is driven by the `mappings.yaml` file, which maps generic gear models and parameters to their platform-specific equivalents.

### Example Mapping (`mappings.yaml`)
```yaml
BiasFX:
  models:
    "Tube Screamer": "808_Overdrive"
  parameters:
    gain: "Drive"
```

### 3. Creating a Patch
Create a `.yaml` file following this structure:

```yaml
name: "My Awesome Tone"
description: "A short description of the sound."
chain:
  - type: pedal
    model: "Tube Screamer"
    settings:
      gain: 0.1         # 0.0 to 1.0 (normalized)
      tone: 
        value: 12
        unit: "oclock"  # Explicit units
      level: 0.9
  - type: amp
    model: "Plexi"
    settings:
      gain: 0.7
      treble: 0.6
      middle: 0.5
      bass: 0.4
```

## Supported Units
- `0.0` - `1.0`: Normalized scale (default).
- `0-10`: Standard guitar knob scale.
- `1-12`: High-resolution or vintage scale.
- `oclock`: Clock-face notation (e.g., `12`, `3`, `9`).
- `db`: Decibels.
- `ms`: Milliseconds (for delay).
- `hz`: Hertz (for EQ frequencies).
- `percent`: 0 to 100.
