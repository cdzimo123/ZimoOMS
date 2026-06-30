# ZimoOMS

This repo configures the Mingdao **HAP** integration (MCP server + the `hap-mcp-app-builder` skill) and contains the build artifacts/scripts for the **《经销订单全流程》** dealer-order app built into the HAP app **ZimoOMS**.

- MCP server config: `.cursor/mcp.json` (`hap-mcp-ZimoOMS`, remote URL with `HAP-Appkey`/`HAP-Sign`).
- Skill: `.cursor/skills/hap-mcp-app-builder/` (Plan → Build via MCP).
- App build: `apps/ZimoOMS/` — `overview.md` (plan), `hap-context.json` (all created object IDs), `worksheetContext.json` (field IDs/option keys), and `build*.py` scripts. `apps/ZimoOMS/buildlib.py` is the shared JSON-RPC MCP client.

## Cursor Cloud specific instructions

- No dependencies to install: build scripts use only the Python 3 standard library (`urllib`, `json`). There is no package manifest and nothing to `pip install`.
- The HAP app is hosted by Mingdao (remote SaaS), not in this repo. Building/inspecting it means calling the MCP tools; there is no local server to run.
- Driving the MCP from a cloud agent: call the streamable-HTTP JSON-RPC endpoint directly (see `apps/ZimoOMS/buildlib.py` / `/tmp/mcp.py`). The configured `.cursor/mcp.json` server is loaded by the Cursor client, not auto-exposed as agent tools here.
- Non-obvious MCP gotchas (cost real debugging time — keep them in mind):
  - The Appkey is bound to one app, so there is **no `create_app` tool**; you build into the existing ZimoOMS app and **must pass `appId` in every tool call** (`buildlib.call()` auto-injects it).
  - Tool responses are inconsistently wrapped: some are `data.{...}`, others double-wrapped `data.data.{...}` (e.g. `create_process`, `delete_process`). Use a deep-unwrap helper.
  - Record id field in `get_record_list` rows is **`rowId`** (capital I); `_id` is a different hex id. Relation values and `get_record_details`/`update_record` need the `rowId` UUID, not `_id`.
  - `get_record_list` returns **newest-first**; do not assume creation order when mapping positional IDs.
  - Workflow build needs real field **IDs** (never alias) and **option keys** for select values (both are in `worksheetContext.json`). Set `trigger.nodeAlias:"trigger"` for deterministic references.
  - Verify automation by reading data after `update_record` with `triggerWorkflow:true` (e.g. `apps/ZimoOMS/demo_workflow.py` shows measurement-done auto-advancing an order 待测量→待生产).
- HAP apps are multi-end (PC web + mobile App + H5/小程序入口); building the app covers all surfaces. A single record can be shared without login via `get_record_share_link` (handy for visual verification without a Mingdao account).
- The HAP UI itself requires a Mingdao account login (the Appkey does not grant UI access), so end-to-end UI walkthroughs may be blocked without credentials; prefer MCP data reads + public share links for verification.
