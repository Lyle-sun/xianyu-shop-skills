# 任务（第二个店的主图变体）：{{CODE}} → 账号 {{ACCOUNT}}

工作目录 `{{SHOP_DIR}}`。同一件货要发到另一个闲鱼店（账号 `{{ACCOUNT}}`），主图要和主店明显不同。配图沿用主店的，不用重出。

## 输入
- 主店主图：`xianyu-assets/{{CODE}}/main.png`、`main.json`
- 变体文案：`xianyu-assets/{{CODE}}/acct-{{ACCOUNT}}/listing.md`（图上的字跟它走）
- 页面图：`xianyu-assets/{{CODE}}/pages/`

## 要做的
1. 读 `xianyu-main-image` skill 的 SKILL.md 照着做。
2. 和主店主图拉开：**换打底页**（不和主店主图、也不和 `shots/` 第一张同一页）、**换配色**、主标题用变体文案的说法；版式可以换成 skill 里另一种适合资料的。
3. 用 skill 自带的 `scripts/render.py` 渲染，自己看大图和缩略图，再和主店主图并排看一眼，确认一眼能分出是两张图。

## 交付
`xianyu-assets/{{CODE}}/acct-{{ACCOUNT}}/main.json`、`main.png`、`image-notes.md`（用了哪页、和主店哪里不同）。

{{RULES}}
