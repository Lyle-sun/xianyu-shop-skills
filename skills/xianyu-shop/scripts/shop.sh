#!/bin/zsh
# 闲鱼店铺总控脚本。所有命令先读 shop-config.env。
#   shop.sh doctor                         体检：配置、工具、登录
#   shop.sh task <模板名> <商品代号> [k=v...]  按模板生成任务单到 $SHOP_DIR/tasks/
#   shop.sh dispatch <角色> <任务单>         按配置派给该角色的 agent，后台跑，日志进 tasks/logs/
#   shop.sh pages <文件> <输出目录> [页码...]  Word/PDF 转页面图（无窗口）
#   shop.sh pack <成品目录> <价格>            把 listing.md / main.png / shots 整理成上架包
#   shop.sh publish <成品目录> [--dry-run]    易店上架 + 配自动发货
#   shop.sh price                            在配置区间里随机给一个价格
#   shop.sh stats                            拉一次易店在售数据
#   shop.sh workbench [端口]                 打开本机工作台网页（默认 8765）
#   shop.sh orders [天数]                    看最近几天订单（默认 2 天）
setopt NULL_GLOB
HERE="${0:A:h}"; SKILL="${HERE:h}"
CONF="${SHOP_CONFIG:-}"
if [ -z "$CONF" ]; then
  for c in "$PWD/shop-config.env" "$HOME/.config/xianyu-shop/shop-config.env"; do
    [ -f "$c" ] && { CONF="$c"; break; }
  done
fi
cmd=$1; shift
if [ -z "$CONF" ] || [ ! -f "$CONF" ]; then
  echo "还没有店铺配置。先按 references/onboarding.md 走一遍首次设置，生成 shop-config.env。"; exit 2
fi
source "$CONF"; export SHOP_DIR YIDIAN_NICK YIDIAN_ADDRESS
QUARK="node $HOME/.agents/skills/quarkclouddrive/scripts/quark-drive.cjs"

ok(){ echo "✓ $1"; }; bad(){ echo "✗ $1"; FAIL=1; }

case $cmd in
doctor)
  FAIL=0
  echo "配置：$CONF"
  [ -d "$SHOP_DIR" ] && ok "店铺目录 $SHOP_DIR" || bad "店铺目录不存在：$SHOP_DIR"
  [ "$YIDIAN_NICK" != "你的闲鱼店铺昵称" ] && [ -n "$YIDIAN_NICK" ] && ok "店铺昵称 $YIDIAN_NICK" || bad "店铺昵称没填"
  for t in python3 node swift; do command -v $t >/dev/null && ok "$t" || bad "缺 $t"; done
  [ -x /Applications/LibreOffice.app/Contents/MacOS/soffice ] && ok "LibreOffice" || bad "缺 LibreOffice（Word 转页面图用，brew install --cask libreoffice）"
  [ -d "$LO_PROFILE/user/fonts" ] && ok "LibreOffice 中文字体" || bad "LibreOffice 配置里没有中文字体：$LO_PROFILE/user/fonts"
  [ -d "/Applications/Google Chrome.app" ] && ok "Chrome（出图渲染用）" || bad "缺 Google Chrome"
  for s in listing-copy-mimic xianyu-main-image; do
    [ -f "$HOME/.claude/skills/$s/SKILL.md" ] || [ -f "$HOME/.agents/skills/$s/SKILL.md" ] && ok "skill $s" || bad "缺 skill $s"
  done
  [ -f "$HOME/.agents/skills/quarkclouddrive/scripts/quark-drive.cjs" ] && ok "skill quarkclouddrive" || bad "缺夸克官方 skill quarkclouddrive"
  for r in SOURCER WRITER DESIGNER PUBLISHER; do
    a=${(P)${:-ROLE_$r}}; v=${(P)${:-AGENT_$a}}
    [ -n "$v" ] || { bad "角色 $r=$a 没有启动命令 AGENT_$a"; continue; }
    [ "$v" = self ] && { ok "角色 $r → $a（当前对话自己做）"; continue; }
    bin=${${(z)v}[1]}; [ "$bin" = zsh ] && bin=$a
    zsh -ic "command -v $bin" >/dev/null 2>&1 && ok "角色 $r → $a" || bad "角色 $r → $a，但找不到命令 $bin"
  done
  [ -f "$HOME/.config/yidian/token" ] || [ -n "$YIDIAN_TOKEN" ] || bad "易店 token 没放（店主本人放到 ~/.config/yidian/token）"
  python3 "$HERE/yidian_api.py" list >/dev/null 2>&1 && ok "易店登录" || bad "易店连不上：token 过期或没放，店主本人重新放一次"
  # 夸克授权按 agent 渠道分开，只能由各 agent 自己查自己的；不借用别的 agent 的授权。
  me=$(cd "$SHOP_DIR" && ${=QUARK} resolve-agent 2>&1 | grep -o 'QK_AGENT_ID=.*' | cut -d= -f2)
  out=$(cd "$SHOP_DIR" && ${=QUARK} get-user-info --stdout-only 2>/dev/null | grep -v compdef)
  if echo "$out" | grep -q '"code":0'; then ok "夸克登录（本渠道 $me）"
  elif [ "$me" = "${(L)ROLE_SOURCER}" ] || [ "$me" = deepseek -a "$ROLE_SOURCER" = dsh ]; then bad "夸克未授权（本渠道 $me，货源角色要用）：店主本人重新授权"
  else echo "- 夸克本渠道（$me）未授权，本角色用不到；货源角色（$ROLE_SOURCER）的任务单开头会自查"; fi
  if [ -n "$FEISHU_BASE" ]; then
    lark-cli base +table-list --base-token "$FEISHU_BASE" --as user >/dev/null 2>&1 && ok "飞书" || bad "飞书读不了（lark-cli 没登录？）"
  else echo "- 飞书没配置，跳过"; fi
  echo; [ $FAIL = 0 ] && echo "体检通过，可以开工。" || echo "有 ✗ 项，先处理再开工。登录类问题由店主本人处理，agent 不要绕。"
  exit $FAIL;;
