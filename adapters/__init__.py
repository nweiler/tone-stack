import json
import yaml
from pathlib import Path
import xml.etree.ElementTree as ET

MAPPINGS_PATH = Path(__file__).parent.parent / "mappings.yaml"

class PlatformAdapter:
    def __init__(self, platform_name):
        self.platform_name = platform_name
        self._mappings = None
        self._reverse_models = None
        self._reverse_params = None

    @property
    def mappings(self):
        if self._mappings is None:
            if MAPPINGS_PATH.exists():
                with open(MAPPINGS_PATH, "r") as f:
                    self._mappings = yaml.safe_load(f).get(self.platform_name, {})
            else:
                self._mappings = {}
        return self._mappings

    @property
    def reverse_models(self):
        if self._reverse_models is None:
            self._reverse_models = {v: k for k, v in self.mappings.get("models", {}).items()}
        return self._reverse_models

    @property
    def reverse_params(self):
        if self._reverse_params is None:
            self._reverse_params = {v: k for k, v in self.mappings.get("parameters", {}).items()}
        return self._reverse_params

    def map_model(self, model_name):
        return self.mappings.get("models", {}).get(model_name, model_name)

    def map_param(self, param_name):
        return self.mappings.get("parameters", {}).get(param_name, param_name)

    def unmap_model(self, platform_model):
        return self.reverse_models.get(platform_model, platform_model)

    def unmap_param(self, platform_param):
        return self.reverse_params.get(platform_param, platform_param)

    def normalize_value(self, val_obj):
        """Converts various units to a normalized 0.0 - 1.0 range."""
        if not isinstance(val_obj, dict):
            if isinstance(val_obj, (int, float)):
                return float(val_obj)
            return val_obj

        val = val_obj.get("value")
        unit = val_obj.get("unit")

        if unit == "oclock":
            if val >= 7: return (val - 7) / 10.0
            if val <= 5: return (val + 5) / 10.0
            return 0.5
        elif unit == "0-10":
            return val / 10.0
        elif unit == "1-12":
            return (val - 1) / 11.0
        elif unit == "percent":
            return val / 100.0
        
        return val

    def format_for_platform(self, normalized_val, target_unit=None):
        if not isinstance(normalized_val, float):
            return normalized_val
            
        if target_unit == "0-10":
            return round(normalized_val * 10, 2)
        elif target_unit == "percent":
            return round(normalized_val * 100, 1)
        
        return round(normalized_val, 3)

    def export_patch(self, meta_patch):
        raise NotImplementedError("Subclasses must implement export_patch()")

    def import_patch(self, platform_data_str):
        raise NotImplementedError("Subclasses must implement import_patch()")

class BiasFXAdapter(PlatformAdapter):
    def __init__(self):
        super().__init__("BiasFX")

    def export_patch(self, meta_patch):
        output = {
            "patch_name": meta_patch.data.get("name"),
            "components": []
        }
        for i, comp in enumerate(meta_patch.data.get("chain", [])):
            platform_comp = {
                "id": self.map_model(comp["model"]),
                "params": {}
            }
            for k, v in comp.get("settings", {}).items():
                norm = self.normalize_value(v)
                platform_comp["params"][self.map_param(k)] = self.format_for_platform(norm)
            output["components"].append(platform_comp)
        return json.dumps(output, indent=2)

class AmplitubeAdapter(PlatformAdapter):
    def __init__(self):
        super().__init__("Amplitube")

    def export_patch(self, meta_patch):
        root = ET.Element("AmpliTubePreset", name=meta_patch.data.get("name"))
        chain = ET.SubElement(root, "Chain")
        for i, comp in enumerate(meta_patch.data.get("chain", [])):
            node = ET.SubElement(chain, "Module", model=self.map_model(comp["model"]), slot=str(i))
            params = ET.SubElement(node, "Parameters")
            for k, v in comp.get("settings", {}).items():
                norm = self.normalize_value(v)
                val = self.format_for_platform(norm, target_unit="0-10")
                ET.SubElement(params, "Param", name=self.map_param(k), value=str(val))
        return ET.tostring(root, encoding="unicode")

class PodGoAdapter(PlatformAdapter):
    def __init__(self):
        super().__init__("PodGo")

    def _get_block_template(self, model=None, enabled=False, pos=None):
        block = {
            "model": model or "L6_None",
            "@enabled": enabled,
            "params": {}
        }
        if pos is not None:
            block["@position"] = pos
        return block

    def export_patch(self, meta_patch):
        output = {
            "version": 6,
            "data": {
                "meta": {
                    "name": meta_patch.data.get("name"),
                    "application": "POD Go Edit",
                    "appversion": "1.40.0"
                },
                "blocks": {
                    "wah": self._get_block_template("HD2_WahFassel"),
                    "vol": self._get_block_template("HD2_VolMonoLog", enabled=True),
                    "fxloop": self._get_block_template("HD2_FXLoopMono"),
                    "amp": self._get_block_template(),
                    "cab": self._get_block_template(),
                    "eq": self._get_block_template(),
                    "block0": self._get_block_template(pos=0),
                    "block1": self._get_block_template(pos=1),
                    "block2": self._get_block_template(pos=2),
                    "block3": self._get_block_template(pos=3)
                }
            }
        }
        
        user_block_idx = 0
        for comp in meta_patch.data.get("chain", []):
            block_type = comp["type"].lower()
            target_block_key = None
            if block_type == "amp": target_block_key = "amp"
            elif block_type == "cab": target_block_key = "cab"
            elif user_block_idx <= 3:
                target_block_key = f"block{user_block_idx}"
                user_block_idx += 1
            
            if target_block_key:
                block = output["data"]["blocks"][target_block_key]
                block["model"] = self.map_model(comp["model"])
                block["@enabled"] = True
                for k, v in comp.get("settings", {}).items():
                    norm = self.normalize_value(v)
                    block["params"][self.map_param(k)] = self.format_for_platform(norm)
            
        return json.dumps(output, indent=2)

    def import_patch(self, platform_data_str):
        data = json.loads(platform_data_str)
        meta = data.get("data", {}).get("meta", {})
        blocks = data.get("data", {}).get("blocks", {})
        
        meta_patch_data = {
            "name": meta.get("name", "Imported Patch"),
            "description": f"Imported from POD GO. Version: {data.get('version')}",
            "tags": ["Imported", "PodGo"],
            "chain": []
        }
        
        # Sort blocks by their logical position or specific key order
        # Fixed blocks order: wah, vol, fxloop, block0, block1, amp, cab, block2, block3, eq
        # This is a simplified priority list
        priority = ["block0", "block1", "amp", "cab", "block2", "block3"]
        
        for key in priority:
            block = blocks.get(key)
            if not block or block.get("model") == "L6_None" or not block.get("@enabled", True):
                continue
                
            comp = {
                "type": "amp" if key == "amp" else ("cab" if key == "cab" else "pedal"),
                "model": self.unmap_model(block["model"]),
                "settings": {}
            }
            
            for p_name, p_val in block.get("params", {}).items():
                generic_name = self.unmap_param(p_name)
                comp["settings"][generic_name] = p_val
                
            meta_patch_data["chain"].append(comp)
            
        return meta_patch_data

def get_adapter(platform_name):
    adapters = {
        "biasfx": BiasFXAdapter,
        "amplitube": AmplitubeAdapter,
        "podgo": PodGoAdapter
    }
    cls = adapters.get(platform_name.lower())
    if not cls:
        raise ValueError(f"No adapter found for platform: {platform_name}")
    return cls()
