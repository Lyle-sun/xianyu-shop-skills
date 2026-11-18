---
name: xianyu-shop
description: 闲鱼虚拟资料店的总控流程：首次设置引导、开工体检、按角色派活（查货源、下载转页、写文案、出图、做发货链接）、验收、易店上架配自动发货、看订单数据、复盘优化。用户说"上架一个 XX""这个能不能做""帮我搞二年级语文""看看这两天成交""店铺流程/workflow"，或要把一件资料从选品做到上架时使用。只写文案用 listing-copy-mimic，只出图用 xianyu-main-image。
---

# 闲鱼店铺总控

一件货从选品到成交走 8 步。本 skill 管「谁做、按什么顺序、做完交什么、怎么验收」，具体手艺交给下面的专门 skill 和脚本。

所有命令走 `scripts/shop.sh`（下文简写 `shop.sh`），它自动读店铺配置 `shop-config.env`。

## 0. 先确认能开工

1. **没有配置**（`shop.sh` 提示找不到 `shop-config.env`）：按 [references/onboarding.md](references/onboarding.md) 走首次设置，问清店主后再继续。
2. **有配置**：跑 `shop.sh doctor`。有 ✗ 先处理；登录类的 ✗ 交给店主本人，不绕。
3. 看配置里的 `ROLE_*`，弄清自己是哪个角色。**只做自己角色的活**；别的角色的活用 `shop.sh dispatch` 派出去，或者交回给总调度。
4. 红线见 [references/redlines.md](references/redlines.md)，每一步都适用。

## 角色

| 角色 | 配置项 | 干什么 |
|---|---|---|
| 总调度 | `ROLE_COORDINATOR` | 定流程、生成任务单、派活、验收、改 skill |
| 货源 | `ROLE_SOURCER` | 查货源、下载、转页面图、做发货链接（管网盘） |
| 写手 | `ROLE_WRITER` | 写标题和正文 |
| 设计 | `ROLE_DESIGNER` | 出主图和配图 |
| 发布 | `ROLE_PUBLISHER` | 打包、上架、配自动发货、看订单数据 |
| 店主 | —— | 拍板做不做、定价、登录授权、有订单后去同行处拿货 |

## 8 步流程

每步做完要有交付文件；**没有交付文件就不进下一步**。商品代号用英文短名，成品都在 `$SHOP_DIR/xianyu-assets/<代号>/`。

| 步 | 谁 | 怎么做 | 交付 | 验收要点 |
|---|---|---|---|---|
| 1 选品 | 店主 + 总调度 | 对标店找卖得好的品，记进线索库；只搜店主给的词 | 线索库一行：对标链接、货源、状态 | 不在红线品类里 |
| 2 查货源 | 货源 | `shop.sh task sourcing-check <代号> BENCHMARK_URL=… SOURCE=…`（SOURCE 写网盘里的文件/文件夹名，或夸克分享链接） → `dispatch sourcer` | `check.md` | 每个文件都有结论；有别人出处的剔掉。**整件不能做就停在这里，告诉店主为什么** |
| 3 下载转页 | 货源 | `task fetch-pages <代号>` → `dispatch sourcer` | `pages/` + `pages/index.md` | 图清楚、无水印；每个文件至少一页 |
| 4 写文案 | 写手 | `task copy <代号> BENCHMARK_URL=…` → `dispatch writer` | `listing.md` | 标题 25–30 字；份数页数和 check.md 一致；无假年份；老教材写清 |
| 5 出图 | 设计 | `task images <代号>` → `dispatch designer` | `main.png`、`shots/`、`image-notes.md` | 3:4 主图两条字带；主图页不和第一张配图重复；配图全是真实页面；最后一张是交付卡 |
| 6 发货链接 | 货源 | `task delivery-link <代号> FOLDER=…` → `dispatch sourcer` | `delivery.md` | 永久、无提取码；文件名干净；买家视角能打开 |
| 7 上架 | 发布 | 店主定价（或 `shop.sh price`）→ `shop.sh pack <目录> <价格>` → `publish <目录> --dry-run` → 店主点头 → `publish <目录>` | `published.json` | 自己先看一遍主图、标题、正文；回读商品 ID |
| 8 成交复盘 | 发布 | `shop.sh orders`、`shop.sh stats`；新品跑 1–2 周和老品比浏览、想要、成交 | 复盘记录 | 只看数据说话 |

第 3、4 步互不依赖（写手可以先用 check.md 写），第 5、6 步也可以同时跑。

### 派活

```bash
t=$(shop.sh task copy grade2-math BENCHMARK_URL=https://www.goofish.com/item?id=…)
shop.sh dispatch writer "$t"
```
任务单里没填的 `{{占位符}}` 会提示，直接编辑任务单补上。派出去的活跑完后看日志 `tasks/logs/` 和交付文件，按上表验收；不合格就写清哪里不对，重新派，不要自己替别的角色干。

### 店主改主意时

店主说「换一张主图」「标题加秒发」这类小改动：生成一张只写这一处改动的小任务单，派给对应角色。改完回到验收。

## 复盘和持续优化

这套流程靠反复改进变好。每做完一件货（或一批），总调度在 `$SHOP_DIR/workflow/improvements.md` 追加：

```
## 2026-11-18 grade2-math
- 卡住的地方：…（哪一步、原因）
- 店主改了什么：…（说明 skill 哪条没写到）
- 要改的规则：…（改哪个 skill / 模板 / 脚本的哪一条）
- 数据：上架 N 天，浏览/想要/成交 …
```

店主明确不满意的（比如「这张图好丑」），当场改对应的 skill、模板或脚本；其他问题同一类出现两次再改，并在本 skill 末尾的「变更记录」写一行。改之前先备份。

改完同步给人看的版本（配置里填了才做）：本地 `$SHOP_DIR/workflow/xianyu-shop-manual.md`；飞书文档 `FEISHU_MANUAL_DOC`（用 `lark-cli docs +update --command overwrite --doc-format markdown` 覆盖，正文不带一级标题），并重打 skill 压缩包附在文档末尾；附录页 `FEISHU_APPENDIX_DOC` 重建 skill 全文。

## 参考

- [references/onboarding.md](references/onboarding.md)：首次设置
- [references/redlines.md](references/redlines.md)：红线
- [references/tools.md](references/tools.md)：工具说明（大白话 + 命令）
- `templates/`：派活模板；`_rules.md` 会自动拼进每张任务单

## 变更记录

- 2026-11-18 v1：从 11-15 批量工具包升级。加入首次设置和体检、角色配置、单品 8 步流程、5 个派活模板、订单查询、复盘机制。
- 2026-11-18 v1.1：交付说明卡规则重写（同主图配色、摆货、三步流程、提醒放底部）；店主不满意的当场改 skill；pack 标题按字符计数。
- 2026-11-18 v1.2：shop-log 挪到店铺目录（沙箱里的写手也能写）；查货源模板去掉会被带进任务单的提示语。
