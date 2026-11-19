#!/usr/bin/env python3
"""闲鱼店铺工作台：本机网页，把选品→上架的流水线、派活、订单、改进记录放到一个页面。

只监听 127.0.0.1。不读、不显示任何 token。所有动作都走 skills/xianyu-shop/scripts/shop.sh。
用法：shop.sh workbench   （或 python3 workbench/server.py [端口]）
"""
import json, os, re, subprocess, sys, time, glob, mimetypes, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(HERE)
SHOP_SH = os.path.join(REPO, "skills", "xianyu-shop", "scripts", "shop.sh")
YIDIAN = os.path.join(REPO, "skills", "xianyu-shop", "scripts", "yidian_api.py")


def find_config():
    for c in (os.environ.get("SHOP_CONFIG"), os.path.join(os.getcwd(), "shop-config.env"),
              os.path.expanduser("~/.config/xianyu-shop/shop-config.env")):
        if c and os.path.isfile(c):
            return c
    sys.exit("没有店铺配置：先按 xianyu-shop 走首次设置，生成 ~/.config/xianyu-shop/shop-config.env")


CONF = find_config()


def load_env():
    out = subprocess.run(["zsh", "-c", f'set -a; source "{CONF}"; set +a; env -0'], capture_output=True).stdout.decode()
    env = dict(x.split("=", 1) for x in out.split("\0") if "=" in x)
    return env


ENV = load_env()
SHOP = os.path.realpath(ENV["SHOP_DIR"])
ASSETS = os.path.join(SHOP, "xianyu-assets")
LOGS = os.path.join(SHOP, "tasks", "logs")

# 8 步里由工作台跟踪的 6 步：步骤名、模板、角色、判定「已完成」的文件
STEPS = [
    ("check", "查货源", "sourcing-check", "sourcer", lambda d: ex(d, "check.md") or ex(d, "review.txt")),
    ("pages", "转页面图", "fetch-pages", "sourcer", lambda d: nonempty(d, "pages") or bool(glob.glob(f"{d}/preview-*.jpg"))),
    ("copy", "写文案", "copy", "writer", lambda d: ex(d, "listing.md") or ex(d, "title.txt")),
    ("images", "出图", "images", "designer", lambda d: ex(d, "main.png") and (nonempty(d, "shots") or bool(glob.glob(f"{d}/preview-*.jpg")))),
    ("delivery", "发货链接", "delivery-link", "sourcer", lambda d: ex(d, "delivery.md") or ex(d, "delivery.txt")),
    ("publish", "上架", None, "publisher", lambda d: ex(d, "published.json")),
]


def ex(d, f):
    return os.path.exists(os.path.join(d, f))


def nonempty(d, sub):
    p = os.path.join(d, sub)
    return os.path.isdir(p) and any(os.scandir(p))


def item_dirs():
    out = []
    for p in sorted(glob.glob(f"{ASSETS}/*/")) + sorted(glob.glob(f"{ASSETS}/batch-*/*/")):
        p = p.rstrip("/")
        name = os.path.basename(p)
        if name.startswith("batch-") or not os.path.isdir(p):
            continue
        marks = ("check.md", "listing.md", "title.txt", "main.json", "published.json", "delivery.md", "manifest.json")
        if any(ex(p, m) for m in marks):
            out.append(p)
    return out


def read(p, n=None):
    try:
        s = open(p, encoding="utf-8").read()
        return s[:n] if n else s
    except Exception:
        return ""


def title_of(d):
    t = read(os.path.join(d, "title.txt")).strip().splitlines()
    if t:
        return t[0]
    t = read(os.path.join(d, "listing.md")).strip().splitlines()
    if t and t[0].startswith("# "):
        return t[0][2:].strip()
    return ""


def running():
    r = subprocess.run(["ps", "-axo", "pid=,etime=,command="], capture_output=True, text=True).stdout
    rows = []
    for line in r.splitlines():
        m = re.search(r"(/[^\s\"']*/tasks/([\w.-]+)\.md)", line)
        if m and ("dsh" in line or "codex" in line) and "grep" not in line:
            pid, et = line.split()[:2]
            rows.append({"pid": pid, "elapsed": et, "task": m.group(2)})
    seen, uniq = set(), []
    for x in rows:
        if x["task"] not in seen:
            seen.add(x["task"]); uniq.append(x)
    return uniq


def code_of(d):
    return os.path.relpath(d, ASSETS)


