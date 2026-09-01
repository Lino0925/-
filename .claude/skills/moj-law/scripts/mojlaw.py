#!/usr/bin/env python3
"""全國法規資料庫 (law.moj.gov.tw) 命令列工具。

兩個資料來源：
  官方 API   https://law.moj.gov.tw/api/{Ch|En}/{Law|Order}/{json|xml}
             整包 ZIP，每天更新，最新但是單一大檔。
  kong0107   https://github.com/kong0107/mojLawSplitJSON
             把官方資料切成一法一檔，多了 divisions（編章節）結構，
             但更新較慢（每週），資料日期看 UpdateDate.txt。

條號編碼（kong0107 版）：條次 × 100 + 之N
    第 1 條    -> 100
    第 15 條   -> 1500
    第 15 條之1 -> 1501
    第 164 條之1 -> 16401
"""
import argparse
import io
import json
import os
import re
import sys
import zipfile

import requests

API = "https://law.moj.gov.tw/api"
RAW = "https://raw.githubusercontent.com/kong0107/mojLawSplitJSON"
UA = "Mozilla/5.0 (compatible; claude-code-mojlaw/1.0)"
TIMEOUT = 180
CACHE = os.path.expanduser("~/.cache/moj-law")


def die(msg, code=1):
    print(f"錯誤：{msg}", file=sys.stderr)
    sys.exit(code)


def enc_article(no):
    """把「15-1」「15之1」「15」轉成 kong0107 的整數條號。"""
    m = re.match(r"^\s*(\d+)\s*(?:[-之]\s*(\d+))?\s*$", str(no))
    if not m:
        die(f"看不懂條號 {no!r}。用 15 或 15-1 這種格式。")
    return int(m.group(1)) * 100 + int(m.group(2) or 0)


def dec_article(n):
    main, sub = divmod(int(n), 100)
    return f"第 {main} 條之{sub}" if sub else f"第 {main} 條"


def http_get(url, **kw):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, **kw)
    except requests.exceptions.SSLError as e:
        die(f"TLS 驗證失敗：{url}\n{e}\n\n"
            "多數政府主機的憑證鏈是完整的；若只有某台失敗，通常是該機關的\n"
            "伺服器少送中繼憑證。不要關掉憑證驗證，改用 --ca-bundle 指定\n"
            "含有正確中繼／根憑證的檔案。")
    except requests.exceptions.RequestException as e:
        die(f"連線失敗：{url}\n{type(e).__name__}: {e}")
    if r.status_code != 200:
        die(f"HTTP {r.status_code}：{url}")
    return r


# ---------- kong0107 一法一檔 ----------

def fetch_split(pcode, lang="ch", ref=None):
    ref = ref or "arranged"
    url = f"{RAW}/{ref}/{lang}/{pcode.upper()}.json"
    r = http_get(url)
    try:
        return r.json()
    except ValueError:
        die(f"{url} 回應不是 JSON。確認 pcode 是否存在。")


def cmd_law(args):
    d = fetch_split(args.pcode, args.lang, args.ref)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
        return
    arts = d.get("articles") or []
    print(f"法規名稱 : {d.get('name', '—')}")
    print(f"pcode    : {d.get('pcode', '—')}")
    print(f"位階     : {d.get('LawLevel', '—')}")
    if d.get("EngLawName"):
        print(f"英文名稱 : {d['EngLawName']}")
    print(f"條文數   : {len(arts)}")
    divs = d.get("divisions") or []
    if divs:
        print("\n編章節：")
        def walk(nodes, depth=0):
            for n in nodes:
                print(f"{'  ' * (depth + 1)}{n.get('type', '')} {n.get('title', '')}"
                      f"  ({dec_article(n.get('start', 0))}–{dec_article(n.get('end', 0))})")
                if n.get("children"):
                    walk(n["children"], depth + 1)
        walk(divs)


def cmd_article(args):
    d = fetch_split(args.pcode, args.lang, args.ref)
    want = enc_article(args.number)
    for a in d.get("articles") or []:
        if a.get("number") == want:
            print(f"{d.get('name', '')} {dec_article(want)}\n")
            for para in a.get("content") or []:
                print(para.get("text", ""))
            return
    nums = [a.get("number") for a in d.get("articles") or []]
    near = sorted(nums, key=lambda n: abs((n or 0) - want))[:5]
    die(f"{d.get('name', args.pcode)} 沒有 {dec_article(want)}。\n"
        f"最接近的：{'、'.join(dec_article(n) for n in near)}")


def cmd_grep(args):
    d = fetch_split(args.pcode, args.lang, args.ref)
    pat = re.compile(args.pattern)
    hits = 0
    for a in d.get("articles") or []:
        body = "\n".join(p.get("text", "") for p in a.get("content") or [])
        if pat.search(body):
            hits += 1
            print(f"── {dec_article(a.get('number', 0))} ──")
            print(body)
            print()
            if hits >= args.limit:
                print(f"（只顯示前 {args.limit} 條，要更多請加 --limit）")
                return
    if not hits:
        print(f"{d.get('name', '')} 裡沒有符合 /{args.pattern}/ 的條文。")
    else:
        print(f"共 {hits} 條符合。")


# ---------- 官方整包 ----------

