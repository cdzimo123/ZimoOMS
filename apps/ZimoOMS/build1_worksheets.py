#!/usr/bin/env python3
"""Step 2-3: create all worksheets with rich fields, capture IDs."""
import sys
from buildlib import call, load_ctx, save_ctx

SECTIONS = {
    "总览": "6a43d913d949443a4eb633af",
    "订单": "6a43dc2c705c490a53f9c814",
    "交付": "6a43dc2c705c490a53f9c815",
    "售后应收": "6a43dc2c705c490a53f9c816",
    "资料": "6a43dc2c705c490a53f9c817",
}

def options(items):
    out = []
    for i, it in enumerate(items):
        if isinstance(it, tuple):
            v, c = it
        else:
            v, c = it, None
        o = {"value": v, "index": i + 1}
        if c:
            o["color"] = c
        out.append(o)
    return out

# color shortcuts
R, G, Y, B, GR, O = "#F52222", "#00C345", "#FAD714", "#2D46C4", "#484848", "#FF9300"

def F(name, alias, ftype, title=False, req=False, opts=None, color=False,
      rel=None, multi=False, disp="dropdown", show=None, expr=None,
      autonum_prefix=None, rate_max=None, currency=True, fmt=None, textmode=None):
    f = {"name": name, "alias": alias, "type": ftype}
    if title:
        f["isTitle"] = True
    if req:
        f["required"] = True
    cfg = {}
    if opts is not None:
        f["options"] = options(opts)
        if color:
            cfg["isColorOptions"] = True
    if ftype == "Currency":
        cfg["code"] = "CNY"
        f["precision"] = 2
    if ftype == "Formula" and expr:
        cfg["expression"] = expr
        f["precision"] = 2
    if ftype == "AutoNumber":
        cfg["rules"] = [{"type": "text", "value": autonum_prefix or "NO"},
                         {"type": "sequence", "length": 4, "repeat": "never"}]
    if ftype == "Rating" and rate_max:
        f["max"] = rate_max
    if ftype == "Collaborator":
        cfg["isMultiple"] = multi
    if ftype in ("Date", "DateTime") and fmt:
        cfg["format"] = fmt
    if ftype == "Text" and textmode:
        cfg["textMode"] = textmode
    if rel:
        cfg["bidirectional"] = True
        cfg["isMultiple"] = multi
        cfg["displayMode"] = disp
        if show:
            cfg["showFields"] = show
        f["_rel"] = rel  # resolved to dataSource at build time
    if cfg:
        f["config"] = cfg
    return f

# title alias registry for relation showFields
TITLE = {
    "经销商": "biz_d_name", "产品": "biz_p_name", "工厂": "biz_fac_name",
    "订单": "biz_o_no", "订单明细": "biz_oi_no", "测量单": "biz_m_no",
    "生产单": "biz_pr_no", "物流单": "biz_l_no", "安装单": "biz_ins_no",
    "售后工单": "biz_as_no", "收款计划": "biz_pp_no", "收款记录": "biz_pa_no",
}

def rel(name, target, multi=False, disp="dropdown"):
    return F(name, f"biz_rel_{abs(hash((name,target)))%100000}", "Relation",
             rel=target, multi=multi, disp=disp, show=[TITLE[target]])

