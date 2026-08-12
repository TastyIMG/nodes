---
name: comfyui-custom-nodes
description: Use this skill whenever creating, editing, or debugging ComfyUI custom nodes. Triggers include any mention of ComfyUI nodes, node packs, custom_nodes, NODE_CLASS_MAPPINGS, or requests to build image processing nodes for ComfyUI workflows. Also use when troubleshooting node registration, display names, wiring issues, or package branding in ComfyUI.
---

# ComfyUI Custom Node Development

## Folder Structure

A custom node package lives in `custom_nodes/<package-name>/`:

```
custom_nodes/tasty/
├── pyproject.toml        # Package metadata + badge nickname
├── __init__.py           # Node registration (imports + mappings)
├── nodes.py              # Node classes
├── utils.py              # Helper functions
└── face_crop_node.py     # Additional node files (split by domain)
```

## Critical Rules

### The green badge = the folder name
- Whatever the folder is named under `custom_nodes/` is what appears in the green badge on every node.
- `pyproject.toml` nickname only overrides this if the user has ComfyUI Manager set to show nicknames.
- To control the badge reliably, **name the folder what you want the badge to say**.

### Registry key collisions
- ComfyUI has built-in nodes like `ImageCrop`. If your `NODE_CLASS_MAPPINGS` key matches a built-in, **yours gets silently overwritten**.
- Always prefix registry keys with a unique identifier: `"TastyImageCrop": ImageCrop` not `"ImageCrop": ImageCrop`.
- Display names are separate and can be clean: `"TastyImageCrop": "Image Crop"`.

### Display names ≠ registry keys ≠ folder name
- **Registry key** (`NODE_CLASS_MAPPINGS`): Internal ID, must be globally unique. Users never see this.
- **Display name** (`NODE_DISPLAY_NAME_MAPPINGS`): What shows on the node in the UI. Keep clean — no brand prefix needed.
- **Folder name**: The green badge. Brand goes here.
- **CATEGORY**: Controls where the node appears in the right-click add menu. Use `"Brand/SubCategory"` format.

### INT output wiring issues
- numpy int64 looks like INT to Python but ComfyUI's type checker can reject it for wiring.
- Always cast outputs to native Python `int()` before returning.
- Return types must be tuples: `return (value,)` not `return value`.

## Node Class Template

```python
import numpy as np
import torch

class MyNode:
    """Short description of what the node does."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "value": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1}),
            },
            "optional": {
                "toggle": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "STRING")
    RETURN_NAMES = ("image", "count", "json_result")
    OUTPUT_NODE = False
    FUNCTION = "process"
    CATEGORY = "Tasty/SubCategory"

    def process(self, image, value, toggle=True):
        # Always cast to native Python types for outputs
        result_count = int(some_value)
        result_json = json.dumps({"key": "value"})
        return (image, result_count, result_json)
```

## __init__.py Template

```python
try:
    from .nodes import NodeA, NodeB
    from .other_nodes import NodeC, NodeD

    NODE_CLASS_MAPPINGS = {
        "BrandNodeA": NodeA,       # Prefixed registry key
        "BrandNodeB": NodeB,
        "BrandNodeC": NodeC,
        "BrandNodeD": NodeD,
    }

    NODE_DISPLAY_NAME_MAPPINGS = {
        "BrandNodeA": "Node A",    # Clean display name
        "BrandNodeB": "Node B",
        "BrandNodeC": "Node C",
        "BrandNodeD": "Node D",
    }

    __all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
    print(f"[brand] OK — registered {len(NODE_CLASS_MAPPINGS)} nodes: {list(NODE_CLASS_MAPPINGS.keys())}")

except Exception as e:
    print(f"[brand] FAILED TO LOAD: {e}")
    import traceback
    traceback.print_exc()
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}
```

## pyproject.toml Template

```toml
[project]
name = "package-name"
version = "1.0.0"
description = "What this node pack does"
license = "LicenseRef-Proprietary"

[tool.comfy]
nickname = "Brand"
```

## Common Data Types

| Type | Python | Notes |
|------|--------|-------|
| `IMAGE` | torch tensor `[B, H, W, C]` float 0-1 | Batch dimension first |
| `MASK` | torch tensor `[B, H, W]` float 0-1 | No channel dimension |
| `INT` | int | Must be native Python int |
| `FLOAT` | float | Must be native Python float |
| `STRING` | str | Good for JSON output |
| `BOOLEAN` | bool | |
| `LATENT` | dict with "samples" key | |

## Debugging Checklist

When nodes don't appear in ComfyUI:

1. **Check terminal output** — look for the `[brand]` print line. If it says FAILED, the traceback tells you exactly what broke.
2. **File not found** — the `.py` file isn't in the folder, or it's misspelled. Run `ls` on the folder.
3. **Import error on a file that exists** — filename typo. Python says "No module named X" which looks like missing file, but it's almost always a spelling mismatch.
4. **Node loads but doesn't show in search** — registry key collision with a built-in node. Rename the key.
5. **Node shows but won't wire to other nodes** — numpy int64 vs Python int. Cast with `int()`.
6. **Hard refresh the browser** — ComfyUI caches the node list in the frontend. Ctrl+F5 after restart.
7. **8 nodes registered but only 4 show** — the `__init__.py` is missing imports from the new file. Check the `from .filename import` lines.

## Workflow for Adding New Nodes

1. Create the `.py` file with node classes in the package folder.
2. Add import in `__init__.py`: `from .new_file import NewNode`.
3. Add to `NODE_CLASS_MAPPINGS` with a **prefixed** registry key.
4. Add to `NODE_DISPLAY_NAME_MAPPINGS` with a **clean** display name.
5. Restart ComfyUI.
6. Check terminal for registration count.
7. Hard refresh browser.

## Batch Edits

When rebranding or updating strings across multiple files, don't read every line — use a Python script:

```python
python3 << 'EOF'
for filename in ["nodes.py", "other_nodes.py", "__init__.py"]:
    with open(filename, "r") as f:
        content = f.read()
    content = content.replace("OldBrand", "NewBrand")
    with open(filename, "w") as f:
        f.write(content)
EOF
```