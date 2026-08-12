"""
Tasty - ComfyUI Custom Node Pack
Resilient loader: each node imports independently so one failure won't block the rest.
"""

import traceback

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
_failed = []


def _register(module_path, imports, mappings):
    """
    Try to import `imports` from `module_path` and register each into the global dicts.
    
    imports:  list of (ClassName,)  — names to import from the module
    mappings: dict of { "NodeID": ("ClassName", "Display Name") }
    """
    try:
        mod = __import__(module_path, fromlist=[c for c in imports])
    except Exception as e:
        for node_id, (cls_name, display) in mappings.items():
            _failed.append((node_id, e))
            print(f"[tasty] ⚠ {node_id} unavailable: {e}")
        return

    for node_id, (cls_name, display) in mappings.items():
        cls = getattr(mod, cls_name, None)
        if cls is None:
            _failed.append((node_id, f"{cls_name} not found in {module_path}"))
            print(f"[tasty] ⚠ {node_id} unavailable: {cls_name} not found in {module_path}")
            continue
        NODE_CLASS_MAPPINGS[node_id] = cls
        NODE_DISPLAY_NAME_MAPPINGS[node_id] = display


# ── Executor Override (must import first to patch ComfyUI) ──
_register("custom_nodes.tasty.py.executor", ["TriggerFireNode"], {
    "TastyTriggerFire": ("TriggerFireNode", "Trigger Fire"),
})

# ── Paid API Nodes ──
_register("custom_nodes.tasty.py.svg_to_png_api", ["SvgToPngApiNode"], {
    "TastySvgToPngApi": ("SvgToPngApiNode", "SVG to PNG (API)"),
})

# ── Image Processing & Cropping ──
_register("custom_nodes.tasty.py.face_crop", ["FaceCrop"], {
    "TastyFaceCrop": ("FaceCrop", "Face Crop"),
})
_register("custom_nodes.tasty.py.face_mask", ["FaceMask"], {
    "TastyFaceMask": ("FaceMask", "Face Mask"),
})
_register("custom_nodes.tasty.py.image_crop", ["ImageCrop"], {
    "TastyImageCrop": ("ImageCrop", "Image Crop"),
})
_register("custom_nodes.tasty.py.image_place", ["ImagePlaceNode"], {
    "TastyImagePlace": ("ImagePlaceNode", "Image Place"),
})
_register("custom_nodes.tasty.py.invert_image", ["InvertImageNode"], {
    "TastyInvertImage": ("InvertImageNode", "Invert Image"),
})
_register("custom_nodes.tasty.py.image_rotate", ["ImageRotateNode"], {
    "TastyImageRotate": ("ImageRotateNode", "Image Rotate"),
})
_register("custom_nodes.tasty.py.image_flip", ["ImageFlipNode"], {
    "TastyImageFlip": ("ImageFlipNode", "Image Flip"),
})

# ── Batch (staged R2 URLs from Worker) ──
_register("custom_nodes.tasty.py.batch_load", ["BatchLoadNode"], {
    "TastyBatchLoad": ("BatchLoadNode", "Batch Load (by index)"),
})

_register("custom_nodes.tasty.py.logo_mask", ["LogoMask"], {
    "TastyLogoMask": ("LogoMask", "Logo Mask"),
})
_register("custom_nodes.tasty.py.mask_bounding_box", ["MaskBoundingBox"], {
    "TastyMaskBoundingBox": ("MaskBoundingBox", "Mask Bounding Box"),
})
_register("custom_nodes.tasty.py.mask_smooth", ["MaskSmoothNode"], {
    "TastyMaskSmooth": ("MaskSmoothNode", "Mask Smooth"),
})
_register("custom_nodes.tasty.py.anti_alias_mask", ["AntiAliasMaskNode"], {
    "TastyAntiAliasMask": ("AntiAliasMaskNode", "Anti-Alias Mask"),
})

# ── SVG (optional — requires cairosvg + system libcairo2) ──
_register("custom_nodes.tasty.py.svg_to_png", ["SVGToPNGNode"], {
    "TastySVGToPNG": ("SVGToPNGNode", "SVG to PNG"),
})
_register("custom_nodes.tasty.py.png_to_vector", ["PNGToVectorNode"], {
    "TastyPNGToVector": ("PNGToVectorNode", "PNG to Vector (SVG)"),
})

# ── Grid & Construction Lines ──
_register("custom_nodes.tasty.py.grid", ["GridGenerator"], {
    "TastyGridGenerator": ("GridGenerator", "Grid Generator"),
})
_register("custom_nodes.tasty.py.grid_coords", ["GridCoordsNode"], {
    "TastyGridCoords": ("GridCoordsNode", "Grid Coords"),
})
_register("custom_nodes.tasty.py.draw_line", ["LineDrawNode"], {
    "TastyLineDraw": ("LineDrawNode", "Line Draw"),
})
_register("custom_nodes.tasty.py.circle_draw", ["CircleDrawNode"], {
    "TastyCircleDraw": ("CircleDrawNode", "Circle Draw"),
})
_register("custom_nodes.tasty.py.fib", ["FibonacciSpiralNode"], {
    "TastyFibonacciSpiral": ("FibonacciSpiralNode", "Fibonacci Spiral"),
})
_register("custom_nodes.tasty.py.construction_lines", ["ConstructionLineOverlay"], {
    "TastyConstructionLineOverlay": ("ConstructionLineOverlay", "Construction Line Overlay"),
})
_register("custom_nodes.tasty.py.edge_detect", ["ShapeEdgeDetect"], {
    "TastyShapeEdgeDetect": ("ShapeEdgeDetect", "Shape Edge Detect"),
})

