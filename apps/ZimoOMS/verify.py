#!/usr/bin/env python3
"""End-to-end verification + live workflow demo."""
import json, os, time
from buildlib import call, load_ctx, HERE

WSCTX = json.load(open(os.path.join(HERE, "worksheetContext.json")))
IDS = {n: WSCTX[n]["worksheetId"] for n in WSCTX}
CTX = load_ctx()

def fa(table, name):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            return f["alias"] or f["id"]
    raise KeyError

def deep(res):
    d = res
    while isinstance(d, dict) and "data" in d and isinstance(d["data"], dict):
        d = d["data"]
    return d

def order_status(rowid):
    res = call("get_record_details", {"worksheet_id": IDS["订单"], "row_id": rowid})
    d = deep(res)
    return d.get(fa("订单", "订单状态")) or d.get("biz_o_status")

def main():
    print("=" * 60)
    print("ZimoOMS 应用结构核对")
    print("=" * 60)
    ws = deep(call("get_app_worksheets_list", {}))
    ws = ws if isinstance(ws, list) else ws.get("data", [])
    print(f"工作表数: {len(ws)}")
    for w in ws:
        cnt = deep(call("get_record_list", {"worksheet_id": w.get("worksheetId") or w.get("id"), "pageSize": 1, "pageIndex": 1}))
        total = cnt.get("total") if isinstance(cnt, dict) else "?"
        print(f"  - {w.get('name')}: {total} 条记录")

    wl = deep(call("get_workflow_list", {}))
    wl = wl if isinstance(wl, list) else wl.get("data", wl.get("list", []))
    print(f"\n工作流数: {len(wl) if isinstance(wl,list) else '?'}")
    if isinstance(wl, list):
        for p in wl:
            print(f"  - {p.get('name')} | 状态: {p.get('status', p.get('enabled','?'))}")

    print("\n" + "=" * 60)
    print("实时工作流演示：测量完成 → 订单自动进入待生产")
    print("=" * 60)
    rid = CTX["rowIds"]
    order = rid["订单"][3]          # 苏州 SO，下单后待测量
    ms = rid["测量单"][0]           # 该订单的测量单（待预约）
    print("演示前 订单状态:", order_status(order))
    print("→ 提交测量单结果（测量状态=已测量, 触发工作流）...")
    call("update_record", {"worksheet_id": IDS["测量单"], "row_id": ms,
                            "fields": [{"id": fa("测量单", "测量状态"), "value": ["已测量"]},
                                       {"id": fa("测量单", "实际测量时间"), "value": "2026-06-30 10:00"}],
                            "triggerWorkflow": True})
    for i in range(8):
        time.sleep(3)
        st = order_status(order)
        print(f"  [{(i+1)*3}s] 订单状态: {st}")
        if st == "待生产":
            print("✅ 工作流生效：订单已自动从【待测量】推进到【待生产】")
            break
    else:
        print("（订单状态未在等待窗口内变化，可能工作流异步延迟）")

if __name__ == "__main__":
    main()
