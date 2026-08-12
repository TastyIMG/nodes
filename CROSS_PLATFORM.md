# Cross-Platform Compatibility Guide

## How Tasty Nodes Stay Compatible Across Environments

### 1. **Dependency Management**

✓ **What we do:**
- `requirements.txt` - Lists all required packages with minimum versions
- `pyproject.toml` - Modern Python packaging standard
- `install.py` - Auto-installs dependencies when ComfyUI loads the node pack

✓ **Why it works:**
- ComfyUI Manager automatically runs `install.py` on first load
- Users can manually run: `pip install -r requirements.txt`
- Version ranges (>=) allow newer compatible versions

### 2. **Defensive Imports**

✓ **Pattern used in our nodes:**

```python
# Try multiple import paths
try:
    from module import something
except ImportError:
    try:
        from alternative_module import something
    except ImportError:
        something = None  # Graceful fallback
```

✓ **Example: OpenCV Haar Cascades**

We check multiple paths because different OpenCV builds put files in different places:

```python
if hasattr(cv2, 'data'):
    cascade_file = cv2.data.haarcascades + "cascade.xml"
else:
    # Fallback to system paths
    cascade_file = "/usr/share/opencv4/haarcascades/cascade.xml"
```

### 3. **Path Handling**

✓ **Always use `os.path.join()` instead of hardcoded slashes:**

```python
# ✓ Good - works on Windows, Linux, Mac
path = os.path.join(base_dir, "subfolder", "file.txt")

# ✗ Bad - breaks on Windows
path = base_dir + "/subfolder/file.txt"
```

✓ **Use `__file__` for relative paths:**

```python
# Get directory where current file lives
current_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(current_dir, "data", "config.json")
```

### 4. **Type Casting for ComfyUI**

✓ **Always cast numpy types to Python natives:**

```python
# ✓ Good - ComfyUI can wire these
x = int(numpy_value)
y = float(numpy_value)

# ✗ Bad - ComfyUI type checker rejects numpy.int64
x = numpy_array[0]  # This is numpy.int64
```

### 5. **Error Handling**

✓ **Graceful degradation:**

```python
try:
    result = do_complex_operation()
except Exception as e:
    print(f"[tasty] Warning: {e}")
    result = safe_fallback_value()
```

✓ **Informative error messages:**

```python
if not cascade.empty():
    # Process
else:
    print("[tasty] FaceCrop: Haar cascade failed to load")
    print("[tasty] Try: pip install opencv-contrib-python")
```

### 6. **Testing Across Environments**

✓ **What to test:**

1. **Fresh Python environment:**
   ```bash
   python -m venv test_env
   source test_env/bin/activate
   pip install comfyui
   # Load your nodes
   ```

2. **Different OS:**
   - Linux (most common for ComfyUI)
   - Windows (common for desktop users)
   - macOS (some users)

3. **Different Python versions:**
   - Python 3.9 (minimum for most users)
   - Python 3.10
   - Python 3.11+

4. **With/without GPU:**
   - CUDA available
   - CPU-only mode

### 7. **ComfyUI-Specific Patterns**

✓ **Node registration:**

```python
try:
    # Import all nodes
    from .py.node1 import Node1
    
    NODE_CLASS_MAPPINGS = {"Node1": Node1}
    
    print(f"[tasty] ✓ Registered {len(NODE_CLASS_MAPPINGS)} nodes")
    
except Exception as e:
    print(f"[tasty] ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    NODE_CLASS_MAPPINGS = {}
```

✓ **Unique registry keys:**

```python
# ✓ Good - prefixed to avoid collisions
NODE_CLASS_MAPPINGS = {
    "TastyImageCrop": ImageCrop,
}

# ✗ Bad - might collide with built-in nodes
NODE_CLASS_MAPPINGS = {
    "ImageCrop": ImageCrop,
}
```

### 8. **Documentation**

✓ **Include in your README:**

- Minimum Python version
- Required dependencies
- Installation instructions
- Known compatibility issues
- How to report bugs

### 9. **Version Pinning Strategy**

✓ **Use minimum versions, not exact:**

```python
# ✓ Good - allows updates
"opencv-python>=4.5.0"

# ✗ Bad - breaks with updates
"opencv-python==4.5.3"
```

✓ **Exception: Pin if API changed:**

```python
# If version 2.0 broke compatibility
"requests>=1.0.0,<2.0.0"
```

### 10. **Common Pitfalls to Avoid**

❌ **Hardcoded paths:**
```python
# Don't do this
cascade = cv2.CascadeClassifier("/home/user/.local/lib/python3.10/...")
```

❌ **Assuming file locations:**
```python
# Don't assume ComfyUI structure
models_dir = "/ComfyUI/models"  # Might be elsewhere
```

❌ **Using system commands:**
```python
# Don't do this - breaks on Windows
os.system("ls -la")
```

❌ **Forgetting to handle missing dependencies:**
```python
# Don't do this
import obscure_library  # Crashes if not installed
```

✓ **Do this instead:**
```python
try:
    import obscure_library
    HAS_OBSCURE = True
except ImportError:
    HAS_OBSCURE = False
    print("[tasty] Optional feature disabled: obscure_library not found")
```

---

## Quick Checklist for New Nodes

- [ ] Added to `requirements.txt` if new dependency
- [ ] Uses `os.path.join()` for all paths
- [ ] Casts numpy types to Python natives
- [ ] Has try/except around imports
- [ ] Prints helpful error messages
- [ ] Tested on fresh Python environment
- [ ] Registry key is prefixed (e.g., "Tasty...")
- [ ] Returns proper tuple format
- [ ] Has json_result and trigger outputs

---

**Remember:** Users have wildly different setups. Code defensively! 🛡️
