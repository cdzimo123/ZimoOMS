#!/usr/bin/env python3
"""Step 5b+7: custom pages (shells + components) and AI assistant."""
import json, os, uuid
from buildlib import call, load_ctx, save_ctx, HERE

WSCTX = json.load(open(os.path.join(HERE, "worksheetContext.json")))
IDS = {n: WSCTX[n]["worksheetId"] for n in WSCTX}
SECTIONS = {"总览": "6a43d913d949443a4eb633af", "订单": "6a43dc2c705c490a53f9c814",
            "交付": "6a43dc2c705c490a53f9c815", "售后应收": "6a43dc2c705c490a53f9c816",
            "资料": "6a43dc2c705c490a53f9c817"}

def fid(table, name):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            return f["id"]
    raise KeyError(f"{table}.{name}")

def uid():
    return str(uuid.uuid4())

def num(table, metric, agg, name, x, vid):
    return {"componentType": "chart", "name": name,
            "position": {"x": x, "y": 0, "w": 12, "h": 8},
            "config": {"worksheetId": IDS[table], "viewId": vid, "objectId": uid(),
                       "chartType": "numberChart", "dataScope": "all", "timeRange": "all",
                       "dimension": [], "values": [{"field": metric, "aggregation": agg}]}}

def chart(table, ctype, dims, vals, name, x, y, w, h, vid, extra=None):
    cfg = {"worksheetId": IDS[table], "viewId": vid, "objectId": uid(),
           "chartType": ctype, "dataScope": "all", "timeRange": "all",
           "dimension": dims, "values": vals}
    if extra:
        cfg.update(extra)
    return {"componentType": "chart", "name": name,
            "position": {"x": x, "y": y, "w": w, "h": h}, "config": cfg}

def section(title, y):
    return {"componentType": "section", "name": title,
            "position": {"x": 0, "y": y, "w": 48, "h": 2}}

def viewcomp(table, viewkey, vmap, title, y, h=13):
    return {"componentType": "view", "position": {"x": 0, "y": y, "w": 48, "h": h},
            "config": {"worksheetId": IDS[table], "viewId": vmap[viewkey], "objectId": uid(), "title": title}}

def textcomp(html, y, h=4):
    return {"componentType": "text", "position": {"x": 0, "y": y, "w": 48, "h": h},
            "config": {"content": html}}

PAGES = [
  ("经营总览看板", "dashboard", "总览", "sys_control-panel_traffic"),
  ("应收回款看板", "dashboard", "总览", "sys_control-panel_traffic"),
  ("订单作业台", "workspace", "订单", "2_3_statistics"),
  ("经销商门户", "workspace", "订单", "2_3_statistics"),
  ("安装任务台", "workspace", "交付", "2_3_statistics"),
]

