# 任务（夸克授权自查）：{{CODE}}

工作目录 `{{SHOP_DIR}}`。夸克用 `{{QUARK}} <命令>`。只查**你自己这个 agent 渠道**的授权，不借用别的渠道。

1. 跑 `{{QUARK}} resolve-agent`，记下渠道标识（`QK_AGENT_ID=` 后面那段）。
2. 跑 `{{QUARK}} get-user-info`。
3. 写 `{{SHOP_DIR}}/data/auth/quark-{{CODE}}.json`（目录没有就建），只写下面这些字段，**不写 token、cookie、昵称以外的账号信息**：
   ```json
   {"agent": "{{CODE}}", "channel": "<渠道标识>", "ok": true, "checked_at": "<YYYY-MM-DD HH:MM>", "message": "<一句话结果>", "login_url": ""}
   ```
   - 返回 `"code":0` → `ok: true`，message 写「已授权」。
   - 未登录 / 未授权 / 过期 → `ok: false`，message 写报错原文（一行）；再跑 `{{QUARK}} login`，把它给出的授权链接原样写进 `login_url`，然后停，等店主自己点开授权。不要替店主点，不要换路子绕。
4. 不做别的事，不动网盘里的文件。

{{RULES}}
