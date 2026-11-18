# xianyu-shop-skills

一套让多个 AI agent 分工合作，把**闲鱼虚拟资料店**从「选品」做到「上架并自动发货」的 skill。

- **xianyu-shop**：总控。负责首次设置、开工体检、按角色派活、验收、上架、看订单、复盘。
- **listing-copy-mimic**：写闲鱼标题和正文，照爆款的结构写。
- **xianyu-main-image**：出主图和配图（3:4 竖图，真实内页打底再压字）。

skill 是通用格式：一个文件夹，放一份 `SKILL.md` 和几个脚本。Claude Code、Codex 等支持 skill 的 agent 都能读。流程里只写「角色」，不写死用哪个 agent；哪个 agent 当哪个角色，在配置文件里改。

> 只适合卖**你有权分发**的资料：没有作者的整理稿、开源项目、自己有书面授权的东西。影视、付费课、出版物、别人在卖的付费产品一律不碰，skill 里写了红线，agent 会停下来。

---

## 1. 它怎么干活

一件货走 8 步，每一步都要交出文件才能进下一步：

| 步 | 默认谁做 | 做什么 | 交出 |
|---|---|---|---|
| 1 选品 | 你 + 总调度 | 从对标店找卖得好的品 | 线索 |
| 2 查货源 | 货源（DSH） | 逐个文件查品牌、水印、出处、教材版本 | `check.md` |
| 3 下载转页 | 货源（DSH） | 下载，把 Word/PDF 转成页面图，不弹窗口 | `pages/` |
| 4 写文案 | 写手（DSH） | 写标题和正文 | `listing.md` |
| 5 出图 | 设计（Codex） | 出主图 + 6–8 张真实内页配图 | `main.png`、`shots/` |
| 6 发货链接 | 货源（DSH） | 夸克建干净文件夹，生成永久分享链接 | `delivery.md` |
| 7 上架 | 发布（Claude） | 易店上架，配好自动发货 | `published.json` |
| 8 复盘 | 发布（Claude） | 看订单和数据，记下哪里要改 | 改进记录 |

第 3、4 步可以同时跑，第 5、6 步也可以。

**角色**：总调度（派活、验收）、货源（管网盘）、写手、设计、发布，外加店主（你）：拍板、定价、登录授权、有订单后去拿货。

---

## 2. 准备

| 需要 | 用来干什么 | 怎么装 |
|---|---|---|
| macOS | 转页脚本用到了 macOS 自带的 PDFKit 和 `sips` | —— |
| Python 3、Node | 跑脚本 | `brew install python node` |
| Google Chrome | 出图时无头渲染 | 官网下载 |
| LibreOffice | Word 转 PDF，不弹窗口 | `brew install --cask libreoffice` |
| 至少一个能跑 skill 的 agent | 干活 | 比如 Claude Code、Codex CLI、DeepSeek Harness（`dsh`） |
| 夸克网盘 + 官方 skill `quarkclouddrive` | 转存、下载、做分享链接 | 按夸克官方说明安装，放到 `~/.agents/skills/quarkclouddrive` |
| 易店（鱼店助手）账号 | 上架和自动发货 | 在易店绑定你的闲鱼店 |
| 飞书 + `lark-cli`（可选） | 选品台账 | 不用也能跑 |

---

## 3. 安装

```bash
git clone https://github.com/Lyle-sun/xianyu-shop-skills.git
cd xianyu-shop-skills
./install.sh                    # 把 3 个 skill 链接到 ~/.agents/skills 和 ~/.claude/skills
./setup/setup-libreoffice.sh    # 给 LibreOffice 准备中文字体（无窗口模式看不到系统字体）
```

## 4. 首次设置

对你的 agent 说：

> 按 xianyu-shop 走首次设置

它会一组一组地问你：店铺目录、易店里的店铺名、对标店、谁当哪个角色、定价区间、每天上限，然后生成 `~/.config/xianyu-shop/shop-config.env`。模板见 [`skills/xianyu-shop/shop-config.example.env`](skills/xianyu-shop/shop-config.example.env)。

有两件事必须你本人做，agent 只给你说明：