task)
  tpl=$1; code=$2; shift 2
  src="$SKILL/templates/$tpl.md"; [ -f "$src" ] || { echo "没有模板 $tpl，可选：$(ls $SKILL/templates | grep -v "^_" | sed "s/\.md//" | tr "\n" " ")"; exit 1; }
  D=$(date +%m%d); out="$SHOP_DIR/tasks/$tpl-$code-$D.md"; mkdir -p "$SHOP_DIR/tasks/logs"
  args=(-e "s#{{SHOP_DIR}}#$SHOP_DIR#g" -e "s#{{CODE}}#$code#g" -e "s#{{DATE}}#$D#g" -e "s#{{SKILL}}#$SKILL#g" -e "s#{{QUARK}}#$QUARK#g")
  for kv in "$@"; do k=${kv%%=*}; v=${kv#*=}; args+=(-e "s#{{$k}}#$v#g"); done
  sed -e "/{{RULES}}/r $SKILL/templates/_rules.md" -e "/{{RULES}}/d" "$src" | sed "${args[@]}" > "$out"
  left=$(grep -o '{{[A-Z_]*}}' "$out" | sort -u | tr '\n' ' ')
  [ -n "$left" ] && echo "注意：还有没填的占位符 $left（直接编辑任务单补上）"
  echo "$out";;
dispatch)
  role=$1; t=$2; [ -f "$t" ] || { echo "任务单不存在：$t"; exit 1; }
  a=${(P)${:-ROLE_${(U)role}}}; [ -n "$a" ] || { echo "配置里没有角色 ROLE_${(U)role}"; exit 1; }
  v=${(P)${:-AGENT_$a}}
  [ "$v" = self ] && { echo "角色 $role 由当前对话的 agent 自己做：读 $t 照做。"; exit 0; }
  c=${v//\{TASK\}/$t}; log="$SHOP_DIR/tasks/logs/${${t:t}:r}.log"
  ( cd "$SHOP_DIR" && eval "$c" < /dev/null > "$log" 2>&1 & )
  echo "已派给 $a（$role），日志 $log";;
pages)
  IN=$1; OUT=$2; shift 2; mkdir -p "$OUT"
  case ${IN:e:l} in
    pdf) PDF="$IN";;
    *) /Applications/LibreOffice.app/Contents/MacOS/soffice -env:UserInstallation=file://$LO_PROFILE \
         --headless --norestore --convert-to pdf --outdir "$OUT" "$IN" >/dev/null 2>&1
       PDF="$OUT/${${IN:t}:r}.pdf"; [ -f "$PDF" ] || { echo "转换失败：$IN"; exit 1; };;
  esac
  swift "$HERE/pdf_pages.swift" "$PDF" "$OUT" "$@" 2>/dev/null | grep pages; echo "PDF: $PDF";;
pack)
  d=$1; price=$2; [ -f "$d/listing.md" ] && [ -f "$d/main.png" ] && [ -f "$d/delivery.md" ] || { echo "$d 里要有 listing.md、main.png、delivery.md"; exit 1; }
  sed -n '1s/^# //p' "$d/listing.md" > "$d/title.txt"
  awk '/^```text/{f=1;next}/^```/{f=0}f' "$d/listing.md" > "$d/body.txt"
  link=$(grep -o 'https://pan.quark.cn/s/[A-Za-z0-9]*' "$d/delivery.md" | head -1); [ -n "$link" ] || { echo "delivery.md 里没有夸克分享链接"; exit 1; }
  printf '亲，感谢下单，网盘自取👇\n\n链接：%s\n\n资料容易失效，请及时保存\n' "$link" > "$d/delivery.txt"
  printf '{"category":"电子资料","price":%s,"share_url":"%s"}\n' "$price" "$link" > "$d/manifest.json"
  sips -s format jpeg -s formatOptions 85 -Z 1000 "$d/main.png" --out "$d/main-upload.jpg" >/dev/null
  echo "标题：$(cat $d/title.txt)（$(python3 -c 'import sys;print(len(open(sys.argv[1],encoding="utf-8").read().strip()))' "$d/title.txt") 字）"; echo "价格：$price  发货：$link"; echo "配图：$(ls $d/shots/*.jpg 2>/dev/null | wc -l | tr -d ' ') 张";;
publish)
  d=$1; shift; python3 "$HERE/yidian_api.py" publish "$d" --skip-review "$@";;
price)
  python3 -c "import random;print(round(random.uniform($PRICE_MIN,$PRICE_MAX),2))";;
stats)  python3 "$HERE/daily_stats.py";;
workbench)
  W="${SKILL:A:h:h}/workbench/server.py"; [ -f "$W" ] || { echo "没找到工作台：$W（要从仓库安装 skill）"; exit 1; }
  SHOP_CONFIG="$CONF" exec python3 "$W" "${1:-8765}";;
orders) python3 "$HERE/yidian_api.py" orders ${1:-2};;
*) sed -n 2,13p "$0";;
esac
