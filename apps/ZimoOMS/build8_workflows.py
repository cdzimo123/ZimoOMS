#!/usr/bin/env python3
"""Step 9-11: create + publish automation workflows."""
import json, os
from buildlib import call, load_ctx, save_ctx, HERE

WSCTX = json.load(open(os.path.join(HERE, "worksheetContext.json")))
IDS = {n: WSCTX[n]["worksheetId"] for n in WSCTX}
CTX = load_ctx()
ROLE = {r["roleName"]: r["roleId"] for r in CTX.get("roleContext", [])}

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

TRIG = {"nodeAlias": "trigger"}

def deep(res):
    d = res
    while isinstance(d, dict) and "data" in d and isinstance(d["data"], dict):
        d = d["data"]
    return d

def cond(node, fieldid, op, right):
    return {"left": {"kind": "field", "node": node, "fieldId": fieldid}, "op": op, "right": right}

def lit(v):
    return {"kind": "literal", "value": v}

def create_proc(name, desc, trigger):
    res = call("create_process", {"name": name, "description": desc, "trigger": trigger})
    data = deep(res)
    pid = data.get("processId") or data.get("id")
    talias = data.get("triggerAlias", "trigger")
    if not pid:
        raise RuntimeError(f"create_process failed {name}: {json.dumps(res, ensure_ascii=False)[:300]}")
    return pid, talias

def add_nodes(pid, nodes):
    res = call("batch_create_process_nodes", {"workflow_id": pid, "nodes": nodes})
    d = deep(res)
    if isinstance(d, dict) and d.get("error"):
        raise RuntimeError(f"nodes error: {json.dumps(d, ensure_ascii=False)[:400]}")
    return d

def publish(pid):
    res = call("publish_process", {"workflow_id": pid})
    return deep(res)

def linkage(name, child, child_status, done_value, order_target_value, notify_role):
    """worksheet_event on child: status==done_value -> find order -> set 订单状态=order_target_value -> notify."""
    desc = f"{child}状态变更为{done_value}时，自动回写关联订单状态为{order_target_value}并通知{notify_role}"
    trigger = {"triggerType": "worksheet_event", "nodeAlias": "trigger",
               "config": {"worksheetId": IDS[child], "event": "add_or_update",
                          "triggerFields": [fid(child, child_status)],
                          "filter": {"logic": "and", "items": [cond(TRIG, fid(child, child_status), "eq", lit(okey(child, child_status, done_value)))]}}}
    pid, ta = create_proc(name, desc, trigger)
    tref = {"nodeAlias": ta}
    nodes = [
      {"nodeAlias": "find_order", "nodeType": "get_single", "name": "查询关联订单",
       "description": "根据触发记录的关联订单找到订单主记录", "prevNode": tref,
       "config": {"worksheetId": IDS["订单"], "ifEmpty": "stop",
                  "filter": {"logic": "and", "items": [
                     {"left": {"kind": "field", "node": {"nodeAlias": "find_order"}, "fieldId": "rowid"},
                      "op": "eq",
                      "right": {"kind": "field", "node": tref, "fieldId": fid(child, "关联订单")}}]}}},
      {"nodeAlias": "set_order", "nodeType": "update_record", "name": f"更新订单状态为{order_target_value}",
       "description": f"将订单状态推进为{order_target_value}", "prevNode": {"nodeAlias": "find_order"},
       "config": {"target": {"kind": "record", "node": {"nodeAlias": "find_order"}},
                  "fields": [{"fieldId": fid("订单", "订单状态"), "op": "set", "value": lit(okey("订单", "订单状态", order_target_value))}]}},
      {"nodeAlias": "notify", "nodeType": "send_internal_notice", "name": f"通知{notify_role}",
       "description": f"通知{notify_role}订单已推进", "prevNode": {"nodeAlias": "set_order"},
       "config": {"recipients": [{"kind": "role", "roleId": ROLE[notify_role]}],
                  "title": name,
                  "content": {"kind": "template", "value": f"订单 $find_order-{fid('订单','订单编号')}$ 已进入【{order_target_value}】阶段，请及时跟进。"}}},
    ]
    r = add_nodes(pid, nodes)
    print(name, "nodes ->", json.dumps(r, ensure_ascii=False)[:140])
    p = publish(pid)
    print(name, "publish ->", json.dumps(p.get("data", p), ensure_ascii=False)[:160])
    return pid

def overdue():
    name = "应收逾期预警"
    desc = "收款计划应收日期到达时，若未结清则标记为已逾期并通知应收专员"
    trigger = {"triggerType": "date_field", "nodeAlias": "trigger",
               "config": {"worksheetId": IDS["收款计划"], "event": "add_or_update",
                          "dateFieldId": fid("收款计划", "应收日期"), "executeTime": "09:00:00",
                          "offset": {"days": 0},
                          "filter": {"logic": "and", "items": [cond(TRIG, fid("收款计划", "收款状态"), "in",
                                     lit([okey("收款计划","收款状态","待收款"), okey("收款计划","收款状态","部分收款")]))]}}}
    pid, ta = create_proc(name, desc, trigger)
    tref = {"nodeAlias": ta}
    nodes = [
      {"nodeAlias": "mark_overdue", "nodeType": "update_record", "name": "标记已逾期",
       "description": "将收款计划状态更新为已逾期", "prevNode": tref,
       "config": {"target": {"kind": "record", "node": tref},
                  "fields": [{"fieldId": fid("收款计划", "收款状态"), "op": "set", "value": lit(okey("收款计划", "收款状态", "已逾期"))}]}},
      {"nodeAlias": "notify", "nodeType": "send_internal_notice", "name": "通知应收专员催收",
       "description": "通知应收专员该应收节点已逾期", "prevNode": {"nodeAlias": "mark_overdue"},
       "config": {"recipients": [{"kind": "role", "roleId": ROLE["应收专员"]}],
                  "title": name,
                  "content": {"kind": "template", "value": f"收款计划 $trigger-{fid('收款计划','计划编号')}$（应收金额 $trigger-{fid('收款计划','应收金额')}$）已逾期，请及时催收。"}}},
    ]
    r = add_nodes(pid, nodes)
    print(name, "nodes ->", json.dumps(r, ensure_ascii=False)[:140])
    p = publish(pid)
    print(name, "publish ->", json.dumps(p.get("data", p), ensure_ascii=False)[:160])
    return pid

def main():
    ctx = load_ctx()
    wf = ctx.get("workflowIdByName", {})
    plan = [
      ("应收逾期预警", overdue),
      ("测量完成联动", lambda: linkage("测量完成联动", "测量单", "测量状态", "已测量", "待生产", "生产跟单员")),
      ("生产完工联动", lambda: linkage("生产完工联动", "生产单", "生产状态", "已完工", "待发货", "物流专员")),
      ("物流签收联动", lambda: linkage("物流签收联动", "物流单", "物流状态", "已签收", "待安装", "订单专员")),
      ("安装验收联动", lambda: linkage("安装验收联动", "安装单", "安装状态", "已验收", "已完成", "应收专员")),
    ]
    for nm, fn in plan:
        if nm in wf:
            print("skip", nm); continue
        try:
            pid = fn()
            wf[nm] = pid
            ctx["workflowIdByName"] = wf; save_ctx(ctx)
        except Exception as e:
            print("ERROR", nm, e)
    print("WORKFLOWS DONE:", list(wf.keys()))

if __name__ == "__main__":
    main()
