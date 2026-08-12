import json


class GateNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("*",),
            },
        }

    RETURN_TYPES = ("TRIGGER", "*", "STRING")
    RETURN_NAMES = ("trigger", "value", "json_result")
    FUNCTION = "execute"
    CATEGORY = "utils/flow"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, input):
        json_result = json.dumps({"node": "GateNode", "type": "gate", "value": str(input)})
        return ("done", input, json_result)


def make_wait_node(type_name, type_str):
    class WaitNode:
        @classmethod
        def INPUT_TYPES(cls):
            return {
                "required": {
                    "trigger": ("TRIGGER",),
                    "value": (type_str,),
                },
            }

        RETURN_TYPES = (type_str, "TASTY_JSON", "TRIGGER")
        RETURN_NAMES = ("value", "json_result", "trigger")
        FUNCTION = "execute"
        CATEGORY = "utils/flow"

        @classmethod
        def VALIDATE_INPUTS(cls, **kwargs):
            return True

        def execute(self, trigger, value):
            json_result = json.dumps({"node": f"Wait{type_name}Node", "type": f"wait_{type_name.lower()}", "value": str(value)})
            return (value, json_result, "done")

    WaitNode.__name__ = f"Wait{type_name}Node"
    WaitNode.__qualname__ = f"Wait{type_name}Node"
    return WaitNode


WAIT_TYPES = {
    "Int":        "INT",
    "Float":      "FLOAT",
    "String":     "STRING",
    "Bool":       "BOOLEAN",
    "Image":      "IMAGE",
    "Latent":     "LATENT",
    "Condition":  "CONDITIONING",
    "VAE":        "VAE",
    "Model":      "MODEL",
    "Clip":       "CLIP",
    "Mask":       "MASK",
}

NODE_CLASS_MAPPINGS = {"GateNode": GateNode}
NODE_DISPLAY_NAME_MAPPINGS = {"GateNode": "Trigger"}

for name, type_str in WAIT_TYPES.items():
    cls_name = f"Wait{name}Node"
    node_cls = make_wait_node(name, type_str)
    NODE_CLASS_MAPPINGS[cls_name] = node_cls
    NODE_DISPLAY_NAME_MAPPINGS[cls_name] = f"Wait ({name})"