def items():
    run = running()
    res = []
    for d in item_dirs():
        code = code_of(d)
        base = os.path.basename(d)
        steps = {k: bool(fn(d)) for k, _, _, _, fn in STEPS}
        pub = {}
        if steps["publish"]:
            try: pub = json.load(open(os.path.join(d, "published.json")))
            except Exception: pass
        active = [r["task"] for r in run if f"-{base}-" in f"-{r['task']}-"]
        nxt = next((k for k, *_ in STEPS if not steps[k]), None)
        thumb = next((f for f in ("main.thumb.png", "main-upload.jpg", "main.png") if ex(d, f)), None)
        verdict = (read(os.path.join(d, "review.txt")).split() or [""])[0].upper()
        shelved = ex(d, ".archived") or (verdict == "DROP" and not steps["publish"])
        res.append({"code": code, "title": title_of(d), "steps": steps, "next": nxt, "running": active,
                    "shelved": shelved, "verdict": verdict,
                    "goods_id": pub.get("goods_id") or pub.get("timed_id"), "price": pub.get("price"),
                    "time": pub.get("time") or "", "thumb": f"{code}/{thumb}" if thumb else None,
                    "mtime": os.path.getmtime(d)})
    res.sort(key=lambda x: (x["steps"]["publish"], -x["mtime"]))
    return res


def item_detail(code):
    d = safe_asset(code)
    shots = sorted(glob.glob(f"{d}/shots/*.jpg")) + sorted(glob.glob(f"{d}/preview-*.jpg"))
    pages = sorted(glob.glob(f"{d}/pages/**/*.jpg", recursive=True))[:24]
    listing = read(os.path.join(d, "listing.md"))
    body = read(os.path.join(d, "body.txt"))
    if not body and "```text" in listing:
        body = listing.split("```text", 1)[1].split("```", 1)[0].strip()
    link = re.search(r"https://pan\.quark\.cn/s/\w+", read(os.path.join(d, "delivery.md")) + read(os.path.join(d, "delivery.txt")))
    base = os.path.basename(d)
    logs = sorted([os.path.basename(p) for p in glob.glob(f"{LOGS}/*{base}*.log")], key=lambda f: -os.path.getmtime(os.path.join(LOGS, f)))
    docs = {f: read(os.path.join(d, f), 6000) for f in ("check.md", "image-notes.md", "delivery.md", "review.txt", "notes.txt") if ex(d, f)}
    pub = read(os.path.join(d, "published.json"))
    rel = lambda p: os.path.relpath(p, ASSETS)
    return {"code": code, "title": title_of(d), "body": body, "listing": listing,
            "main": f"{code}/main.png" if ex(d, "main.png") else None,
            "shots": [rel(p) for p in shots], "pages": [rel(p) for p in pages],
            "delivery_link": link.group(0) if link else None, "docs": docs, "logs": logs,
            "published": json.loads(pub) if pub else None}


def safe_asset(code):
    d = os.path.realpath(os.path.join(ASSETS, code))
    if not d.startswith(ASSETS + os.sep) or not os.path.isdir(d):
        raise ValueError("商品不存在")
    return d


def sh(*args, timeout=300):
    r = subprocess.run(["zsh", SHOP_SH, *args], capture_output=True, text=True, cwd=SHOP, timeout=timeout,
                       env={**os.environ, "SHOP_CONFIG": CONF})
    return (r.stdout + r.stderr).replace("compdef:153: _comps: assignment to invalid subscript range\n", "").strip(), r.returncode


def dispatch(code, step, note, kv):
    d = safe_asset(code)
    st = next((s for s in STEPS if s[0] == step), None)
    if not st or not st[2]:
        raise ValueError("这一步不能派活")
    base = os.path.basename(d)
    args = ["task", st[2], base] + [f"{k}={v}" for k, v in kv.items() if v]
    out, rc = sh(*args)
    task = out.strip().splitlines()[-1] if out else ""
    if rc or not task.endswith(".md"):
        return {"ok": False, "out": out}
    if os.path.relpath(d, ASSETS) != base:  # 批量目录里的商品，路径要改过来
        s = read(task).replace(f"xianyu-assets/{base}/", f"xianyu-assets/{os.path.relpath(d, ASSETS)}/")
        open(task, "w", encoding="utf-8").write(s)
    if note.strip():
        with open(task, "a", encoding="utf-8") as f:
            f.write("\n## 店主补充\n\n" + note.strip() + "\n")
    out2, rc2 = sh("dispatch", st[3], task)
    return {"ok": rc2 == 0, "out": out + "\n" + out2, "task": os.path.basename(task)}


def new_item(code, bench, source, note):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", code):
        raise ValueError("代号用小写英文、数字和短横线，比如 hs-physics")
    d = os.path.join(ASSETS, code)
    if os.path.exists(d):
        raise ValueError("这个代号已经有了")
    os.makedirs(d)
    open(os.path.join(d, "manifest.json"), "w").write(json.dumps({"benchmark": bench, "source": source}, ensure_ascii=False))
    return dispatch(code, "check", note, {"BENCHMARK_URL": bench, "SOURCE": source})


