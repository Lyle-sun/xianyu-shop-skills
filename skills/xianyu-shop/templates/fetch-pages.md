# 任务（下载 + 转页面图）：{{CODE}}

工作目录 `{{SHOP_DIR}}`。先读 `xianyu-assets/{{CODE}}/check.md`，只处理结论是「干净可用」「改名可用」的文件。

1. 用 `{{QUARK}} download` 下载这些文件到 `.tmp/{{CODE}}/src/`（已经下过的跳过）。
2. 转页面图：`{{SKILL}}/scripts/shop.sh pages <文件> xianyu-assets/{{CODE}}/pages/<文件序号> [页码...]`。
   - Word 和 PDF 都用这条命令，不弹窗口，9MB 的 Word 约 2 分钟。
   - 先不带页码跑一次拿到总页数，再挑 8–12 页出图：目录页、信息密的干货页、带图或公式的页，每个文件至少一页。
3. 自己看每张图：字清楚、公式和图没丢；有水印、网址、人名的页不要。
4. 写 `xianyu-assets/{{CODE}}/pages/index.md`：每张图对应哪个文件第几页、内容是什么、为什么选。

{{RULES}}
