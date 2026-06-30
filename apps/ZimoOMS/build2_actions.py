#!/usr/bin/env python3
"""Step 4: create custom actions."""
import json, os
from buildlib import call, load_ctx, save_ctx, HERE

WSCTX = json.load(open(os.path.join(HERE, "worksheetContext.json")))
IDS = {n: WSCTX[n]["worksheetId"] for n in WSCTX}
REVNAME = {v: k for k, v in IDS.items()}

def fid(table, name):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            return f["id"]
    raise KeyError(f"{table}.{name}")

def falias(table, name):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            return f["alias"] or f["id"]
    raise KeyError(f"{table}.{name}")

def okey(table, name, value):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            for o in f["options"]:
                if o["value"] == value:
                    return o["key"]
    raise KeyError(f"{table}.{name}={value}")

def rev_rel_id(source, target_name):
    """reverse relation field id on `source` table that points to target_name."""
    for f in WSCTX[source]["fields"]:
        if f["dataSource"] == IDS.get(target_name) and f["name"] == target_name:
            return f["id"]
    # fallback: any field pointing to target
    for f in WSCTX[source]["fields"]:
        if f["dataSource"] == IDS.get(target_name):
            return f["id"]
    raise KeyError(f"reverse {source}->{target_name}")

def cond(table, field, op, value):
    return {"type": "condition", "field": fid(table, field), "operator": op, "value": value}

def grp(*conds, logic="AND"):
    return {"type": "group", "logic": logic, "children": list(conds)}

PLAN = {
 "订单": [
   {"name": "派工测量", "type": "createRelatedRecord", "relationField": rev_rel_id("订单","测量单"),
    "enableWhen": grp(cond("订单","订单状态","eq", okey("订单","订单状态","待测量")))},
   {"name": "同步工厂", "type": "createRelatedRecord", "relationField": rev_rel_id("订单","生产单"),
    "enableWhen": grp(cond("订单","订单状态","eq", okey("订单","订单状态","待生产")))},
   {"name": "安排发货", "type": "createRelatedRecord", "relationField": rev_rel_id("订单","物流单"),
    "enableWhen": grp(cond("订单","订单状态","eq", okey("订单","订单状态","待发货")))},
   {"name": "派工安装", "type": "createRelatedRecord", "relationField": rev_rel_id("订单","安装单"),
    "enableWhen": grp(cond("订单","订单状态","eq", okey("订单","订单状态","待安装")))},
   {"name": "登记回款", "type": "createRelatedRecord", "relationField": rev_rel_id("订单","收款记录"),
    "enableWhen": grp(cond("订单","收款状态","ne", okey("订单","收款状态","已结清")))},
 ],
 "测量单": [
   {"name": "提交测量结果", "type": "updateCurrentRecord",
    "updateFields": [falias("测量单",n) for n in ["测量状态","实际测量时间","现场尺寸","是否需复尺","测量图纸"]],
    "enableWhen": grp(cond("测量单","测量状态","in", [okey("测量单","测量状态","待预约"), okey("测量单","测量状态","已预约")]))},
 ],
 "生产单": [
   {"name": "更新生产进度", "type": "updateCurrentRecord",
    "updateFields": [falias("生产单",n) for n in ["生产状态","生产进度","实际完工日期","生产备注"]]},
 ],
 "物流单": [
   {"name": "确认发货", "type": "updateCurrentRecord",
    "updateFields": [falias("物流单",n) for n in ["物流状态","物流公司","运单号","发货日期","预计到达日期"]],
    "enableWhen": grp(cond("物流单","物流状态","eq", okey("物流单","物流状态","待发货")))},
 ],
 "安装单": [
   {"name": "提交安装结果", "type": "updateCurrentRecord",
    "updateFields": [falias("安装单",n) for n in ["安装状态","实际安装时间","安装照片","客户签字","验收结果"]],
    "enableWhen": grp(cond("安装单","安装状态","in", [okey("安装单","安装状态","待派工"), okey("安装单","安装状态","已派工"), okey("安装单","安装状态","安装中")]))},
   {"name": "确认验收", "type": "updateCurrentRecord",
    "updateFields": [falias("安装单",n) for n in ["验收结果","客户评分"]],
    "enableWhen": grp(cond("安装单","安装状态","eq", okey("安装单","安装状态","已安装")))},
 ],
 "售后工单": [
   {"name": "提交处理结果", "type": "updateCurrentRecord",
    "updateFields": [falias("售后工单",n) for n in ["工单状态","处理方案","处理结果","回访满意度"]]},
 ],
}

def main():
    ctx = load_ctx()
    amap = ctx.get("actionIdByName", {})
    for table, actions in PLAN.items():
        res = call("create_custom_actions", {"worksheet_id": IDS[table], "actions": actions})
        data = res.get("data", res)
        print(table, "->", json.dumps(data, ensure_ascii=False)[:200])
        # capture ids
        items = data if isinstance(data, list) else data.get("actions", data.get("list", []))
        if isinstance(items, list):
            for a in items:
                nm = a.get("name"); aid = a.get("id") or a.get("actionId")
                if nm and aid:
                    amap[f"{table}-{nm}"] = aid
        ctx["actionIdByName"] = amap
        save_ctx(ctx)
    print("DONE actions:", len(amap))

if __name__ == "__main__":
    main()