def publish(code, price, dry):
    d = safe_asset(code)
    if ex(d, "published.json"):
        return {"ok": False, "out": "已经上架过了（有 published.json），不会重复上架。"}
    try:
        price = float(price)
    except Exception:
        return {"ok": False, "out": "价格不对"}
    out, rc = sh("pack", d, f"{price:.2f}")
    if rc:
        return {"ok": False, "out": out}
    out2, rc2 = sh("publish", d, *(["--dry-run"] if dry else []), timeout=600)
    return {"ok": rc2 == 0, "out": out + "\n\n" + out2}


_orders_cache = {"t": 0, "rows": []}


def all_orders():
    if time.time() - _orders_cache["t"] > 300:
        os.environ.update({k: v for k, v in ENV.items() if k.startswith("YIDIAN_")})
        sys.path.insert(0, os.path.dirname(YIDIAN))
        import yidian_api
        _orders_cache.update(t=time.time(), rows=yidian_api.list_orders(None, 500))
    return _orders_cache["rows"]


def categories():
    cat = {}
    try: cat = json.load(open(os.path.join(SHOP, "data", "catalog.json"), encoding="utf-8"))
    except Exception: pass
    stats, latest = {}, ""
    import csv
    try:
        for r in csv.DictReader(open(os.path.join(SHOP, "data", "stats", "daily.csv"), encoding="utf-8")):
            if r["date"] >= latest:
                if r["date"] > latest: latest, stats = r["date"], {}
                stats[r["goods_id"]] = r
    except Exception: pass
    od = {}
    try:
        for o in all_orders():
            if o["status"] in ("交易关闭", "退款中"): continue
            g = str(o["goods_id"]); x = od.setdefault(g, [0, 0.0]); x[0] += 1; x[1] += float(o["money"] or 0)
    except Exception as e:
        print("orders:", e)
    rows = []
    now = time.time()
    for gid, st in stats.items():
        t = cat.get(gid, {})
        try: days = max(1.0, (now - time.mktime(time.strptime(st["listed_at"], "%Y-%m-%d %H:%M:%S"))) / 86400)
        except Exception: days = 1.0
        n, money = od.get(gid, [0, 0.0])
        rows.append({"goods_id": gid, "title": st["title"], "price": st["price"], "listed_at": st["listed_at"], "days": round(days, 1),
                     "exposure": int(st["exposureNum"] or 0), "browse": int(st["browseCount"] or 0), "want": int(st["wantNum"] or 0),
                     "orders": n, "money": round(money, 2),
                     **{k: t.get(k) for k in ("category", "sub", "stage", "year", "edition", "format", "source_shop", "confidence", "basis")}})
    return {"date": latest, "tagged": sum(1 for r in rows if r["category"]), "rows": rows}


SETTINGS = os.path.join(SHOP, "data", "workbench-settings.json")


