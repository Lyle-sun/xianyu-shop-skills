#!/bin/zsh
# 把仓库里的 3 个 skill 链接到 agent 能读到的位置。重复跑没关系。
set -e
R="${0:A:h}"
mkdir -p ~/.agents/skills ~/.claude/skills
for s in xianyu-shop listing-copy-mimic xianyu-main-image; do
  for d in ~/.agents/skills ~/.claude/skills; do
    if [ -e "$d/$s" ] && [ ! -L "$d/$s" ]; then echo "跳过 $d/$s（已有同名目录，先备份或删掉再装）"; continue; fi
    ln -sfn "$R/skills/$s" "$d/$s"; echo "已链接 $d/$s"
  done
done
chmod +x "$R/skills/xianyu-shop/scripts/shop.sh" "$R/setup/setup-libreoffice.sh"
cat <<'MSG'

下一步：
1. 装夸克官方 skill quarkclouddrive（按它自己的说明），放在 ~/.agents/skills/quarkclouddrive
2. ./setup/setup-libreoffice.sh        # 给 Word 转页面图准备中文字体
3. 对你的 agent 说：「按 xianyu-shop 走首次设置」
4. ~/.agents/skills/xianyu-shop/scripts/shop.sh doctor   # 全部 ✓ 就能开工
MSG
