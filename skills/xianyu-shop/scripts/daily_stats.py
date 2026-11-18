#!/usr/bin/env python3
"""每天拉一次易店在售数据，追加到 data/stats/daily.csv（只读，不改商品）。

用法：python3 tools/daily_stats.py
"""
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

import os
ROOT = Path(os.environ.get("SHOP_DIR") or sys.exit("缺 SHOP_DIR：先 source 店铺配置 shop-config.env"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from yidian_api import req  # noqa: E402

OUT = ROOT / "data" / "stats" / "daily.csv"
FIELDS = ["date", "goods_id", "title", "price", "exposureNum", "browseCount", "wantNum", "listed_at"]


def fetch_live():
    rows, page = [], 1
    while True:
        q = f"page={page}&limit=100&cate_id=&type=1&store_name=&name="
        data = req("GET", "/adminapi/product/product?" + q)["data"]
        batch = data.get("list") or []
        rows.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return rows


def num(v):
    try:
        return int(float(v or 0))
    except (TypeError, ValueError):
        return 0


def load_existing():
    if not OUT.exists():
        return []
    with OUT.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    raw = fetch_live()
    current = []
    for x in raw:
        current.append({
            "date": today,
            "goods_id": str(x.get("goods_id", "")),
            "title": x.get("store_name", ""),
            "price": x.get("price", ""),
            "exposureNum": num(x.get("exposureNum")),
            "browseCount": num(x.get("browseCount")),
            "wantNum": num(x.get("wantNum")),
            "listed_at": x.get("add_time", ""),
        })

    old = load_existing()
    old_today = [r for r in old if r.get("date") == today]
    kept = [r for r in old if r.get("date") != today]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(kept + current)

    print(f"日期 {today}｜在售 {len(current)} 个商品｜写入 {OUT.relative_to(ROOT)}")
    if old_today:
        print(f"同一天已有 {len(old_today)} 行，已覆盖")

    te = sum(r["exposureNum"] for r in current)
    tb = sum(r["browseCount"] for r in current)
    tw = sum(r["wantNum"] for r in current)
    print(f"今天合计：曝光 {te}｜浏览 {tb}｜想要 {tw}")

    ymap = {r["goods_id"]: r for r in old if r.get("date") == yesterday}
    if not ymap:
        print("较昨天：没有昨天的数据，无法对比（明天开始有）。")
        return

    changes = []
    for r in current:
        y = ymap.get(r["goods_id"])
        if not y:
            continue
        de = r["exposureNum"] - num(y.get("exposureNum"))
        db = r["browseCount"] - num(y.get("browseCount"))
        dw = r["wantNum"] - num(y.get("wantNum"))
        if de == 0 and db == 0 and dw == 0:
            continue
        changes.append((de, db, dw, r))
    changes.sort(key=lambda x: (-abs(x[0]), -abs(x[1]), -abs(x[2])))

    print(f"较昨天变化最大的前 {min(5, len(changes))} 个（按曝光变化）：")
    if not changes:
        print("  无变化")
    for de, db, dw, r in changes[:5]:
        print(f"  {r['title'][:24]}｜曝光 {de:+d}｜浏览 {db:+d}｜想要 {dw:+d}")


if __name__ == "__main__":
    main()
