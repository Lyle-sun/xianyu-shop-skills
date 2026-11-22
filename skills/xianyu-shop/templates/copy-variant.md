# 任务（第二个店的文案变体）：{{CODE}} → 账号 {{ACCOUNT}}

工作目录 `{{SHOP_DIR}}`。同一件货要发到另一个闲鱼店（账号 `{{ACCOUNT}}`），两个店的商品不能一模一样，不然闲鱼可能判成重复铺货。只写字，不出图。

## 输入
- 主店文案：`xianyu-assets/{{CODE}}/listing.md`
- `xianyu-assets/{{CODE}}/check.md`、`pages/index.md`

## 要做的
1. 读 `listing-copy-mimic` skill 的 SKILL.md 照着做。
2. **标题**：换一个切入点重写，不是换几个字。比如主店从「年级+科目」切入，这里就从「用途/痛点/份数」切入；和主店标题相同的连续字不超过 6 个。不能用主店 listing.md 里的备选标题原样照搬。
3. **正文**：开头一段换说法，清单换个分组或顺序；**事实不变**：份数、页数、版本、年份和 check.md 一致，不加没有的东西。
4. 违禁词照样过 `{{SKILL}}/scripts/banned-words.txt`。

## 交付
`xianyu-assets/{{CODE}}/acct-{{ACCOUNT}}/listing.md`（目录没有就建），格式和主店 listing.md 一样：第一行 `# 标题`，正文放在 ```text 代码块里；末尾写一句「和主店的区别：…」。

{{RULES}}
