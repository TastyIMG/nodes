# Node UI Rendering in ComfyUI

## The Problem

ComfyUI's Python backend can return UI data via `{"ui": {...}}`, but the frontend only knows how to render certain built-in keys (like `"images"` for image previews). For custom text display, you need a companion JS file.

## Architecture

```
tasty/
├── py/
│   └── your_node.py       ← Python: returns {"ui": {"text": [value]}}
├── web/
│   └── js/
│       └── your_node.js   ← JS: reads message.text[0] and shows it
└── __init__.py             ← Must declare WEB_DIRECTORY = "./web/js"
```

## Step 1: Python Node

Return UI data alongside results:

```python
class MyDisplayNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("STRING", {"forceInput": True}),  # connector only, no widget
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "Tasty/Utils"

    def execute(self, value):
        display_text = str(value)
        return {
            "ui": {"text": [display_text]},   # <-- this is what JS reads
            "result": (value,)                 # <-- this is what outputs carry
        }
```

Key points:
- `OUTPUT_NODE = True` is required for UI rendering
- `"ui"` dict keys are arbitrary — you pick the name, JS reads it
- `"result"` tuple must match `RETURN_TYPES` length

## Step 2: JavaScript Extension

Create `web/js/your_node.js`:

```javascript
import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "tasty.MyDisplayNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "TastyMyDisplayNode") {    // must match NODE_CLASS_MAPPINGS key

            // Create a read-only text widget when node is added to canvas
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated ? onNodeCreated.apply(this, []) : undefined;
                this.showValueWidget = ComfyWidgets["STRING"](
                    this, "output", ["STRING", { multiline: true }], app
                ).widget;
                this.showValueWidget.inputEl.readOnly = true;
                this.showValueWidget.serializeValue = async () => "";
            };

            // Update the widget when node finishes executing
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, [message]);
                if (message?.text?.[0] !== undefined) {
                    this.showValueWidget.value = message.text[0];  // reads ui.text[0]
                }
            };
        }
    },
});
```

Key points:
- `nodeData.name` must match the key in `NODE_CLASS_MAPPINGS` (e.g. `"TastyJsonViewer"`)
- `message.text[0]` reads from the Python `{"ui": {"text": [...]}}` return
- `serializeValue = async () => ""` prevents the display value from being saved in workflows
- `readOnly = true` prevents users from typing in the display area

## Step 3: Register in \_\_init\_\_.py

```python
WEB_DIRECTORY = "./web/js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
```

## Quick Reference: Built-in UI Keys

These work without JS because ComfyUI's frontend handles them natively:

| UI Key | What it renders | Example |
|--------|----------------|---------|
| `"images"` | Image thumbnails | `{"images": [{"filename": "x.png", "subfolder": "temp", "type": "temp"}]}` |

Everything else (text, tables, charts) needs a JS companion.

## Input Types Cheatsheet

| Config | Result |
|--------|--------|
| `("STRING",)` | Text field widget (editable + connectable) |
| `("STRING", {"forceInput": True})` | Connector only (no widget) |
| `("STRING", {"multiline": True})` | Large text area widget |
| `("STRING", {"default": "hello"})` | Text field with default value |
| `("INT", {"forceInput": True})` | Int connector only |
| `("*",)` | Accepts any type |

## Common Patterns

### Pass-through display (view + forward data)
```python
RETURN_TYPES = ("STRING",)
OUTPUT_NODE = True

def execute(self, value):
    return {"ui": {"text": [value]}, "result": (value,)}
```

### Display-only (no outputs)
```python
RETURN_TYPES = ()
OUTPUT_NODE = True

def execute(self, value):
    return {"ui": {"text": [str(value)]}}
```

### Image preview with passthrough
```python
RETURN_TYPES = ("IMAGE",)
OUTPUT_NODE = True

def execute(self, images):
    # save to temp, build results list...
    return {"ui": {"images": results}, "result": (images,)}
```
