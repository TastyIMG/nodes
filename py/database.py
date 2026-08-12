import requests
import json


class D1QueryNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "account_id": ("STRING", {"default": ""}),
                "database_id": ("STRING", {"default": ""}),
                "api_token": ("STRING", {"default": ""}),
                "table_name": ("STRING", {"default": ""}),
            },
            "optional": {
                "columns": ("STRING", {"default": "*"}),
                "filter_column": ("STRING", {"default": ""}),
                "filter_value": ("STRING", {"default": ""}),
                "limit": ("INT", {"default": 100, "min": 1, "max": 10000}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "TRIGGER")
    RETURN_NAMES = ("rows_json", "columns_json", "row_count", "trigger")
    FUNCTION = "execute"
    CATEGORY = "utils/database"

    def execute(self, account_id, database_id, api_token, table_name,
                columns="*", filter_column="", filter_value="", limit=100):

        safe_table = "".join(c for c in table_name if c.isalnum() or c == "_")
        if not safe_table:
            return (json.dumps({"node": "D1QueryNode", "error": "Invalid table name"}), "[]", 0, "done")

        # Build SELECT
        cols = columns.strip() if columns.strip() else "*"
        sql = f"SELECT {cols} FROM {safe_table}"

        # Optional WHERE
        params = []
        if filter_column.strip() and filter_value.strip():
            safe_col = "".join(c for c in filter_column if c.isalnum() or c == "_")
            sql += f" WHERE {safe_col} = ?"
            params.append(filter_value.strip())

        sql += f" LIMIT {limit}"

        # Hit D1 REST API
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        payload = {"sql": sql}
        if params:
            payload["params"] = params

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=30)
            data = r.json()

            if not data.get("success", False):
                errors = data.get("errors", [{"message": "Unknown error"}])
                return (json.dumps({"node": "D1QueryNode", "error": errors}), "[]", 0, "done")

            results = data.get("result", [{}])[0]
            rows = results.get("results", [])
            col_names = list(rows[0].keys()) if rows else []

            rows_with_node = [{"node": "D1QueryNode", **row} for row in rows] if rows else []
            return (json.dumps(rows_with_node), json.dumps(col_names), len(rows), "done")

        except Exception as e:
            return (json.dumps({"node": "D1QueryNode", "error": str(e)}), "[]", 0, "done")


NODE_CLASS_MAPPINGS = {"D1QueryNode": D1QueryNode}
NODE_DISPLAY_NAME_MAPPINGS = {"D1QueryNode": "D1 Query"}