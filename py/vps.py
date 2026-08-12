import requests
import json


class VPSWorkflowNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vps_url": ("STRING", {"default": "http://98.86.30.158:3733"}),
                "endpoint": ("STRING", {"default": "/generate"}),
                "api_key": ("STRING", {"default": "12345"}),
                "modifier": (["Image2Image", "Text2Image", "Upscale", "Inpaint"], {}),
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "negative_prompt": ("STRING", {"default": "watermark, text", "multiline": True}),
            },
            "optional": {
                "input_image_url": ("STRING", {"default": ""}),
                "ckpt_name": ("STRING", {"default": "v1-5-pruned-emaonly-fp16.safetensors"}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 150}),
                "cfg_scale": ("FLOAT", {"default": 8.0, "min": 0.0, "max": 30.0, "step": 0.5}),
                "sampler_name": ("STRING", {"default": "dpmpp_2m"}),
                "request_id": ("STRING", {"default": ""}),
                "webhook_url": ("STRING", {"default": ""}),
                "extra_params_json": ("STRING", {"default": "{}"}),
                "trigger": ("TRIGGER",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "TRIGGER")
    RETURN_NAMES = ("response_json", "request_id", "status_code", "trigger")
    FUNCTION = "execute"
    CATEGORY = "utils/api"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    def execute(self, vps_url, endpoint, api_key, modifier, prompt, negative_prompt,
                input_image_url="", ckpt_name="v1-5-pruned-emaonly-fp16.safetensors",
                steps=20, cfg_scale=8.0, sampler_name="dpmpp_2m", request_id="",
                webhook_url="", extra_params_json="{}", trigger=None):

        # ── Build payload (matches your curl structure) ──
        payload = {
            "input": {
                "request_id": request_id,
                "modifier": modifier,
                "modifications": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "ckpt_name": ckpt_name,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "sampler_name": sampler_name,
                },
            }
        }

        # ── Only include image if provided ──
        if input_image_url.strip():
            payload["input"]["modifications"]["input_image"] = input_image_url.strip()

        # ── Only include webhook if provided ──
        if webhook_url.strip():
            try:
                extra = json.loads(extra_params_json)
            except Exception:
                extra = {}

            payload["input"]["webhook"] = {
                "url": webhook_url.strip(),
                "extra_params": extra,
            }

        # ── Hit VPS ──
        url = f"{vps_url.rstrip('/')}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": api_key,
        }

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=120)
            resp = r.text

            # Try to extract request_id from response
            out_id = request_id
            try:
                parsed = json.loads(resp)
                out_id = parsed.get("request_id", parsed.get("id", request_id))
            except Exception:
                pass

            return (resp, str(out_id), r.status_code, "done")

        except requests.exceptions.Timeout:
            return (json.dumps({"node": "VPSWorkflowNode", "error": "Request timed out (120s)"}), request_id, 408, "done")
        except requests.exceptions.ConnectionError:
            return (json.dumps({"node": "VPSWorkflowNode", "error": f"Cannot reach {url}"}), request_id, 503, "done")
        except Exception as e:
            return (json.dumps({"node": "VPSWorkflowNode", "error": str(e)}), request_id, 500, "done")


NODE_CLASS_MAPPINGS = {"VPSWorkflowNode": VPSWorkflowNode}
NODE_DISPLAY_NAME_MAPPINGS = {"VPSWorkflowNode": "VPS Workflow"}