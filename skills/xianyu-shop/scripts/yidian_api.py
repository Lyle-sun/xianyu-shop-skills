#!/usr/bin/env python3
"""易店（鱼店助手）上架命令行工具，给 DSH 等 Agent 用。

登录凭证：用户自己把易店 token 存到 ~/.config/yidian/token（chmod 600），
或设环境变量 YIDIAN_TOKEN。脚本只读取、不打印、不外传。Agent 不要去浏览器里取 token。

用法：
  python3 yidian_api.py list                    # 列出在售商品（id / 标题 / 价格）
  python3 yidian_api.py show <goods_id>         # 看一个商品的标题、价格、图片、正文
  python3 yidian_api.py update <goods_id> [--title T] [--body-file F] [--main-image J] [--price P] [--dry-run]
                                                # 改在售商品（必须店主同意），只改传入的字段
  python3 yidian_api.py offshelf|onshelf <goods_id>   # 下架 / 重新上架（不删除商品）
  python3 yidian_api.py publish <包目录> [--dry-run] [--skip-review]
      加 --at "2026-11-16 07:00:00" 走易店自带的定时发布（电脑关机也照常发），自动发货配在定时商品上。
  python3 yidian_api.py orders [天数]            # 最近几天的订单（默认 2 天，只读，不含买家信息）
  python3 yidian_api.py timed                   # 列出易店「定时上架商品」
      默认只发 review.txt 第一行是 PASS 或 FIXED 的包；单品临时上架（店主点头）才用 --skip-review。
      包目录里需要：title.txt（第一行是标题）、body.txt、delivery.txt、manifest.json（category、price），
      以及上传图：main-upload.jpg（主图）+ preview-*.jpg / shots/*.jpg（详情图，最多再放 8 张）。
      成功后写 published.json（goods_id、图片地址、时间），已有 published.json 的包会跳过。
"""
import json, os, sys, time, uuid, glob, urllib.request, urllib.parse

BASE = "https://ed.weeeg.com"
CATE = {"电子资料": "50", "设计素材": "54"}
CATE_ALIAS = {"资料包": "电子资料", "教程": "电子资料", "模板素材": "设计素材", "模板": "设计素材", "素材": "设计素材"}
NICK = os.environ.get("YIDIAN_NICK") or sys.exit("缺 YIDIAN_NICK：先 source 店铺配置 shop-config.env")
ADDRESS = json.loads(os.environ.get("YIDIAN_ADDRESS", "[1, 35, 408]"))
DEFAULTS = dict(address=ADDRESS, freight=4, postage=0, quan=999, nick=NICK)
DELIVER_TPL = {"id": 0, "nick_id": NICK, "disk_type": 1, "wp_txt": "", "cdk_txt": "", "xm_cdkname": "",
    "is_show": 1, "goods_id": "", "wp_start_name": "", "cdk_start_name": "", "ids": "", "custom_form": [],
    "kktemplate": "", "spec": "", "cdkChange": False, "spec_type": 0, "senior_open": 0, "senior_state": False,
    "close_pending_update": False, "addendum_state": False, "addendum_txt": "", "cdk_send_num": 1,
    "purchase_limit": "{\"quantity\":0,\"time_limit\":0,\"auto_close\":0}",
    "shipping_evidence": "{\"open\":0,\"txt\":\"\",\"images\":[]}",
    "good_comment_gift": "{\"open\":0,\"disk_type\":1,\"wp_txt\":\"\",\"cdk_txt\":\"\",\"cdk_name\":\"\",\"cdk_send_num\":1}",
    "card_header_config": "{\"open\":0,\"card_mode\":\"password_only\",\"card_header\":\"\",\"password_header\":\"\"}",
    "auto_offshelf": 0}


def token():
    t = os.environ.get("YIDIAN_TOKEN")
    if not t:
        p = os.path.expanduser("~/.config/yidian/token")
        if os.path.exists(p):
            t = open(p).read().strip()
    if not t:
        sys.exit("缺 token：请用户把易店 token 存到 ~/.config/yidian/token（Agent 不要自己去取）")
    return urllib.parse.unquote(t)


