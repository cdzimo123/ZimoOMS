#!/usr/bin/env python3
"""Shared MCP client + helpers for building the ZimoOMS HAP app."""
import json, os, urllib.request, urllib.error, time

URL = ("https://api.mingdao.com/mcp?HAP-Appkey=b28e57130fb4572d"
       "&HAP-Sign=NzNjMDBjOWQ2NTYxMzQzMWMyMzk3YmM1N2QxYzM5MGE0Nzk2YzU1MmQ5OTE0MGY5ODJlZGEzZmRlOGFhOGI5OA==")

HERE = os.path.dirname(os.path.abspath(__file__))
CTX = os.path.join(HERE, "hap-context.json")

APP_ID = "46eecd9f-8c9e-4049-80f6-388d09e45ee3"
ORG_ID = "a526cdaf-65b7-407f-9412-e415136d9038"

_id = [100]

def rpc(method, params=None, retries=3):
    _id[0] += 1
    body = {"jsonrpc": "2.0", "id": _id[0], "method": method}
    if params is not None:
        body["params"] = params
    data = json.dumps(body, ensure_ascii=False).encode()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(URL, data=data, headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            })
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read().decode()
            if "data:" in raw[:40] and raw.lstrip().startswith("event:"):
                for line in raw.splitlines():
                    if line.startswith("data:"):
                        raw = line[5:].strip(); break
            return json.loads(raw)
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"RPC failed {method}: {last}")

def call(tool, args):
    if "appId" not in args:
        args = {"appId": APP_ID, **args}
    res = rpc("tools/call", {"name": tool, "arguments": args})
    if "result" not in res:
        raise RuntimeError(f"{tool} error: {json.dumps(res, ensure_ascii=False)}")
    content = res["result"].get("content", [])
    text = None
    for c in content:
        if c.get("type") == "text":
            text = c["text"]; break
    if text is None:
        return res["result"]
    try:
        return json.loads(text)
    except Exception:
        return {"_raw": text}

def load_ctx():
    if os.path.exists(CTX):
        with open(CTX) as f:
            return json.load(f)
    return {}

def save_ctx(ctx):
    with open(CTX, "w") as f:
        json.dump(ctx, f, ensure_ascii=False, indent=1)