def main():
    ctx = load_ctx()
    pmap = ctx.get("customPageIdByName", {})
    vmap = ctx["viewIdByName"]

    # 1. create page shells
    to_create = [{"type": "customPage", "name": n, "icon": ic, "sectionId": SECTIONS[sec]}
                 for n, pt, sec, ic in PAGES if n not in pmap]
    if to_create:
        res = call("create_app_items", {"items": to_create})
        data = res.get("data", res)
        items = data if isinstance(data, list) else data.get("items", data.get("list", []))
        for it in items:
            nm = it.get("name"); pid = it.get("id") or it.get("pageId") or it.get("workSheetId")
            if nm and pid:
                pmap[nm] = pid
        ctx["customPageIdByName"] = pmap; save_ctx(ctx)
    print("pages:", pmap)

    # 2. AI assistant
    cmap = ctx.get("chatbotIdByName", {})
    if "订单助手" not in cmap:
        res = call("create_chatbot", {
            "name": "订单助手", "sectionId": SECTIONS["总览"], "icon": "17_6_reddit",
            "description": "查询订单进度、交期、应收对账与售后状态",
            "welcomeMessage": "您好！我是订单助手，可以帮您查询订单进度、交期、应收对账与售后工单状态。",
            "presetQuestions": ["查一下待安装的订单", "本月销售额和回款额是多少", "有哪些逾期应收", "苏州优家定制的订单进度", "待处理的售后工单有哪些"],
            "prompt": "你是紫盟经销订单全流程应用的智能助手。基于应用内订单、收款计划、收款记录、售后工单等数据，帮助内部员工和经销商查询订单进度、交期、应收对账、回款情况与售后状态。回答需简洁准确，涉及金额时给出汇总。"})
        data = res.get("data", res)
        cid = data.get("id") or data.get("chatbotId") if isinstance(data, dict) else None
        if cid:
            cmap["订单助手"] = cid
        ctx["chatbotIdByName"] = cmap; save_ctx(ctx)
    print("chatbot:", cmap)

    # 3. configure components
    ov = vmap["订单-全部"]; pp = vmap["收款计划-全部"]; pa = vmap["收款记录-全部"]
    rowid = "rowid"
    comps_overview = [
        num("订单", rowid, "COUNT", "订单总数", 0, ov),
        num("订单", fid("订单","订单总金额"), "SUM", "销售总额", 12, ov),
        num("订单", fid("订单","已收金额"), "SUM", "已回款", 24, ov),
        num("订单", fid("订单","未收金额"), "SUM", "未回款", 36, ov),
        chart("订单", "pieChart", [{"field": fid("订单","订单状态")}], [{"field": rowid, "aggregation": "COUNT"}], "订单状态分布", 0, 8, 24, 10, ov),
        chart("订单", "barChart", [{"field": fid("订单","关联经销商")}], [{"field": fid("订单","订单总金额"), "aggregation": "SUM"}], "各经销商销售额", 24, 8, 24, 10, ov),
        chart("订单", "lineChart", [{"field": fid("订单","下单日期"), "granularity": 3}], [{"field": fid("订单","订单总金额"), "aggregation": "SUM"}], "月度下单趋势", 0, 18, 24, 10, ov),
        chart("订单", "pivotTable", [], [{"field": fid("订单","订单总金额"), "aggregation": "SUM"}], "订单金额透视", 24, 18, 24, 10, ov,
              extra={"rows": [{"field": fid("订单","订单状态")}], "columns": [{"field": fid("订单","订单来源")}]}),
    ]
    comps_recv = [
        num("收款计划", fid("收款计划","应收金额"), "SUM", "应收总额", 0, pp),
        num("收款计划", fid("收款计划","已收金额"), "SUM", "已收金额", 12, pp),
        num("收款计划", fid("收款计划","未收金额"), "SUM", "未收金额", 24, pp),
        num("收款记录", rowid, "COUNT", "回款笔数", 36, pa),
        chart("收款计划", "pieChart", [{"field": fid("收款计划","收款状态")}], [{"field": rowid, "aggregation": "COUNT"}], "收款状态分布", 0, 8, 24, 10, pp),
        chart("收款计划", "barChart", [{"field": fid("收款计划","收款节点")}], [{"field": fid("收款计划","应收金额"), "aggregation": "SUM"}], "各节点应收金额", 24, 8, 24, 10, pp),
        chart("收款记录", "lineChart", [{"field": fid("收款记录","收款日期"), "granularity": 3}], [{"field": fid("收款记录","收款金额"), "aggregation": "SUM"}], "回款趋势", 0, 18, 48, 10, pa),
    ]
    comps_orderdesk = [
        section("订单作业台 · 待办", 0),
        viewcomp("订单", "订单-待审核", vmap, "待审核订单", 2),
        viewcomp("订单", "订单-生产交付跟踪", vmap, "生产交付跟踪", 15),
        viewcomp("收款计划", "收款计划-逾期应收", vmap, "逾期应收", 28),
    ]
    comps_portal = [
        section("经销商门户", 0),
        textcomp("<h3>欢迎使用紫盟经销商门户</h3><p>在这里您可以查看订单进度、应收对账，并发起售后申请。</p>", 2),
        viewcomp("订单", "订单-全部", vmap, "我的订单", 6),
        viewcomp("售后工单", "售后工单-待处理工单", vmap, "我的售后工单", 19),
    ]
    comps_install = [
        section("安装任务台", 0),
        viewcomp("安装单", "安装单-待派工", vmap, "待派工安装", 2),
        viewcomp("安装单", "安装单-安装看板", vmap, "安装看板", 15),
    ]
    page_components = {
        "经营总览看板": comps_overview, "应收回款看板": comps_recv,
        "订单作业台": comps_orderdesk, "经销商门户": comps_portal, "安装任务台": comps_install,
    }
    done = ctx.get("pagesConfigured", [])
    for pname, comps in page_components.items():
        if pname in done:
            print("skip configured", pname); continue
        res = call("update_custom_page", {"page_id": pmap[pname], "components": comps})
        print(pname, "->", json.dumps(res.get("data", res), ensure_ascii=False)[:120])
        done.append(pname); ctx["pagesConfigured"] = done; save_ctx(ctx)
    print("PAGES DONE")

if __name__ == "__main__":
    main()