TABLES = [
 ("经销商", "13_2_business", "资料", "记录经销商主数据、信用与累计交易", [
    F("经销商名称","biz_d_name","Text",title=True,req=True),
    F("经销商编号","biz_d_no","AutoNumber",autonum_prefix="DLR"),
    F("联系人","biz_d_contact","Text"),
    F("联系电话","biz_d_phone","PhoneNumber"),
    F("电子邮箱","biz_d_email","Email"),
    F("所在区域","biz_d_region","Region"),
    F("详细地址","biz_d_addr","Text"),
    F("经销商等级","biz_d_level","SingleSelect",opts=[("战略",B),("核心",G),("普通",None),("潜在",Y)],color=True),
    F("合作状态","biz_d_status","SingleSelect",opts=[("合作中",G),("暂停",Y),("终止",GR)],color=True),
    F("信用额度","biz_d_credit","Currency"),
    F("已用额度","biz_d_usedcredit","Currency"),
    F("累计订单金额","biz_d_totorder","Currency"),
    F("累计回款金额","biz_d_totpaid","Currency"),
    F("开户银行","biz_d_bank","Text"),
    F("银行账号","biz_d_bankno","Text"),
    F("营业执照","biz_d_license","Attachment"),
    F("备注","biz_d_remark","Text",textmode="multiLine"),
 ]),
 ("产品", "12_2_book", "资料", "可下单产品/SKU 主数据", [
    F("产品名称","biz_p_name","Text",title=True,req=True),
    F("产品编码","biz_p_no","AutoNumber",autonum_prefix="SKU"),
    F("产品分类","biz_p_cat","SingleSelect",opts=["橱柜","衣柜","木门","门窗","配件","其他"]),
    F("品牌","biz_p_brand","Text"),
    F("规格型号","biz_p_spec","Text"),
    F("计量单位","biz_p_unit","SingleSelect",opts=["套","件","平方米","米","个"]),
    F("销售单价","biz_p_price","Currency"),
    F("成本单价","biz_p_cost","Currency"),
    F("标准交期天数","biz_p_lead","Number"),
    F("是否需要测量","biz_p_needm","Checkbox"),
    F("是否需要安装","biz_p_needi","Checkbox"),
    F("上架状态","biz_p_status","SingleSelect",opts=[("在售",G),("停售",GR)],color=True),
    F("产品图片","biz_p_img","Attachment"),
    F("产品简介","biz_p_desc","RichText"),
    F("备注","biz_p_remark","Text",textmode="multiLine"),
 ]),
 ("工厂", "22_1_factory", "资料", "生产工厂/供应商主数据", [
    F("工厂名称","biz_fac_name","Text",title=True,req=True),
    F("工厂编号","biz_fac_no","AutoNumber",autonum_prefix="FAC"),
    F("工厂类型","biz_fac_type","SingleSelect",opts=["自有工厂","外协工厂"]),
    F("对接人","biz_fac_contact","Text"),
    F("联系电话","biz_fac_phone","PhoneNumber"),
    F("所在区域","biz_fac_region","Region"),
    F("详细地址","biz_fac_addr","Text"),
    F("月产能","biz_fac_cap","Number"),
    F("主营品类","biz_fac_cats","MultipleSelect",opts=["橱柜","衣柜","木门","门窗","配件"]),
    F("准时交付率","biz_fac_otd","Number"),
    F("质量评分","biz_fac_rate","Rating",rate_max=5),
    F("合作状态","biz_fac_status","SingleSelect",opts=[("合作中",G),("暂停",Y),("终止",GR)],color=True),
    F("合作开始日期","biz_fac_since","Date"),
    F("备注","biz_fac_remark","Text",textmode="multiLine"),
 ]),
 ("订单", "1_1_task", "订单", "订单主表，贯穿全流程的状态主线", [
    F("订单编号","biz_o_no","AutoNumber",title=True,autonum_prefix="SO"),
    rel("关联经销商","经销商"),
    F("下单日期","biz_o_date","Date"),
    F("期望交付日期","biz_o_eta","Date"),
    F("订单状态","biz_o_status","SingleSelect",opts=[("待审核",Y),("已驳回",R),("待测量",B),("待生产",B),("待发货",O),("待安装",O),("已完成",G),("已取消",GR)],color=True),
    F("收货联系人","biz_o_recv","Text"),
    F("收货电话","biz_o_recvphone","PhoneNumber"),
    F("收货地区","biz_o_recvregion","Region"),
    F("收货地址","biz_o_recvaddr","Text"),
    F("是否需要测量","biz_o_needm","Checkbox"),
    F("是否需要安装","biz_o_needi","Checkbox"),
    F("订单总金额","biz_o_amount","Currency"),
    F("应收总额","biz_o_recv_total","Currency"),
    F("已收金额","biz_o_paid","Currency"),
    F("未收金额","biz_o_unpaid","Currency"),
    F("收款状态","biz_o_paystatus","SingleSelect",opts=[("未收款",GR),("部分收款",Y),("已结清",G),("已逾期",R)],color=True),
    F("订单来源","biz_o_source","SingleSelect",opts=["经销商门户","电话","线下","其他"]),
    F("销售负责人","biz_o_owner","Collaborator"),
    F("备注","biz_o_remark","Text",textmode="multiLine"),
    F("附件","biz_o_attach","Attachment"),
 ]),
 ("订单明细", "1_3_list", "订单", "订单下逐条产品明细", [
    F("明细编号","biz_oi_no","AutoNumber",title=True,autonum_prefix="SOI"),
    rel("关联订单","订单"),
    rel("关联产品","产品"),
    F("规格说明","biz_oi_spec","Text"),
    F("数量","biz_oi_qty","Number"),
    F("单价","biz_oi_price","Currency"),
    F("小计","biz_oi_subtotal","Formula",expr="$biz_oi_qty$ * $biz_oi_price$"),
    F("是否定制","biz_oi_custom","Checkbox"),
    F("明细状态","biz_oi_status","SingleSelect",opts=[("待生产",B),("生产中",O),("已完成",G)],color=True),
    F("备注","biz_oi_remark","Text",textmode="multiLine"),
 ]),
 ("测量单", "11_3_ruler", "交付", "上门测量任务与尺寸结果", [
    F("测量单号","biz_m_no","AutoNumber",title=True,autonum_prefix="MS"),
    rel("关联订单","订单"),
    F("测量状态","biz_m_status","SingleSelect",opts=[("待预约",Y),("已预约",B),("已测量",G),("已取消",GR)],color=True),
    F("预约测量时间","biz_m_booktime","DateTime"),
    F("实际测量时间","biz_m_realtime","DateTime"),
    F("测量员","biz_m_worker","Collaborator"),
    F("测量地址","biz_m_addr","Text"),
    F("现场尺寸","biz_m_size","RichText"),
    F("是否需复尺","biz_m_recheck","Checkbox"),
    F("测量图纸","biz_m_draw","Attachment"),
    F("备注","biz_m_remark","Text",textmode="multiLine"),
 ]),
 ("生产单", "22_1_factory", "交付", "同步到工厂的排产与生产进度", [
    F("生产单号","biz_pr_no","AutoNumber",title=True,autonum_prefix="PR"),
    rel("关联订单","订单"),
    rel("生产工厂","工厂"),
    F("生产状态","biz_pr_status","SingleSelect",opts=[("待排产",Y),("排产中",B),("生产中",O),("已完工",G),("已取消",GR)],color=True),
    F("同步工厂时间","biz_pr_synctime","DateTime"),
    F("计划开工日期","biz_pr_planstart","Date"),
    F("计划完工日期","biz_pr_planend","Date"),
    F("实际完工日期","biz_pr_realend","Date"),
    F("生产进度","biz_pr_progress","Number"),
    F("跟单员","biz_pr_owner","Collaborator"),
    F("生产备注","biz_pr_remark","Text",textmode="multiLine"),
    F("附件","biz_pr_attach","Attachment"),
 ]),
 ("物流单", "21_2_truck", "交付", "发货与物流签收记录", [
    F("物流单号","biz_l_no","AutoNumber",title=True,autonum_prefix="LG"),
    rel("关联订单","订单"),
    F("物流状态","biz_l_status","SingleSelect",opts=[("待发货",Y),("运输中",B),("已签收",G),("异常",R)],color=True),
    F("物流公司","biz_l_carrier","Text"),
    F("运单号","biz_l_trackno","Text"),
    F("发货日期","biz_l_shipdate","Date"),
    F("预计到达日期","biz_l_eta","Date"),
    F("实际签收日期","biz_l_signdate","Date"),
    F("收货人","biz_l_recv","Text"),
    F("收货电话","biz_l_recvphone","PhoneNumber"),
    F("运费","biz_l_fee","Currency"),
    F("物流专员","biz_l_owner","Collaborator"),
    F("备注","biz_l_remark","Text",textmode="multiLine"),
 ]),
 ("安装单", "9_2_tool", "交付", "安装派工、安装结果与验收", [
    F("安装单号","biz_ins_no","AutoNumber",title=True,autonum_prefix="IN"),
    rel("关联订单","订单"),
    F("安装状态","biz_ins_status","SingleSelect",opts=[("待派工",Y),("已派工",B),("安装中",O),("已安装",B),("已验收",G),("返工",R)],color=True),
    F("预约安装时间","biz_ins_booktime","DateTime"),
    F("实际安装时间","biz_ins_realtime","DateTime"),
    F("安装师傅","biz_ins_worker","Collaborator"),
    F("安装地址","biz_ins_addr","Text"),
    F("验收结果","biz_ins_accept","SingleSelect",opts=[("待验收",Y),("合格",G),("不合格",R)],color=True),
    F("客户签字","biz_ins_sign","Attachment"),
    F("安装照片","biz_ins_photo","Attachment"),
    F("客户评分","biz_ins_rate","Rating",rate_max=5),
    F("备注","biz_ins_remark","Text",textmode="multiLine"),
 ]),
 ("售后工单", "10_5_service", "售后应收", "售后问题受理、处理与回访", [
    F("工单编号","biz_as_no","AutoNumber",title=True,autonum_prefix="AS"),
    rel("关联订单","订单"),
    rel("关联经销商","经销商"),
    F("工单状态","biz_as_status","SingleSelect",opts=[("待受理",Y),("处理中",O),("待回访",B),("已关闭",G),("已升级",R)],color=True),
    F("问题类型","biz_as_type","SingleSelect",opts=["质量问题","物流破损","安装问题","缺件少件","其他"]),
    F("紧急程度","biz_as_urgency","SingleSelect",opts=[("低",GR),("中",Y),("高",O),("紧急",R)],color=True),
    F("问题描述","biz_as_desc","RichText"),
    F("期望解决时间","biz_as_expect","Date"),
    F("受理人","biz_as_owner","Collaborator"),
    F("处理方案","biz_as_plan","Text",textmode="multiLine"),
    F("处理结果","biz_as_result","SingleSelect",opts=[("已解决",G),("部分解决",Y),("无法解决",R)],color=True),
    F("回访满意度","biz_as_rate","Rating",rate_max=5),
    F("问题图片","biz_as_img","Attachment"),
    F("备注","biz_as_remark","Text",textmode="multiLine"),
 ]),
 ("收款计划", "7_1_money", "售后应收", "按付款节点拆分的应收节点", [
    F("计划编号","biz_pp_no","AutoNumber",title=True,autonum_prefix="PP"),
    rel("关联订单","订单"),
    F("收款节点","biz_pp_node","SingleSelect",opts=["定金","进度款一","进度款二","尾款"]),
    F("应收金额","biz_pp_amount","Currency"),
    F("已收金额","biz_pp_paid","Currency"),
    F("未收金额","biz_pp_unpaid","Currency"),
    F("应收日期","biz_pp_duedate","Date"),
    F("收款状态","biz_pp_status","SingleSelect",opts=[("待收款",Y),("部分收款",O),("已结清",G),("已逾期",R)],color=True),
    F("实际结清日期","biz_pp_cleardate","Date"),
    F("备注","biz_pp_remark","Text",textmode="multiLine"),
 ]),
 ("收款记录", "7_3_wallet", "售后应收", "实际回款流水", [
    F("收款单号","biz_pa_no","AutoNumber",title=True,autonum_prefix="PA"),
    rel("关联收款计划","收款计划"),
    rel("关联订单","订单"),
    F("收款金额","biz_pa_amount","Currency"),
    F("收款方式","biz_pa_method","SingleSelect",opts=["银行转账","微信","支付宝","现金","承兑汇票"]),
    F("收款日期","biz_pa_date","Date"),
    F("收款人","biz_pa_owner","Collaborator"),
    F("收款凭证","biz_pa_proof","Attachment"),
    F("备注","biz_pa_remark","Text",textmode="multiLine"),
 ]),
]

