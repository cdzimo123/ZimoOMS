#!/usr/bin/env python3
"""Clean self-contained live workflow demo: fresh order -> measurement done -> order auto-advances."""
import json, os, time
from buildlib import call, load_ctx, HERE

WSCTX = json.load(open(os.path.join(HERE, "worksheetContext.json")))
IDS = {n: WSCTX[n]["worksheetId"] for n in WSCTX}
CTX = load_ctx()

def fa(table, name):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            return f["alias"] or f["id"]
    raise KeyError(table + name)

def deep(r):
    while isinstance(r, dict) and "data" in r and isinstance(r["data"], dict):
        r = r["data"]
    return r

def newest(table):
    d = deep(call("get_record_list", {"worksheet_id": IDS[table], "pageSize": 1, "pageIndex": 1}))
    return d["rows"][0]

def ostatus(rowid):
    d = deep(call("get_record_details", {"worksheet_id": IDS["订单"], "row_id": rowid}))
    s = d.get(fa("订单", "订单状态"))
    return s[0]["value"] if isinstance(s, list) and s else s

def main():
    dealer = CTX["rowIds"]["经销商"][0]
    print("1) 新建演示订单（状态=待测量）")
    call("batch_create_records", {"worksheet_id": IDS["订单"], "triggerWorkflow": False, "rows": [{"fields": [
        {"id": fa("订单", "关联经销商"), "value": [dealer]},
        {"id": fa("订单", "下单日期"), "value": "2026-06-30"},
        {"id": fa("订单", "订单状态"), "value": ["待测量"]},
        {"id": fa("订单", "收货联系人"), "value": "演示客户"},
        {"id": fa("订单", "订单总金额"), "value": 9999},
        {"id": fa("订单", "是否需要测量"), "value": 1},
    ]}]})
    order = newest("订单")
    orow = order.get("rowId") or order.get("rowid") or order.get("_id")
    print("   订单编号:", order.get(fa("订单", "订单编号")), "| rowid:", orow[:10], "| 状态:", ostatus(orow))

    print("2) 为该订单新建测量单（状态=待预约）")
    call("batch_create_records", {"worksheet_id": IDS["测量单"], "triggerWorkflow": False, "rows": [{"fields": [
        {"id": fa("测量单", "关联订单"), "value": [orow]},
        {"id": fa("测量单", "测量状态"), "value": ["待预约"]},
        {"id": fa("测量单", "测量地址"), "value": "演示地址"},
    ]}]})
    ms = newest("测量单")
    msrow = ms.get("rowId") or ms.get("rowid") or ms.get("_id")
    print("   测量单号:", ms.get(fa("测量单", "测量单号")), "| rowid:", msrow[:10])

    print("3) 提交测量结果：测量状态 -> 已测量（触发工作流 [测量完成联动]）")
    call("update_record", {"worksheet_id": IDS["测量单"], "row_id": msrow, "triggerWorkflow": True,
                            "fields": [{"id": fa("测量单", "测量状态"), "value": ["已测量"]},
                                       {"id": fa("测量单", "实际测量时间"), "value": "2026-06-30 10:30"}]})
    print("4) 轮询订单状态，等待工作流自动推进 待测量 -> 待生产")
    ok = False
    for i in range(10):
        time.sleep(3)
        st = ostatus(orow)
        print(f"   [{(i+1)*3:>2}s] 订单状态 = {st}")
        if st == "待生产":
            ok = True
            break
    print("\n" + ("✅ 工作流实时生效：测量完成后订单已自动进入【待生产】" if ok else "⚠️ 未在窗口内观测到状态变化"))

if __name__ == "__main__":
    main()
