# 工具说明（大白话 + 命令）

总控脚本 `scripts/shop.sh`，所有命令都先读店铺配置。

| 干什么 | 大白话 | 命令 |
|---|---|---|
| 体检 | 开工前查一遍：配置、软件、各个登录 | `shop.sh doctor` |
| 生成任务单 | 从模板生成一张派活单，填好商品代号和参数 | `shop.sh task <模板> <代号> KEY=值 …` |
| 派活 | 按配置把任务单交给对应角色的 agent，后台跑 | `shop.sh dispatch <角色> <任务单>` |
| Word/PDF 转页面图 | 不弹窗口，把文件变成一页页图片 | `shop.sh pages <文件> <输出目录> [页码…]` |
| 随机定价 | 在配置的区间里给个价 | `shop.sh price` |
| 打包 | 把文案、主图、配图、发货链接整理成上架包 | `shop.sh pack <成品目录> <价格>` |
| 上架 | 通过易店上架并配好自动发货，写 `published.json` | `shop.sh publish <成品目录> [--dry-run]` |
| 看订单 | 最近几天的成交，不含买家信息 | `shop.sh orders [天数]` |
| 拉数据 | 在售商品的曝光、浏览、想要，追加到 `data/stats/daily.csv` | `shop.sh stats` |

模板：`sourcing-check`（查货源）、`fetch-pages`（下载+转页）、`copy`（写文案）、`images`（出图）、`delivery-link`（做发货链接）。

## 背后用到的东西

| 东西 | 是什么 |
|---|---|
| 夸克官方 skill `quarkclouddrive` | 让 agent 能转存、翻目录、下载、改名、做分享链接 |
| `listing-copy-mimic` skill | 写标题和正文的说明书，照同行爆款结构 |
| `xianyu-main-image` skill | 出主图的说明书 + 模板（`render.py` + Chrome 渲染） |
| LibreOffice + `pdf_pages.swift` | Word 转 PDF、PDF 切页成图 |
| `yidian_api.py` | 连易店的小脚本：上架、改价、下架、看订单 |
| 飞书多维表格 | 选品表、线索库（`lark-cli` 读写） |

## 一次上很多个

同样按 8 步走，给每件货一个代号，第 2–6 步可以给多件货同时派活（同一角色可以开多个进程）。上架时每个品之间按配置 `GAP_SECONDS` 随机间隔，不超过 `DAILY_LIMIT`。
