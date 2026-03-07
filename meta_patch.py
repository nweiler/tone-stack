import json
import yaml
import jsonschema
import sys
import os
import glob
from pathlib import Path
import adapters

SCHEMA_PATH = Path(__file__).parent / "meta-patch-schema.json"
PATCH_DIR = Path(__file__).parent / "patches"

class MetaPatch:
    def __init__(self, data, path=None):
        self.data = data
        self.path = path
        self._schema = None

    @property
    def schema(self):
        if self._schema is None:
            with open(SCHEMA_PATH, "r") as f:
                self._schema = json.load(f)
        return self._schema

    def validate(self):
        try:
            jsonschema.validate(instance=self.data, schema=self.schema)
            return True, "Validation successful."
        except jsonschema.exceptions.ValidationError as e:
            return False, f"Validation error: {e.message}"

    @classmethod
    def from_yaml(cls, yaml_str, path=None):
        data = yaml.safe_load(yaml_str)
        return cls(data, path)

    @classmethod
    def from_file(cls, file_path):
        ext = Path(file_path).suffix.lower()
        with open(file_path, "r") as f:
            if ext in [".yaml", ".yml"]:
                return cls.from_yaml(f.read(), path=file_path)
            elif ext == ".json" or ext == ".at5p":
                # Check if it's a Meta-Patch JSON or a Platform JSON
                content = f.read()
                try:
                    data = json.loads(content)
                    if "chain" in data: # Likely Meta-Patch
                        return cls(data, path=file_path)
                    return data # Return raw data for importer
                except json.JSONDecodeError:
                    return content # Likely XML (Amplitube)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")

    def to_json(self):
        return json.dumps(self.data, indent=2)

    def to_yaml(self):
        return yaml.dump(self.data, sort_keys=False)

    def describe(self):
        lines = []
        lines.append(f"Meta-Patch: {self.data.get('name', 'Unnamed')}")
        lines.append(f"Description: {self.data.get('description', 'N/A')}")
        lines.append(f"Tags: {', '.join(self.data.get('tags', []))}")
        lines.append("-" * 40)
        
        for i, comp in enumerate(self.data.get('chain', [])):
            lines.append(f"[{i+1}] {comp['type'].upper()}: {comp['model']}")
            for key, val in comp.get('settings', {}).items():
                if isinstance(val, dict):
                    display_val = f"{val['value']} {val['unit']}"
                elif isinstance(val, float):
                    display_val = f"{val*100:.0f}%" if 0 <= val <= 1 else str(val)
                else:
                    display_val = str(val)
                lines.append(f"    - {key}: {display_val}")
        
        return "\n".join(lines)

def load_all_patches():
    patches = []
    if not PATCH_DIR.exists():
        return patches
    for file_path in glob.glob(str(PATCH_DIR / "*.yaml")) + glob.glob(str(PATCH_DIR / "*.yml")):
        try:
            patches.append(MetaPatch.from_file(file_path))
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}")
    return patches

def main():
    if len(sys.argv) < 2:
        print("Usage: python meta_patch.py <patch_file|command> [args...]")
        print("\nCommands:")
        print("  list                       List all available patches in ./patches/")
        print("  search <term>              Search patches by name or tag")
        print("  batch-export <platform>    Export all patches to a target platform")
        print("  import <platform> <file>   Import a platform-specific patch")
        print("  batch-import <platform> <dir> [target_dir]  Import all patches in a directory")
        sys.exit(1)

    cmd_or_file = sys.argv[1]

    if cmd_or_file == "list":
        patches = load_all_patches()
        print(f"{'Name':<25} {'Tags':<30} {'File'}")
        print("-" * 80)
        for p in patches:
            name = p.data.get('name', 'Unnamed')
            tags = ", ".join(p.data.get('tags', []))
            file = Path(p.path).name
            print(f"{name[:24]:<25} {tags[:29]:<30} {file}")
        sys.exit(0)

    if cmd_or_file == "search":
        if len(sys.argv) < 3:
            print("Error: search requires a term.")
            sys.exit(1)
        term = sys.argv[2].lower()
        patches = load_all_patches()
        matches = [p for p in patches if term in p.data.get('name', '').lower() or any(term in t.lower() for t in p.data.get('tags', []))]
        for p in matches:
            print("-" * 40)
            print(p.describe())
        sys.exit(0)

    if cmd_or_file == "batch-export":
        if len(sys.argv) < 3:
            print("Error: batch-export requires a platform.")
            sys.exit(1)
        platform = sys.argv[2]
        patches = load_all_patches()
        output_dir = Path(f"export_{platform}")
        output_dir.mkdir(exist_ok=True)
        adapter = adapters.get_adapter(platform)
        for p in patches:
            ext = "json" if platform.lower() != "amplitube" else "at5p"
            out_file = output_dir / f"{Path(p.path).stem}.{ext}"
            with open(out_file, "w") as f:
                f.write(adapter.export_patch(p))
            print(f"Exported {p.data.get('name')} to {out_file}")
        sys.exit(0)

    if cmd_or_file == "import":
        if len(sys.argv) < 4:
            print("Usage: python meta_patch.py import <platform> <file>")
            sys.exit(1)
        platform = sys.argv[2]
        import_path = sys.argv[3]
        adapter = adapters.get_adapter(platform)
        with open(import_path, "r") as f:
            raw_data = f.read()
            meta_data = adapter.import_patch(raw_data)
            patch = MetaPatch(meta_data)
            print(patch.to_yaml())
        sys.exit(0)

    if cmd_or_file == "batch-import":
        if len(sys.argv) < 4:
            print("Usage: python meta_patch.py batch-import <platform> <source_dir> [target_dir]")
            sys.exit(1)
        platform = sys.argv[2]
        source_dir = Path(sys.argv[3])
        target_dir = Path(sys.argv[4]) if len(sys.argv) > 4 else PATCH_DIR
        target_dir.mkdir(exist_ok=True)
        
        adapter = adapters.get_adapter(platform)
        files = list(source_dir.glob("*"))
        for f_path in files:
            if f_path.is_dir(): continue
            try:
                with open(f_path, "r") as f:
                    raw_data = f.read()
                    meta_data = adapter.import_patch(raw_data)
                    patch = MetaPatch(meta_data)
                    out_file = target_dir / f"{f_path.stem}.yaml"
                    with open(out_file, "w") as out:
                        out.write(patch.to_yaml())
                    print(f"Imported {f_path.name} -> {out_file.name}")
            except Exception as e:
                print(f"Failed to import {f_path.name}: {e}")
        sys.exit(0)

    # Otherwise, treat first arg as file
    file_path = cmd_or_file
    command = sys.argv[2] if len(sys.argv) > 2 else "describe"

    try:
        patch_or_raw = MetaPatch.from_file(file_path)
        
        if isinstance(patch_or_raw, (dict, str)) and not isinstance(patch_or_raw, MetaPatch):
            print("Error: This appears to be a platform-specific file. Use 'import' instead.")
            sys.exit(1)
            
        patch = patch_or_raw
        
        if command == "validate":
            success, msg = patch.validate()
            print(msg)
            sys.exit(0 if success else 1)
        elif command == "describe":
            print(patch.describe())
        elif command == "export":
            if len(sys.argv) < 4:
                print("Error: export command requires a platform name.")
                sys.exit(1)
            platform = sys.argv[3]
            adapter = adapters.get_adapter(platform)
            print(adapter.export_patch(patch))
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
