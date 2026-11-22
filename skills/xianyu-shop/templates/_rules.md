## 通用规则（每张任务单都适用）

- 先读 `{{SHOP_DIR}}/shop-config.env` 和 `{{SKILL}}/references/redlines.md`。
- 只在本任务写明的目录里写文件。不改 skill、手册和别的商品的文件。
- 碰到未登录、未授权、过期、权限不足：立刻停，把报错原文写进交付文件，等店主处理。不翻别处的配置找 token，不拿 cookie 拼请求，不换路子绕。
- 不打开会弹窗口的软件（WPS、Word、Pages 等），不操作屏幕界面。
- 要用无头 Chrome 抓网页或渲染，启动参数必须带 `--use-mock-keychain --password-store=basic`，并用 `.tmp/` 下的独立 `--user-data-dir`；不然每次启动都会在店主屏幕上弹「Keychain Not Found」。能复用一个 Chrome 进程就别每页重开。
- 网盘只移动、不删除，不动本任务以外的文件。
- 不写「自己做内容」「自制」这类建议。
- 收尾删掉本任务自己在 `.tmp/` 下产生的中间文件，交付物和货源原件留着；在交付文件末尾写一句删了什么。
- 做完写一句「完成」。
- 要用夸克的任务，开头先跑一次 `{{QUARK}} get-user-info`；返回未登录/未授权就停，写明报错，并跑 `login` 把授权链接原样写进交付文件，等店主自己点开授权。查完把结果按 `{{SKILL}}/templates/quark-auth.md` 第 3 步的格式写进 `{{SHOP_DIR}}/data/auth/quark-<你的 agent 名>.json`，工作台靠它显示登录状态。
