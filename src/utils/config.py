import os
from pathlib import Path

DEFAULT_CONFIG_PATH = "pixal.yaml"

def load_config(path: str = DEFAULT_CONFIG_PATH) -> dict:
    """Minimal YAML reader without dependencies.
    
    Supports the subset we use (key: value, nested via indentation, simple lists).
    If you want full YAML later, we can add PyYAML, but v1 keeps deps minimal.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing config file: {path}")

    cfg = {}
    stack = [(0, cfg)]

    with open(path, "r", encoding="utf-8") as f:
        for raw in f.readlines():
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip(" "))

            # Determine current container based on indentation
            while stack and indent < stack[-1][0]:
                stack.pop()
            container = stack[-1][1]

            # List item detection - check before colon split
            if stripped.startswith("- "):
                item = stripped[2:].strip()
                container.setdefault("__list__", []).append(item)
                continue

            # Must have a colon for key: value or key: (nested dict)
            if ":" not in stripped:
                continue  # Skip invalid lines without colons

            key_val = stripped.split(":", 1)
            key = key_val[0].strip()
            val = key_val[1].strip() if len(key_val) > 1 else ""

            # value normalization
            if val == "":
                # nested dict (line ends with colon only)
                container[key] = {}
                stack.append((indent + 2, container[key]))
            else:
                # scalar
                if val.lower() in ("true", "false"):
                    v = val.lower() == "true"
                else:
                    # strip quotes if present
                    v = val.strip("'\"")
                container[key] = v

    # Convert any "__list__" to real lists
    def normalize(node):
        if isinstance(node, dict):
            if "__list__" in node and len(node) == 1:
                return node["__list__"]
            return {k: normalize(v) for k, v in node.items() if k != "__list__"}
        return node

    return normalize(cfg)

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)