def req(method, path, data=None, ctype="application/json;charset=UTF-8"):
    h = {"Accept": "application/json, text/plain, */*", "Authori-zation": "Bearer " + token(),
         "Origin": BASE, "Referer": BASE + "/ekadmin/product/product_list",
         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
    if data is not None:
        h["Content-Type"] = ctype
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False).encode()
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=60) as resp:
        j = json.loads(resp.read().decode())
    if j.get("status") != 200:
        raise RuntimeError(f"{path} 失败：{j.get('msg')}")
    return j


def upload(fp):
    b = uuid.uuid4().hex
    name = os.path.basename(fp)
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            f"Content-Type: image/jpeg\r\n\r\n").encode() + open(fp, "rb").read() + f"\r\n--{b}--\r\n".encode()
    j = req("POST", "/adminapi/file/upload", body, f"multipart/form-data; boundary={b}")
    return j["data"]["src"]


def list_live(name=""):
    q = urllib.parse.urlencode({"page": 1, "limit": 100, "cate_id": "", "type": 1, "store_name": "", "name": name})
    j = req("GET", "/adminapi/product/product?" + q)
    return [{"id": x["goods_id"], "title": x["store_name"], "price": x["price"]} for x in j["data"]["list"]]


def list_timed():
    q = urllib.parse.urlencode({"page": 1, "limit": 100, "cate_id": "", "type": 7, "store_name": "", "name": ""})
    j = req("GET", "/adminapi/product/product?" + q)
    return [{"id": x.get("id"), "title": x["store_name"], "price": x["price"], "at": x.get("dsfabu_time")} for x in j["data"]["list"]]


def free_uploads(urls):
    """删掉易店「照片存储」里这些上传记录（易店上限 200 条）。只删记录，不删商品：
    闲鱼上架时会把图转存到自己的 bao/uploaded 地址，商品不再引用这些上传记录（2026-11-19 实测）。"""
    urls = set(urls); ids = []
    for page in range(1, 10):
        d = req("GET", "/adminapi/file/file?" + urllib.parse.urlencode({"page": page, "limit": 50, "pid": 0}))["data"]
        ids += [str(r["att_id"]) for r in d["list"] if r.get("att_dir") in urls]
        if len(d["list"]) < 50: break
    if ids:
        req("POST", "/adminapi/file/file/delete", {"ids": ",".join(ids)})
    return len(ids)


