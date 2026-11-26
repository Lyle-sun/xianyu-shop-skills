# 任务（DSH 上架）：{{CODE}}

工作目录 `{{SHOP_DIR}}`，商品目录 `xianyu-assets/{{CODE}}/`。店主已经审过品，**不要再审内容、查版权或判断能不能卖**，只按下面上架。

- 售价：{{PRICE}} 元
- 发货：{{DELIVERY}}（「自动」= 拍下自动发网盘链接；「人工」= 无货源，不配自动发货）
- 发货链接：{{LINK}}（人工发货写「无」）

1. 确认目录里有 `listing.md`（第一行 `# 标题`，正文在 ```text 块里）和 `main.png`；配图放 `shots/*.jpg`（可没有）。缺哪样就停，写出来。
2. 自动发货：`delivery.md` 里没有链接就新建一个，只写一行 `链接：{{LINK}}`；然后跑
   `zsh {{SKILL}}/scripts/shop.sh pack xianyu-assets/{{CODE}} {{PRICE}}`。
   人工发货：自己生成 `title.txt`（标题一行）、`body.txt`（```text 块里的正文）、`main-upload.jpg`（`sips -s format jpeg -s formatOptions 88 -Z 1000 main.png --out main-upload.jpg`）和 `manifest.json`：`{"category":"电子资料","price":{{PRICE}},"manual":true}`。人工发货的标题正文不能出现「秒发」「自动发货」，有就改掉。
3. 先预演：`YIDIAN_ACCOUNT=main python3 {{SKILL}}/scripts/yidian_api.py publish xianyu-assets/{{CODE}} --skip-review --dry-run`，再去掉 `--dry-run` 正式发。报违禁词就改掉那个词再发，最多改两次。
4. 发完核对：`published.json` 里有 goods_id；`yidian_api.py list` 能看到这个标题和价格。
5. 在 `{{SHOP_DIR}}/shop-log.md` 表格末尾加一行：`| {{DATE}} | 标题 | — | 开头句 | 清单格式 | 结尾说法 | 在售 <goods_id>（{{PRICE}} 元，<自动/人工>发货） |`。
6. 写 `xianyu-assets/{{CODE}}/publish-report.md`：goods_id、标题、价格、发货方式、有没有改过词。

- 接口报 500/超时：隔 1 分钟重试，最多 3 次；还不行就停，写报错原文。**脚本说「已提交但没找到」时不要重发**，写进报告等人工确认。
- 不改别的商品，不下架、不删除任何商品。

{{RULES}}
