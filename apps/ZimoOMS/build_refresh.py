#!/usr/bin/env python3
"""Step 3: fetch full field structures into worksheetContext.json."""
import json, os
from buildlib import call, load_ctx, HERE

WSCTX = os.path.join(HERE, "worksheetContext.json")

def main():
    ctx = load_ctx()
    wsctx = {}
    for name, wid in ctx["worksheetIdByName"].items():
        res = call("get_worksheet_structure", {"worksheet_id": wid})
        data = res.get("data", res)
        controls = data.get("controls", data.get("fields", []))
        fields = []
        for c in controls:
            opts = []
            for o in c.get("options", []) or []:
                opts.append({"value": o.get("value"), "key": o.get("key")})
            fields.append({
                "name": c.get("name"),
                "alias": c.get("alias"),
                "id": c.get("id") or c.get("controlId"),
                "type": c.get("type"),
                "dataSource": c.get("dataSource", ""),
                "options": opts,
            })
        wsctx[name] = {"worksheetId": wid, "fields": fields}
        print(f"{name}: {len(fields)} fields")
    with open(WSCTX, "w") as f:
        json.dump(wsctx, f, ensure_ascii=False, indent=1)
    print("WROTE", WSCTX)

if __name__ == "__main__":
    main()
