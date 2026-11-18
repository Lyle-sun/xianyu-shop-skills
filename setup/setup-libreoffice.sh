#!/bin/zsh
# 给 LibreOffice 无窗口模式准备中文字体（Word 转页面图用）。只需跑一次。
# 无窗口模式看不到系统字体，所以把 macOS 自带的中文字体复制进专用配置目录，并把宋体/黑体/微软雅黑等替换过去。
set -e
P="${1:-$HOME/.config/xianyu-shop/lo-profile}"
HERE="${0:A:h}"
[ -x /Applications/LibreOffice.app/Contents/MacOS/soffice ] || { echo "先装 LibreOffice：brew install --cask libreoffice"; exit 1; }
mkdir -p "$P/user/fonts"
for f in "/Library/Fonts/Arial Unicode.ttf" "/System/Library/Fonts/STHeiti Light.ttc" "/System/Library/Fonts/STHeiti Medium.ttc"; do
  [ -f "$f" ] && cp -n "$f" "$P/user/fonts/" && echo "已放字体：${f:t}" || echo "没找到 $f（跳过）"
done
[ -f "$P/user/registrymodifications.xcu" ] || cp "$HERE/font-substitution.xcu" "$P/user/registrymodifications.xcu"
echo "完成：$P"
echo "在 shop-config.env 里把 LO_PROFILE 设成这个目录（默认就是）。"
