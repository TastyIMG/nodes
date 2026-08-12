import json


class JsonViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("TASTY_JSON", {"forceInput": True}),
            },
            "optional": {
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("TASTY_JSON", "TRIGGER")
    RETURN_NAMES = ("json_string", "trigger")
    OUTPUT_NODE = True
    FUNCTION = "execute"
    CATEGORY = "Tasty/Utils"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, json_string, trigger=None):
        try:
            parsed = json.loads(json_string)
            pretty = json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, TypeError):
            pretty = str(json_string)

        return {
            "ui": {"text": [pretty]},
            "result": (json_string, "done")
        }
