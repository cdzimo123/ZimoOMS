#!/usr/bin/env python3
"""Step 8: roles."""
from buildlib import call, load_ctx, save_ctx

def gp(add=True, exp=True):
    return {"addRecord": add, "share": False, "import": False, "export": exp,
            "log": True, "attachmentDownload": True, "systemPrint": True, "discuss": True}

ROLES = [
  ("订单专员", "受理审核订单、维护订单全生命周期、向各环节派工协调", "general", "80", gp()),
  ("测量员", "接收测量派工、上门测量并回填尺寸数据", "general", "60", gp()),
  ("生产跟单员", "同步订单到工厂、跟踪排产与生产进度", "general", "60", gp()),
  ("物流专员", "安排发货、登记运单并跟踪签收", "general", "60", gp()),
  ("售后专员", "受理分派处理售后工单、回访关闭", "general", "60", gp()),
  ("应收专员", "维护收款计划、登记回款、对账与逾期催收", "general", "80", gp()),
  ("管理层", "查看经营与应收分析看板（只读）", "general", "20", gp(add=False)),
  ("安装师傅", "通过外部门户接收并执行安装任务、回填安装结果", "externalPortal", "30", gp()),
  ("经销商", "通过外部门户下单、查看进度、确认验收、查看应收对账与发起售后", "externalPortal", "30", gp()),
]

def main():
    ctx = load_ctx()
    rc = ctx.get("roleContext", [])
    have = {r["roleName"] for r in rc}
    for name, desc, scope, pscope, glob in ROLES:
        if name in have:
            print("skip", name); continue
        args = {"name": name, "description": desc, "roleScope": scope,
                "permissionScope": pscope, "globalPermissions": glob}
        res = call("create_role", args)
        data = res.get("data", res)
        rid = data.get("roleId") or data.get("id") if isinstance(data, dict) else None
        print(name, "->", rid or json.dumps(data, ensure_ascii=False)[:120])
        rc.append({"roleId": rid, "roleName": name})
        ctx["roleContext"] = rc; save_ctx(ctx)
    print("ROLES DONE:", len(rc))

if __name__ == "__main__":
    import json
    main()
