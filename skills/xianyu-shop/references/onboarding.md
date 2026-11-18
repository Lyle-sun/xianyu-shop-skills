# 首次设置（引导）

装好 skill 后先走这一遍，生成 `~/.config/xianyu-shop/shop-config.env`。以后每次开工前只跑体检 `shop.sh doctor`。
换电脑、换 agent、换人用，都重新走一遍。

## 一、问店主（一次问一组，给默认值让店主点头）

| 问什么 | 写进配置 | 默认 |
|---|---|---|
| 店铺目录放哪 | `SHOP_DIR` | `~/xianyu-shop` |
| 易店里绑定的店铺名 | `YIDIAN_NICK` | —— |
| 对标店（第一个是主对标） | `BENCHMARK_SHOPS` | —— |
| 谁查货源/管网盘、谁写文案、谁出图、谁上架 | `ROLE_*` | dsh / dsh / codex / claude |
| 新品定价区间 | `PRICE_MIN` / `PRICE_MAX` | 0.1 / 1.9 |
| 每天最多上几个 | `DAILY_LIMIT` | 10 |
| 飞书台账（可选） | `FEISHU_*` | 留空 |

然后把 `references/redlines.md` 给店主看一遍，店主点头才算设置完。

## 二、写配置

```bash
mkdir -p ~/.config/xianyu-shop && cp <skill>/shop-config.example.env ~/.config/xianyu-shop/shop-config.env
```
按上面的答案改。**配置里不写任何 token、密码、API Key。**

## 三、需要店主本人做的（agent 只给链接和说明，不代办）

1. **易店 token**：Chrome 登录易店 → F12 → Application → Cookies → 复制 `token`，然后
   `pbpaste > ~/.config/yidian/token && chmod 600 ~/.config/yidian/token`
2. **夸克授权**：每个 agent 渠道单独授权。让该 agent 在店铺目录跑 `quark-drive.cjs login`，把返回的授权链接给店主，店主自己点开确认。
3. **飞书**（可选）：`lark-cli` 登录。

## 四、环境（体检会查，缺什么装什么）

- Python3、Node、Swift（macOS 自带）
- Google Chrome（出图渲染）
- LibreOffice：`brew install --cask libreoffice`。无窗口模式看不到系统字体，要把中文字体放进 `$LO_PROFILE/user/fonts/`（如 Arial Unicode.ttf、STHeiti），并在 `registrymodifications.xcu` 里把宋体/黑体/微软雅黑替换到这些字体。
- skill：`listing-copy-mimic`、`xianyu-main-image`、夸克官方 `quarkclouddrive`
- 各角色的 agent 命令能跑（如 `dsh`、`codex`）。Codex 出图要完全权限（`-s danger-full-access`），沙箱里 Chrome 会崩。

## 五、体检

```bash
<skill>/scripts/shop.sh doctor
```
全部 ✓ 才算完成。登录类 ✗ 交给店主本人。
