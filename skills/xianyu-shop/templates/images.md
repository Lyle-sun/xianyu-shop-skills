# 任务（出图）：{{CODE}}

工作目录 `{{SHOP_DIR}}`。只出图，文案已经写好。

## 输入
- 页面图：`xianyu-assets/{{CODE}}/pages/`（看 `index.md`）
- 文案：`xianyu-assets/{{CODE}}/listing.md`。图上的字和数字必须和它一致。

## 要做的
1. 读 `xianyu-main-image` skill 的 SKILL.md，从头读到尾照着做。
2. 主图：资料类用「内页压字」版式 3:4；两条字带；打底页选信息最密的一页，不能和第一张配图重复；老教材这类提醒不上主图。
3. 配图：6–8 张，只用真实页面，不用 AI 生成；顺序：目录页 → 3–5 张代表内页 → 最后一张交付说明卡。宽 750 的 jpg。
4. 用 skill 自带的 `scripts/render.py` 渲染，自己看大图和缩略图：不压线、不糊、不溢出。

## 交付
`xianyu-assets/{{CODE}}/main.json`、`main.png`、`shots/01-*.jpg … NN-delivery.jpg`、`image-notes.md`（选了哪几页、为什么、哪里要店主确认）。

{{RULES}}
