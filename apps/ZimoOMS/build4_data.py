#!/usr/bin/env python3
"""Step 6: sample data."""
import json, os, sys
from buildlib import call, load_ctx, save_ctx, HERE

WSCTX = json.load(open(os.path.join(HERE, "worksheetContext.json")))
IDS = {n: WSCTX[n]["worksheetId"] for n in WSCTX}

def fa(table, name):
    for f in WSCTX[table]["fields"]:
        if f["name"] == name:
            return f["alias"] or f["id"]
    raise KeyError(f"{table}.{name}")

def row(table, **kv):
    fields = []
    for name, val in kv.items():
        fields.append({"id": fa(table, name), "value": val})
    return {"fields": fields}

def create(table, rows):
    res = call("batch_create_records", {"worksheet_id": IDS[table], "rows": rows, "triggerWorkflow": False})
    data = res.get("data", res)
    return data

def extract_ids(table, n):
    """fetch latest n record ids ordered by ctime asc fallback."""
    res = call("get_record_list", {"worksheet_id": IDS[table], "pageSize": 200, "pageIndex": 1})
    data = res.get("data", res)
    recs = data.get("rows", data.get("records", data if isinstance(data, list) else []))
    ids = [r.get("rowid") or r.get("rowId") or r.get("id") for r in recs]
    return recs, ids

D, R, F2 = "经销商", "产品", "工厂"

def main():
    ctx = load_ctx()
    rid = ctx.get("rowIds", {})

    if "经销商" not in rid:
        create(D, [
          row(D, 经销商名称="杭州家居体验馆", 联系人="王磊", 联系电话="13805710001", 电子邮箱="hz@dealer.com", 详细地址="杭州市西湖区文三路100号", 经销商等级="战略", 合作状态="合作中", 信用额度=500000, 已用额度=180000),
          row(D, 经销商名称="上海品质生活馆", 联系人="李婷", 联系电话="13905720002", 电子邮箱="sh@dealer.com", 详细地址="上海市徐汇区漕河泾88号", 经销商等级="核心", 合作状态="合作中", 信用额度=400000, 已用额度=120000),
          row(D, 经销商名称="苏州优家定制", 联系人="陈伟", 联系电话="13705730003", 详细地址="苏州市工业园区星海街9号", 经销商等级="普通", 合作状态="合作中", 信用额度=200000),
          row(D, 经销商名称="南京筑家空间", 联系人="赵敏", 联系电话="13605740004", 详细地址="南京市鼓楼区中山路200号", 经销商等级="潜在", 合作状态="暂停", 信用额度=100000),
        ])
        _, ids = extract_ids(D, 4); rid[D] = ids; save_ctx({**ctx, "rowIds": rid})
        print("dealers", ids)

    if R not in rid:
        create(R, [
          row(R, 产品名称="整体橱柜-现代简约", 产品分类="橱柜", 品牌="紫盟", 规格型号="L型3.6m", 计量单位="套", 销售单价=12000, 成本单价=7200, 标准交期天数=25, 是否需要测量=1, 是否需要安装=1, 上架状态="在售"),
          row(R, 产品名称="入墙衣柜-北欧", 产品分类="衣柜", 品牌="紫盟", 规格型号="平开门", 计量单位="平方米", 销售单价=1800, 成本单价=1050, 标准交期天数=20, 是否需要测量=1, 是否需要安装=1, 上架状态="在售"),
          row(R, 产品名称="实木复合门", 产品分类="木门", 品牌="紫盟", 规格型号="2100x900", 计量单位="件", 销售单价=2600, 成本单价=1500, 标准交期天数=18, 是否需要安装=1, 上架状态="在售"),
          row(R, 产品名称="断桥铝门窗", 产品分类="门窗", 品牌="紫盟", 规格型号="65系列", 计量单位="平方米", 销售单价=980, 成本单价=560, 标准交期天数=15, 是否需要测量=1, 是否需要安装=1, 上架状态="在售"),
          row(R, 产品名称="五金拉手套装", 产品分类="配件", 品牌="紫盟", 计量单位="套", 销售单价=120, 成本单价=45, 标准交期天数=3, 上架状态="在售"),
          row(R, 产品名称="岩板岛台台面", 产品分类="橱柜", 品牌="紫盟", 规格型号="2.4m", 计量单位="米", 销售单价=1500, 成本单价=900, 标准交期天数=22, 是否需要测量=1, 是否需要安装=1, 上架状态="在售"),
        ])
        _, ids = extract_ids(R, 6); rid[R] = ids; save_ctx({**ctx, "rowIds": rid})
        print("products", ids)

    if F2 not in rid:
        create(F2, [
          row(F2, 工厂名称="杭州中央工厂", 工厂类型="自有工厂", 对接人="孙强", 联系电话="13500010001", 详细地址="杭州市余杭区生产基地1号", 月产能=2000, 主营品类=["橱柜","衣柜"], 准时交付率=96, 合作状态="合作中"),
          row(F2, 工厂名称="佛山协作门窗厂", 工厂类型="外协工厂", 对接人="周杰", 联系电话="13500020002", 详细地址="佛山市南海区工业园18号", 月产能=1500, 主营品类=["门窗","木门"], 准时交付率=92, 合作状态="合作中"),
        ])
        _, ids = extract_ids(F2, 2); rid[F2] = ids; save_ctx({**ctx, "rowIds": rid})
        print("factories", ids)

    save_ctx({**ctx, "rowIds": rid})
    print("masters done")

if __name__ == "__main__":
    main()