def settings(upd=None):
    st = {"auto_refresh_hours": 6, "last_refresh": None, "last_result": ""}
    try: st.update(json.load(open(SETTINGS, encoding="utf-8")))
    except Exception: pass
    if upd:
        st.update(upd); os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
        json.dump(st, open(SETTINGS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return st


def refresh_stats():
    out, rc = sh("stats", timeout=300)
    _orders_cache["t"] = 0
    settings({"last_refresh": time.strftime("%Y-%m-%d %H:%M"), "last_result": (out.splitlines() or [""])[0] if rc == 0 else "失败：" + (out.strip().splitlines() or [""])[-1][-160:]})
    return out, rc


def scheduler():
    while True:
        try:
            st = settings(); h = float(st.get("auto_refresh_hours") or 0)
            last = st.get("last_refresh")
            wait = 0.25 if str(st.get("last_result", "")).startswith("失败") else h  # 失败了 15 分钟后重试
            due = h > 0 and (not last or time.time() - time.mktime(time.strptime(last, "%Y-%m-%d %H:%M")) >= wait * 3600)
            if due: refresh_stats()
        except Exception as e:
            print("scheduler:", e)
        time.sleep(60)


def trend():
    import csv
    cat = {}
    try: cat = json.load(open(os.path.join(SHOP, "data", "catalog.json"), encoding="utf-8"))
    except Exception: pass
    agg = {}
    try:
        for r in csv.DictReader(open(os.path.join(SHOP, "data", "stats", "daily.csv"), encoding="utf-8")):
            c = (cat.get(r["goods_id"]) or {}).get("category") or "未标"
            a = agg.setdefault(r["date"], {}).setdefault(c, {"browse": 0, "want": 0, "n": 0})
            a["browse"] += int(r["browseCount"] or 0); a["want"] += int(r["wantNum"] or 0); a["n"] += 1
    except Exception: pass
    return {"dates": sorted(agg), "data": agg}


def improvements(add=None):
    p = os.path.join(SHOP, "workflow", "improvements.md")
    if add:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"\n## {time.strftime('%Y-%m-%d')} 店主记录\n- {add.strip()}\n")
    return read(p)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        try:
            if u.path == "/":
                return self.send(200, open(os.path.join(HERE, "index.html"), "rb").read(), "text/html; charset=utf-8")
            if u.path == "/api/state":
                return self.send(200, {"shop": ENV.get("YIDIAN_NICK", ""), "shop_dir": SHOP, "items": items(), "running": running(),
                                       "price": [ENV.get("PRICE_MIN", "0.1"), ENV.get("PRICE_MAX", "1.9")],
                                       "roles": {k[5:].lower(): v for k, v in ENV.items() if k.startswith("ROLE_")}})
            if u.path == "/api/item":
                return self.send(200, item_detail(q["code"]))
            if u.path == "/api/orders":
                out, _ = sh("orders", q.get("days", "7"))
                return self.send(200, {"out": out})
            if u.path == "/api/live":
                r = subprocess.run(["python3", YIDIAN, "list"], capture_output=True, text=True, env={**os.environ, **ENV}, timeout=60)
                return self.send(200, {"out": (r.stdout or r.stderr).strip()})
            if u.path == "/api/doctor":
                out, rc = sh("doctor", timeout=180)
                return self.send(200, {"out": out, "ok": rc == 0})
            if u.path == "/api/log":
                name = os.path.basename(q["name"])
                s = read(os.path.join(LOGS, name))
                return self.send(200, {"out": s[-int(q.get("n", 6000)):]})
            if u.path == "/api/improvements":
                return self.send(200, {"out": improvements()})
            if u.path == "/api/categories":
                return self.send(200, {**categories(), "settings": settings()})
            if u.path == "/api/trend":
                return self.send(200, trend())
            if u.path.startswith("/file/"):
                rel = urllib.parse.unquote(u.path[6:])
                p = os.path.realpath(os.path.join(ASSETS, rel))
                if not p.startswith(ASSETS + os.sep) or not os.path.isfile(p):
                    return self.send(404, {"error": "没有这个文件"})
                return self.send(200, open(p, "rb").read(), mimetypes.guess_type(p)[0] or "application/octet-stream")
            self.send(404, {"error": "not found"})
        except Exception as e:
            self.send(400, {"error": str(e)})

    def do_POST(self):
        # 只接受本页发来的请求
        if self.headers.get("X-Workbench") != "1" or (self.headers.get("Origin") or "").split("//")[-1] not in ("", self.headers.get("Host")):
            return self.send(403, {"error": "forbidden"})
        n = int(self.headers.get("Content-Length") or 0)
        b = json.loads(self.rfile.read(n) or b"{}")
        try:
            if self.path == "/api/new":
                return self.send(200, new_item(b["code"].strip(), b.get("benchmark", "").strip(), b.get("source", "").strip(), b.get("note", "")))
            if self.path == "/api/dispatch":
                return self.send(200, dispatch(b["code"], b["step"], b.get("note", ""), {}))
            if self.path == "/api/publish":
                return self.send(200, publish(b["code"], b["price"], bool(b.get("dry", True))))
            if self.path == "/api/archive":
                d = safe_asset(b["code"]); f = os.path.join(d, ".archived")
                if b.get("on", True): open(f, "w").write(time.strftime("%Y-%m-%d %H:%M:%S"))
                elif os.path.exists(f): os.remove(f)
                return self.send(200, {"ok": True})
            if self.path == "/api/stats":
                out, rc = refresh_stats()
                return self.send(200, {"out": out, "ok": rc == 0})
            if self.path == "/api/settings":
                h = float(b.get("auto_refresh_hours", 6))
                return self.send(200, settings({"auto_refresh_hours": max(0.0, h)}))
            if self.path == "/api/price":
                out, _ = sh("price")
                return self.send(200, {"price": out.strip()})
            if self.path == "/api/improvements":
                return self.send(200, {"out": improvements(b.get("text", ""))})
            self.send(404, {"error": "not found"})
        except Exception as e:
            self.send(400, {"error": str(e)})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"工作台：http://127.0.0.1:{port}   店铺目录：{SHOP}")
    import threading
    threading.Thread(target=scheduler, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