def layout_fields(fields):
    for i, f in enumerate(fields):
        f["layout"] = {"rowIndex": i // 2, "span": 6}
    return fields

def fetch_fields(wid):
    res = call("get_worksheet_structure", {"worksheet_id": wid})
    data = res.get("data", res)
    fmap = {}
    for fld in data.get("controls", data.get("fields", [])):
        a = fld.get("alias") or fld.get("controlId")
        fid = fld.get("controlId") or fld.get("fieldId") or fld.get("id")
        if a:
            fmap[a] = fid
    return fmap

def main():
    ctx = load_ctx()
    ws_id = ctx.get("worksheetIdByName", {})
    ws_fields = ctx.get("worksheetFields", {})  # name -> {alias: fieldId}
    # reconcile existing worksheets to avoid duplicates
    existing = call("get_app_worksheets_list", {}).get("data", [])
    for w in existing:
        nm = w.get("name") or w.get("workSheetName")
        wid = w.get("worksheetId") or w.get("id")
        if nm and wid and nm not in ws_id:
            ws_id[nm] = wid
    ctx["worksheetIdByName"] = ws_id
    for name, icon, section, desc, fields in TABLES:
        if name in ws_id:
            print(f"skip {name} (exists {ws_id[name]})")
            continue
        flds = []
        for f in fields:
            f = dict(f)
            if "_rel" in f:
                target = f.pop("_rel")
                if target not in ws_id:
                    raise RuntimeError(f"relation target {target} not created yet for {name}")
                f["dataSource"] = ws_id[target]
            flds.append(f)
        layout_fields(flds)
        args = {"name": name, "alias": "ws_" + flds[0]["alias"].split("_")[1],
                "sectionId": SECTIONS[section], "icon": icon, "remark": desc,
                "returnData": True, "fields": flds}
        res = call("create_worksheet", args)
        data = res.get("data", res)
        wid = data.get("worksheetId") or data.get("worksheetsId") or data.get("id")
        if not wid:
            print("UNEXPECTED RESPONSE:", res)
            raise RuntimeError(f"no worksheetId for {name}")
        ws_id[name] = wid
        # capture field alias->id
        fmap = {}
        for fld in data.get("fields", data.get("controls", [])):
            a = fld.get("alias") or fld.get("controlId")
            fid = fld.get("id") or fld.get("fieldId") or fld.get("controlId")
            if a:
                fmap[a] = fid
        if not fmap:
            fmap = fetch_fields(wid)
        ws_fields[name] = fmap
        # capture default view id
        views = ctx.get("viewIdByName", {})
        for v in data.get("views", []):
            views[f"{name}-{v.get('name')}"] = v.get("id")
        ctx["viewIdByName"] = views
        ctx["worksheetIdByName"] = ws_id
        ctx["worksheetFields"] = ws_fields
        save_ctx(ctx)
        print(f"created {name}: {wid} ({len(fmap)} fields captured)")
    save_ctx(ctx)
    print("DONE worksheets:", len(ws_id))

if __name__ == "__main__":
    main()