def publish(d, dry=False, skip_review=False, at=None):
    """at="YYYY-MM-DD HH:MM:SS" 时用易店自带的定时发布：先进「定时上架商品」，到点由易店发到闲鱼。"""
    if os.path.exists(f"{d}/published.json"):
        print("跳过（已上架）", d); return
    if not skip_review:
        rv = f"{d}/review.txt"
        verdict = open(rv, encoding="utf-8").read().strip().split()[0].upper() if os.path.exists(rv) and open(rv, encoding="utf-8").read().strip() else ""
        if verdict not in ("PASS", "FIXED"):
            print(f"跳过（复核未通过：{verdict or '没有 review.txt'}）", d); return
    title = open(f"{d}/title.txt", encoding="utf-8").read().strip().splitlines()[0].strip()
    body = open(f"{d}/body.txt", encoding="utf-8").read().strip()
    wp = open(f"{d}/delivery.txt", encoding="utf-8").read().strip()
    m = json.load(open(f"{d}/manifest.json", encoding="utf-8"))
    cat = m.get("category", "电子资料"); cat = CATE_ALIAS.get(cat, cat)
    if cat not in CATE: sys.exit(f"不认识的分类：{cat}（只能是 {list(CATE)}）")
    price = float(m.get("price", 1))
    main = f"{d}/main-upload.jpg"
    if not os.path.exists(main):
        sys.exit(f"缺主图 {main}")
    extra = sorted(glob.glob(f"{d}/preview-*.jpg")) + sorted(glob.glob(f"{d}/shots/*.jpg"))
    imgs = [main] + extra[:8]
    if len(title) > 30: sys.exit(f"标题超过 30 字：{title}")
    if "pan.quark.cn/s/" not in wp and not any(k in wp for k in ("feishu.cn/docx/", "feishu.cn/wiki/")):
        sys.exit("delivery.txt 里没有夸克分享链接或飞书文档链接")
    if any(x["title"] == title for x in list_live(title)):
        sys.exit(f"易店里已有同名商品：{title}")
    if at:
        import datetime as _dt
        _t = _dt.datetime.strptime(at, "%Y-%m-%d %H:%M:%S")
        if _t <= _dt.datetime.now() + _dt.timedelta(minutes=5): sys.exit(f"定时时间要晚于现在 5 分钟以上：{at}")
        if any(x["title"] == title for x in list_timed()): sys.exit(f"定时列表里已有同名商品：{title}")
    print(f"标题：{title}\n分类：{cat}  价格：{price}\n图片：{[os.path.basename(i) for i in imgs]}" + (f"\n定时：{at}" if at else ""))
    if dry: return
    urls = []
    for i in imgs:
        urls.append(upload(i)); time.sleep(0.5)
    p = dict(address=DEFAULTS["address"], attrs=[], cate_id=[CATE[cat]], categoryName=cat, dsfabu_open=1 if at else 0, dsfabu_time=at or "",
             freight=DEFAULTS["freight"], id=0, is_virtual=0, items=[], nick=DEFAULTS["nick"], nick_id=DEFAULTS["nick"],
             other="", polishing_open=0, polishing_time=0, postage=DEFAULTS["postage"], price=f"{price:.2f}",
             quan=DEFAULTS["quan"], quans=DEFAULTS["quan"], sellingxin=False, slider_image=urls, spec_type=0,
             store_info=body, store_name=title, virtual_type=0)
    req("POST", "/adminapi/product/product_goods/0", p)
    if at:
        tid = None
        for _ in range(6):
            time.sleep(2.5)
            hit = [x for x in list_timed() if x["title"] == title]
            if hit: tid = hit[0]["id"]; break
        if not tid:
            sys.exit("已提交定时发布，但「定时上架商品」里没找到，请人工去易店确认，不要重复提交")
        dv = dict(DELIVER_TPL, goods_id="", wp_txt=wp)
        req("POST", f"/adminapi/product/timed_delivery/{tid}", dv)
        back = req("GET", f"/adminapi/product/timed_delivery/{tid}")["data"]
        ok = wp.split("链接：")[-1][:40] in json.dumps(back, ensure_ascii=False)
        json.dump({"timed_id": tid, "scheduled_at": at, "title": title, "price": price, "images": urls,
                   "delivery_verified": ok, "time": time.strftime("%Y-%m-%d %H:%M:%S")},
                  open(f"{d}/published.json", "w"), ensure_ascii=False, indent=1)
        print(f"已进定时上架：timed_id={tid}  {at}  {title}  自动发货{'已配置' if ok else '回读没对上，请人工检查'}")
        return
    gid = None
    for _ in range(6):
        time.sleep(2.5)
        hit = [x for x in list_live(title) if x["title"] == title]
        if hit: gid = hit[0]["id"]; break
    if not gid:
        sys.exit("已提交发布，但列表里没找到新商品，请人工去易店确认，不要重复发布")
    dv = dict(DELIVER_TPL, goods_id=str(gid), wp_txt=wp)
    req("POST", "/adminapi/product/product/0", dv)
    json.dump({"goods_id": gid, "title": title, "price": price, "images": urls,
               "time": time.strftime("%Y-%m-%d %H:%M:%S")}, open(f"{d}/published.json", "w"), ensure_ascii=False, indent=1)
    try:
        n = free_uploads(urls)
        print(f"已上架并配置自动发货：{gid}  {title}（清掉易店照片存储 {n} 条上传记录）")
    except Exception as e:
        print(f"已上架并配置自动发货：{gid}  {title}（清理照片存储失败，不影响商品：{e}）")


ORDER_STATUS = {1: "待发货", 2: "待收货", 3: "交易完成", 4: "交易关闭", 5: "退款中"}


def list_orders(days=None, limit=100):
    """最近订单（只读）。不输出买家信息。"""
    import datetime as _dt
    q = f"page=1&limit={limit}&status=&dianpuType=&data=&real_name=&field_key=&type="
    rows = req("GET", "/adminapi/home/xianyu_list?" + q)["data"]["lists"]
    if days:
        cut = (_dt.datetime.now() - _dt.timedelta(days=int(days))).strftime("%Y-%m-%d %H:%M:%S")
        rows = [r for r in rows if (r.get("pay_time") or "") >= cut]
    return [{"time": r.get("pay_time"), "goods_id": r.get("goods_id"), "title": r.get("name"),
             "money": r.get("money"), "status": ORDER_STATUS.get(r.get("order_status"), r.get("order_status"))} for r in rows]