def cmd_bulk(args):
    lang = "Ch" if args.lang == "ch" else "En"
    kind = "Law" if args.kind == "law" else "Order"
    url = f"{API}/{lang}/{kind}/{args.format}"
    print(f"# 下載 {url}", file=sys.stderr)
    r = http_get(url)
    print(f"# 收到 {len(r.content):,} bytes", file=sys.stderr)

    outdir = args.out or os.path.join(CACHE, f"{lang}{kind}")
    os.makedirs(outdir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        names = z.namelist()
        print(f"# ZIP 內容：{'、'.join(names)}", file=sys.stderr)
        z.extractall(outdir)
    print(f"# 已解壓到 {outdir}", file=sys.stderr)

    main = next((n for n in names if n.lower().endswith(".json")), None)
    if main and args.format == "json":
        with open(os.path.join(outdir, main), encoding="utf-8-sig") as fh:
            data = json.load(fh)
        laws = data.get("Laws") or []
        print(f"資料日期 : {data.get('UpdateDate', '—')}")
        print(f"法規筆數 : {len(laws):,}")
        if laws:
            print(f"範例     : {laws[0].get('LawName')}"
                  f"（{len(laws[0].get('LawArticles') or [])} 條）")
        print(f"檔案     : {os.path.join(outdir, main)}")


def cmd_find(args):
    """在官方整包裡用法規名稱找 pcode。"""
    path = args.file
    if not path:
        guess = os.path.join(CACHE, "ChLaw", "ChLaw.json")
        if not os.path.exists(guess):
            die("找不到本機資料。先跑一次：\n"
                "  mojlaw.py bulk --kind law --format json")
        path = guess
    with open(path, encoding="utf-8-sig") as fh:
        data = json.load(fh)
    pat = re.compile(args.keyword)
    n = 0
    for law in data.get("Laws") or []:
        name = law.get("LawName") or ""
        if pat.search(name):
            n += 1
            url = law.get("LawURL") or ""
            pcode = re.search(r"pcode=([A-Z0-9]+)", url, re.I)
            print(f"{pcode.group(1) if pcode else '????????'}  {law.get('LawLevel', ''):4s}  {name}")
            if n >= args.limit:
                print(f"（只顯示前 {args.limit} 筆）")
                return
    if not n:
        print(f"沒有名稱符合 /{args.keyword}/ 的法規。")


def cmd_freshness(args):
    """比較官方 API 與 kong0107 鏡像的資料日期。"""
    r = http_get(f"{RAW}/{args.ref or 'arranged'}/UpdateDate.txt")
    mirror = r.text.strip()
    print(f"kong0107 鏡像 : {mirror}")
    r2 = requests.get(f"{API}/Ch/Law/json", headers={"User-Agent": UA},
                      timeout=TIMEOUT, stream=True)
    buf = io.BytesIO()
    for chunk in r2.iter_content(65536):
        buf.write(chunk)
    with zipfile.ZipFile(buf) as z:
        info = next(i for i in z.infolist() if i.filename.lower().endswith(".json"))
        packed = "%04d%02d%02d" % info.date_time[:3]
        with z.open(info) as fh:
            data = json.loads(fh.read().decode("utf-8-sig"))
    # UpdateDate 是資料本身的異動日；ZIP 內的檔案時間只是打包日，兩者會差幾天。
    raw = str(data.get("UpdateDate", ""))
    m = re.search(r"(\d{4})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(\d{1,2})", raw)
    official = f"{m.group(1)}{int(m.group(2)):02d}{int(m.group(3)):02d}" if m else packed
    print(f"官方 API      : {official}  (UpdateDate={raw or '—'}；打包日 {packed})")
    if official > mirror:
        print("\n官方比鏡像新。要最新條文用 bulk；要一法一檔的結構用 law/article。")
    elif official < mirror:
        print("\n鏡像比官方標示的異動日新（官方可能剛打包但 UpdateDate 未動）。")
    else:
        print("\n兩邊同步。")


def main():
    p = argparse.ArgumentParser(description="全國法規資料庫查詢工具")
    p.add_argument("--lang", choices=["ch", "en"], default="ch")
    p.add_argument("--ref", help="kong0107 的分支或 tag（預設 arranged）")
    sub = p.add_subparsers(dest="cmd", required=True)

    l = sub.add_parser("law", help="看一部法規的概要與編章節")
    l.add_argument("pcode")
    l.add_argument("--json", action="store_true")
    l.set_defaults(func=cmd_law)

    a = sub.add_parser("article", help="讀單一條文")
    a.add_argument("pcode")
    a.add_argument("number", help="條號，如 184 或 15-1")
    a.set_defaults(func=cmd_article)

    g = sub.add_parser("grep", help="在一部法規內以正規式搜條文")
    g.add_argument("pcode")
    g.add_argument("pattern")
    g.add_argument("--limit", type=int, default=10)
    g.set_defaults(func=cmd_grep)

    b = sub.add_parser("bulk", help="下載官方整包（每日更新）")
    b.add_argument("--kind", choices=["law", "order"], default="law")
    b.add_argument("--format", choices=["json", "xml"], default="json")
    b.add_argument("--out", help="解壓目錄")
    b.set_defaults(func=cmd_bulk)

    f = sub.add_parser("find", help="用法規名稱找 pcode（需先跑 bulk）")
    f.add_argument("keyword")
    f.add_argument("--file", help="ChLaw.json 路徑")
    f.add_argument("--limit", type=int, default=20)
    f.set_defaults(func=cmd_find)

    fr = sub.add_parser("freshness", help="比較官方與鏡像的資料日期")
    fr.set_defaults(func=cmd_freshness)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
