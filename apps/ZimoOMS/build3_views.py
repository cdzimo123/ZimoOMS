#!/usr/bin/env python3
"""Step 5: create views."""
import json, os
from buildlib import call, load_ctx, save_ctx, HERE

WSCTX = json.load(open(os.path.join(HERE, "worksheetContext.json")))
IDS = {n: WSCTX[n]["worksheetId"] for n in WSCTX}

def fid(table, name):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            return f["id"]
    raise KeyError(f"{table}.{name}")

def okey(table, name, value):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            for o in f["options"]:
                if o["value"] == value:
                    return o["key"]
    raise KeyError(f"{table}.{name}={value}")

def C(table, field, op, value):
    return {"type": "condition", "field": fid(table, field), "operator": op, "value": value}

def G(table, *conds, logic="AND"):
    return {"type": "group", "logic": logic, "children": list(conds)}

def keys(table, field, *vals):
    return [okey(table, field, v) for v in vals]

VIEWS = {
 "订单": [
   {"name": "待审核", "type": "table", "filter": G("订单", C("订单","订单状态","eq", okey("订单","订单状态","待审核")))},
   {"name": "生产交付跟踪", "type": "kanban", "config": {"groupField": fid("订单","订单状态")}},
   {"name": "待收款订单", "type": "table", "filter": G("订单", C("订单","收款状态","in", keys("订单","收款状态","未收款","部分收款","已逾期")))},
 ],
 "测量单": [
   {"name": "待办测量", "type": "table", "filter": G("测量单", C("测量单","测量状态","in", keys("测量单","测量状态","待预约","已预约")))},
   {"name": "测量看板", "type": "kanban", "config": {"groupField": fid("测量单","测量状态")}},
 ],
 "生产单": [
   {"name": "生产看板", "type": "kanban", "config": {"groupField": fid("生产单","生产状态")}},
   {"name": "在产订单", "type": "table", "filter": G("生产单", C("生产单","生产状态","in", keys("生产单","生产状态","排产中","生产中")))},
 ],
 "物流单": [
   {"name": "待发货", "type": "table", "filter": G("物流单", C("物流单","物流状态","eq", okey("物流单","物流状态","待发货")))},
   {"name": "运输中", "type": "table", "filter": G("物流单", C("物流单","物流状态","eq", okey("物流单","物流状态","运输中")))},
 ],
 "安装单": [
   {"name": "安装看板", "type": "kanban", "config": {"groupField": fid("安装单","安装状态")}},
   {"name": "待派工", "type": "table", "filter": G("安装单", C("安装单","安装状态","eq", okey("安装单","安装状态","待派工")))},
 ],
 "售后工单": [
   {"name": "待处理工单", "type": "table", "filter": G("售后工单", C("售后工单","工单状态","in", keys("售后工单","工单状态","待受理","处理中")))},
   {"name": "售后看板", "type": "kanban", "config": {"groupField": fid("售后工单","工单状态")}},
 ],
 "收款计划": [
   {"name": "待收款", "type": "table", "filter": G("收款计划", C("收款计划","收款状态","in", keys("收款计划","收款状态","待收款","部分收款")))},
   {"name": "逾期应收", "type": "table", "filter": G("收款计划", C("收款计划","收款状态","eq", okey("收款计划","收款状态","已逾期")))},
 ],
 "经销商": [
   {"name": "合作中", "type": "table", "filter": G("经销商", C("经销商","合作状态","eq", okey("经销商","合作状态","合作中")))},
 ],
 "产品": [
   {"name": "产品图册", "type": "gallery"},
   {"name": "在售产品", "type": "table", "filter": G("产品", C("产品","上架状态","eq", okey("产品","上架状态","在售")))},
 ],
}

def main():
    ctx = load_ctx()
    vmap = ctx.get("viewIdByName", {})
    for table, views in VIEWS.items():
        res = call("create_view", {"worksheet_id": IDS[table], "views": views})
        data = res.get("data", res)
        items = data if isinstance(data, list) else data.get("views", data.get("list", []))
        got = []
        if isinstance(items, list):
            for v in items:
                nm = v.get("name"); vid = v.get("id") or v.get("viewId")
                if nm and vid:
                    vmap[f"{table}-{nm}"] = vid; got.append(nm)
        print(table, "->", got if got else json.dumps(data, ensure_ascii=False)[:160])
        ctx["viewIdByName"] = vmap
        save_ctx(ctx)
    print("DONE views:", len(vmap))

if __name__ == "__main__":
    main()