# ── Color & Effects ──
_register("custom_nodes.tasty.py.contrast", ["WCAGContrastNode"], {
    "TastyWCAGContrast": ("WCAGContrastNode", "WCAG Contrast Calculator"),
})
_register("custom_nodes.tasty.py.recolor", ["RecolorNode"], {
    "TastyRecolor": ("RecolorNode", "Recolor (Mask)"),
})
_register("custom_nodes.tasty.py.blur_average", ["BlurAverageNode"], {
    "TastyBlurAverage": ("BlurAverageNode", "Blur Average (Dominant Color)"),
})

# ── Primitives ──
_register("custom_nodes.tasty.py.prim_node", ["IntNode", "FloatNode", "StringNode", "BoolNode"], {
    "TastyIntPrim": ("IntNode", "Int"),
    "TastyFloatPrim": ("FloatNode", "Float"),
    "TastyStringPrim": ("StringNode", "String"),
    "TastyBoolPrim": ("BoolNode", "Bool"),
})

# ── Variables ──
_register("custom_nodes.tasty.py.variables", [
    "NumberVarSetNode", "NumberVarGetNode", "NumberVarIncrementNode",
    "NumberVarDecrementNode", "NumberVarResetNode",
    "StringVarSetNode", "StringVarGetNode", "StringVarDeleteNode",
], {
    "TastyNumberVarSet": ("NumberVarSetNode", "Variable Set (Number)"),
    "TastyNumberVarGet": ("NumberVarGetNode", "Variable Get (Number)"),
    "TastyNumberVarIncrement": ("NumberVarIncrementNode", "Variable Increment (Number)"),
    "TastyNumberVarDecrement": ("NumberVarDecrementNode", "Variable Decrement (Number)"),
    "TastyNumberVarReset": ("NumberVarResetNode", "Variable Reset (Number)"),
    "TastyStringVarSet": ("StringVarSetNode", "Variable Set (String)"),
    "TastyStringVarGet": ("StringVarGetNode", "Variable Get (String)"),
    "TastyStringVarDelete": ("StringVarDeleteNode", "Variable Delete (String)"),
})

# ── Flow Control ──
try:
    from .py.trigger import GateNode, make_wait_node, WAIT_TYPES
    NODE_CLASS_MAPPINGS["TastyGate"] = GateNode
    NODE_DISPLAY_NAME_MAPPINGS["TastyGate"] = "Trigger"
    for name, type_str in WAIT_TYPES.items():
        cls_name = f"TastyWait{name}"
        NODE_CLASS_MAPPINGS[cls_name] = make_wait_node(name, type_str)
        NODE_DISPLAY_NAME_MAPPINGS[cls_name] = f"Wait ({name})"
except Exception as e:
    _failed.append(("TastyGate + Wait nodes", e))
    print(f"[tasty] ⚠ Flow control nodes unavailable: {e}")

# ── API & Network ──
_register("custom_nodes.tasty.py.http", ["HttpRequestNode"], {
    "TastyHttpRequest": ("HttpRequestNode", "HTTP Request"),
})
_register("custom_nodes.tasty.py.api", ["TastyApiNode"], {
    "TastyApi": ("TastyApiNode", "Tasty API"),
})
_register("custom_nodes.tasty.py.vps", ["VPSWorkflowNode"], {
    "TastyVPSWorkflow": ("VPSWorkflowNode", "VPS Workflow"),
})
_register("custom_nodes.tasty.py.database", ["D1QueryNode"], {
    "TastyD1Query": ("D1QueryNode", "D1 Query"),
})

# ── Crypto & Utilities ──
_register("custom_nodes.tasty.py.crypto", ["SHA256Node", "RandomNumberNode", "UUIDNode"], {
    "TastySHA256": ("SHA256Node", "SHA-256 Hash"),
    "TastyRandomNumber": ("RandomNumberNode", "Random Number"),
    "TastyUUID": ("UUIDNode", "UUID Generator"),
})
_register("custom_nodes.tasty.py.json_viewer", ["JsonViewerNode"], {
    "TastyJsonViewer": ("JsonViewerNode", "JSON Viewer"),
})

# ── Preview & Save ──
_register("custom_nodes.tasty.py.preview", ["TastyPreviewImage", "TastySaveImage", "TastyPreviewAny"], {
    "TastyPreviewImage": ("TastyPreviewImage", "Preview Image"),
    "TastySaveImage": ("TastySaveImage", "Save Image"),
    "TastyPreviewAny": ("TastyPreviewAny", "Preview Any"),
})

# ── Summary ──
WEB_DIRECTORY = "./web/js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

if _failed:
    print(f"[tasty] ✓ Registered {len(NODE_CLASS_MAPPINGS)} nodes ({len(_failed)} failed)")
    for node_id, err in _failed:
        print(f"[tasty]   ✗ {node_id}: {err}")
else:
    print(f"[tasty] ✓ Registered {len(NODE_CLASS_MAPPINGS)} nodes")
