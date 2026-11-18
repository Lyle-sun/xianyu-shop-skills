#!/usr/bin/env python3
"""Render a Xianyu main image (1080x1440 for 3:4, or 1080x1080 for 1:1) from a JSON spec.

Usage: python3 render.py spec.json out.png
Writes out.png, out.thumb.png (360px, to check how it reads in search results)
and out.html (editable source) next to it. Needs Google Chrome; no Python packages.
"""
import json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "templates", "main.html")
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "", shutil.which("chromium") or "",
]

def chrome():
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    sys.exit("Google Chrome not found; install it or render the .html in a browser at 1080x1080.")

def shot(html, png, scale, h=1080):
    subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--force-device-scale-factor={scale}", f"--window-size=1080,{h}",
                    "--virtual-time-budget=8000", f"--screenshot={png}", "file://" + html],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    spec_path, out = sys.argv[1], os.path.abspath(sys.argv[2])
    spec = json.load(open(spec_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(spec_path))
    # make local image paths absolute file:// URLs for the preview layout
    spec["images"] = ["file://" + os.path.abspath(os.path.join(base, p)) if not p.startswith(("http", "file:")) else p
                      for p in spec.get("images", [])]
    # 3:4 (1080x1440) is the default for overlay; other layouts stay 1:1 unless spec says size "3:4"
    size = spec.get("size") or ("3:4" if spec.get("layout") == "overlay" else "1:1")
    h = 1440 if size == "3:4" else 1080
    spec["_h"] = h
    tpl = open(TEMPLATE, encoding="utf-8").read()
    inject = "<script>window.SPEC = " + json.dumps(spec, ensure_ascii=False) + ";</script>"
    html_path = os.path.splitext(out)[0] + ".html"
    open(html_path, "w", encoding="utf-8").write(tpl.replace("<!--SPEC-->", inject))
    shot(html_path, out, 1, h)
    shot(html_path, os.path.splitext(out)[0] + ".thumb.png", 1 / 3, h)
    print(out)

if __name__ == "__main__":
    main()