def show(gid):
    d = req("GET", f"/adminapi/product/productedit/{gid}")["data"]
    return d


def update(gid, title=None, body=None, images=None, price=None, dry=False):
    """改在售商品。只改传入的字段，其余保持原样。改之前要店主同意。"""
    d = show(gid)
    old = dict(title=d["store_name"], price=d["price"], n_img=len(d["slider_image"]))
    p = {k: d[k] for k in d}
    p.update(id=gid, attrs=p.get("attrs", []), items=p.get("items", []), dsfabu_open=0,
             categoryName=p.get("categoryName", ""), quans=p.get("quan"))
    if title: p["store_name"] = title
    if body: p["store_info"] = body
    if images: p["slider_image"] = images
    if price is not None: p["price"] = f"{float(price):.2f}"
    if len(p["store_name"]) > 30: sys.exit(f"标题超过 30 字：{p['store_name']}")
    print("原：", old); print("新：", dict(title=p["store_name"], price=p["price"], n_img=len(p["slider_image"]), body_changed=bool(body)))
    if dry: return
    req("POST", f"/adminapi/product/product_goods/{gid}", p)
    print("已更新", gid)


def set_show(gid, on):
    req("PUT", f"/adminapi/product/product/set_show/{gid}/{1 if on else 0}", {})
    print(("已上架 " if on else "已下架 ") + str(gid))


if __name__ == "__main__":
    import argparse
    a = sys.argv[1:]
    if a and a[0] == "orders":
        days = a[1] if len(a) > 1 else 2
        L = list_orders(days)
        for x in L: print(x["time"], x["status"], f'¥{x["money"]}', x["title"])
        print(f"近 {days} 天共 {len(L)} 单，合计 ¥{sum(float(x['money'] or 0) for x in L):.2f}"); sys.exit(0)
    if a and a[0] == "timed":
        L = list_timed()
        for x in L: print(x["id"], x["at"], x["price"], x["title"])
        print(f"共 {len(L)} 个定时商品"); sys.exit(0)
    if a and a[0] == "free-uploads":  # 给已上架的包补清照片存储：free-uploads <包目录>...
        import glob as _g
        for d in a[1:]:
            pj = os.path.join(d, "published.json")
            if os.path.exists(pj) and json.load(open(pj)).get("goods_id"):
                print(d, "清掉", free_uploads(json.load(open(pj))["images"]), "条")
        sys.exit(0)
    if not a or a[0] not in ("list", "publish", "show", "update", "offshelf", "onshelf"):
        print(__doc__); sys.exit(1)
    if a[0] == "list":
        for x in list_live(): print(x["id"], x["price"], x["title"])
    elif a[0] == "publish":
        at = a[a.index("--at") + 1] if "--at" in a else None
        publish(a[1].rstrip("/"), dry="--dry-run" in a, skip_review="--skip-review" in a, at=at)
    elif a[0] == "show":
        d = show(a[1]); print(json.dumps({"title": d["store_name"], "price": d["price"], "images": d["slider_image"], "body": d["store_info"]}, ensure_ascii=False, indent=1))
    elif a[0] == "update":
        ap = argparse.ArgumentParser(); ap.add_argument("gid"); ap.add_argument("--title"); ap.add_argument("--body-file")
        ap.add_argument("--main-image", help="新主图 jpg，替换第 1 张"); ap.add_argument("--price"); ap.add_argument("--dry-run", action="store_true")
        o = ap.parse_args(a[1:])
        body = open(o.body_file, encoding="utf-8").read().strip() if o.body_file else None
        imgs = None
        if o.main_image:
            cur = show(o.gid)["slider_image"]
            imgs = [cur[0]] + cur[1:] if o.dry_run else [upload(o.main_image)] + cur[1:]
        update(o.gid, o.title, body, imgs, o.price, o.dry_run)
    else:
        set_show(a[1], a[0] == "onshelf")