1. **易店 token**：Chrome 登录易店 → F12 → Application → Cookies → 复制 `token`：
   ```bash
   mkdir -p ~/.config/yidian && pbpaste > ~/.config/yidian/token && chmod 600 ~/.config/yidian/token
   ```
   大约 30 天过期，过期了重放一次。
2. **夸克授权**：每个 agent 要单独授权一次。让这个 agent 跑 `quark-drive.cjs login`，它会给你一个授权链接，你自己点开确认。

最后体检：

```bash
~/.agents/skills/xianyu-shop/scripts/shop.sh doctor
```

全部 ✓ 就能开工。

## 5. 做第一件货

最简单的方式，直接对总调度 agent 说：

> 用 xianyu-shop 上架一件：对标商品 https://www.goofish.com/item?id=…，货源在夸克「来自：分享」里的 XXX.pdf

它会按 8 步生成任务单、派给各角色、验收，到上架前停下来问你定价。

也可以自己一条条跑：

```bash
S=~/.agents/skills/xianyu-shop/scripts/shop.sh
t=$($S task sourcing-check my-item "BENCHMARK_URL=https://www.goofish.com/item?id=…" "SOURCE=夸克里的 XXX.pdf")
$S dispatch sourcer "$t"                  # 后台跑，日志在 <店铺目录>/tasks/logs/
# … 依次 fetch-pages / copy / images / delivery-link
$S pack <店铺目录>/xianyu-assets/my-item "$($S price)"
$S publish <店铺目录>/xianyu-assets/my-item --dry-run
$S publish <店铺目录>/xianyu-assets/my-item
$S orders 2                               # 最近 2 天订单（不显示买家信息）
```

`shop.sh` 的全部命令见 [`references/tools.md`](skills/xianyu-shop/references/tools.md)。

## 6. 换成别的 agent

改 `shop-config.env` 里两处就行：

```bash
ROLE_WRITER="kimi"                                    # 写手换成 kimi
AGENT_kimi='kimi run "请完整读取并严格执行 {TASK}。"'  # 告诉脚本怎么启动它，{TASK} 会换成任务单路径
```

`AGENT_xxx='self'` 表示这个角色由当前对话里的 agent 自己做，不另起进程。

## 7. 持续优化

每做完一件，总调度在 `<店铺目录>/workflow/improvements.md` 记一笔：卡在哪、你改了什么、该改哪条规则、上架后的数据。**你明确不满意的当场改 skill，其他问题同一类出现两次再改**，写进 `SKILL.md` 末尾的变更记录。欢迎提 issue 和 PR。

## 8. 红线（节选，全文见 [`references/redlines.md`](skills/xianyu-shop/references/redlines.md)）

- 不碰影视、动画、付费课、出版物、名师/机构资料、别人在卖的付费产品、账号会员、破解。
- 带别人水印、店铺名、联系方式的文件剔掉或换货，不靠去水印。
- 不抄同行的图和字，只学结构。
- 碰到登录、授权问题就停，等店主处理；token 不进聊天、不进配置。
- 网盘只移动不删除；只发自己网盘的永久链接。
- 不写假的「最新」「2026 版」；配好自动发货才写「秒发」。

## 9. 常见问题

| 现象 | 原因和办法 |
|---|---|
| Codex 出图时 Chrome 崩溃（SIGABRT） | 沙箱模式里 Chrome 起不来，要用 `-s danger-full-access` 跑（配置里默认就是） |
| Word 转出来没有中文 | 没跑 `setup/setup-libreoffice.sh`，或者 `LO_PROFILE` 指错了目录 |
| 夸克报「未登录」，可另一个 agent 能用 | 夸克授权按 agent 分开，每个 agent 都要单独授权，不能借用 |
| 易店连不上 | token 过期了，重放一次 |
| 上架脚本报「已提交但没找到」 | **不要重跑**，去易店后台看一眼，避免重复上架 |

## 10. 目录

```
skills/
  xianyu-shop/            总控：SKILL.md、references/、templates/（5 个派活模板）、scripts/shop.sh
  listing-copy-mimic/     文案（爆款样例要你自己收集，见 references/README.md）
  xianyu-main-image/      主图（render.py + templates/main.html + examples/）
setup/setup-libreoffice.sh
install.sh
```

## 许可

MIT。
