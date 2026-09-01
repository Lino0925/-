#!/usr/bin/env python3
"""政府資料開放平臺 (data.gov.tw) 命令列工具。

公開端點（不用金鑰）：
    GET https://data.gov.tw/api/v2/rest/dataset/{numeric_id}

需要金鑰的端點（POST + Authorization 標頭）：
    POST https://data.gov.tw/api/v2/rest/dataset
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.parse

import requests

API_BASE = "https://data.gov.tw/api/v2/rest/dataset"
CA_BUNDLE = None  # 由 --ca-bundle 設定；None = 用系統信任庫
UA = "Mozilla/5.0 (compatible; claude-code-datagov/1.0)"
TIMEOUT = 45


def die(msg, code=1):
    print(f"錯誤：{msg}", file=sys.stderr)
    sys.exit(code)



def http_get(url):
    """統一的 GET，把 TLS 失敗轉成看得懂的診斷而不是 traceback。"""
    kw = {"verify": CA_BUNDLE} if CA_BUNDLE else {}
    try:
        return requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, **kw)
    except requests.exceptions.SSLError as e:
        host = urllib.parse.urlparse(url).netloc
        die(f"TLS 憑證驗證失敗：{host}\n{e}\n\n"
            "資料檔放在各機關自己的伺服器上，不是平臺上，所以憑證品質不一。\n"
            "常見原因是該機關少送中繼憑證，或憑證鏈掛在本機信任庫沒有的根憑證\n"
            f"（例如中華電信 ePKI Root G2）。\n\n"
            "處理方式：\n"
            f"  1. 用瀏覽器開 {url} 手動下載。\n"
            "  2. 取得該機關的中繼／根憑證後，用 --ca-bundle 憑證檔 指定。\n"
            "  3. 不要用 verify=False 繞過——那等於放棄驗證伺服器身分。")
    except requests.exceptions.RequestException as e:
        die(f"連線失敗：{url}\n{type(e).__name__}: {e}")


def get_meta(dataset_id):
    if not str(dataset_id).isdigit():
        die(f"資料集 ID 必須是數字，收到 {dataset_id!r}。"
            "\n平臺網址 https://data.gov.tw/dataset/6019 裡的 6019 就是 ID。")
    r = http_get(f"{API_BASE}/{dataset_id}")
    if r.status_code != 200:
        die(f"HTTP {r.status_code}（平臺回應非 200）")
    try:
        body = r.json()
    except ValueError:
        die(f"回應不是 JSON，前 200 字：{r.text[:200]}")
    if not body.get("success"):
        err = body.get("error", {})
        die(f"{err.get('error_type', '未知')} — {err.get('message', '')}")
    return body["result"]


def fmt_freq(freq):
    if not isinstance(freq, dict):
        return "—"
    n, unit = freq.get("Frequency", ""), freq.get("unittime", "")
    return f"每 {n} {unit}" if n and unit else "—"


def cmd_meta(args):
    d = get_meta(args.dataset_id)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
        return
    print(f"標題      : {d.get('title', '—')}")
    # dataProvider 是平臺帳號不是機關名稱；license 一律回代碼 "1"。
    print(f"提供者帳號: {d.get('dataProvider', '—')}")
    lic = str(d.get("license", ""))
    print(f"授權      : {'政府資料開放授權條款' if lic == '1' else (lic or '—')}")
    print(f"計費      : {d.get('cost', '—')}")
    print(f"更新頻率  : {fmt_freq(d.get('updateFrequency'))}")
    print(f"發布日期  : {d.get('publishedDate', '—')}")
    print(f"最後異動  : {d.get('modifiedDate', '—')}")
    kw = d.get("keyword")
    if kw:
        print(f"關鍵字    : {'、'.join(kw) if isinstance(kw, list) else kw}")
    cov = (d.get("coverageStartedDate"), d.get("coverageEndedDate"))
    if any(cov):
        print(f"資料期間  : {cov[0] or '?'} ~ {cov[1] or '?'}")
    desc = (d.get("description") or "").strip()
    if desc:
        print(f"\n說明：\n{desc}")
    dists = d.get("distribution") or []
    print(f"\n檔案（{len(dists)} 個）：")
    for i, dist in enumerate(dists):
        amt = dist.get("resourceAmount")
        amt = f"{amt:,} 筆" if isinstance(amt, int) else "—"
        print(f"  [{i}] {dist.get('resourceFormat', '?'):5s} {amt:>12s}  "
              f"{dist.get('resourceDescription', '')}")


def cmd_resources(args):
    d = get_meta(args.dataset_id)
    dists = d.get("distribution") or []
    if not dists:
        die("這個資料集沒有掛任何檔案。")
    for i, dist in enumerate(dists):
        print(f"[{i}] {dist.get('resourceDescription', '')}")
        print(f"    格式  : {dist.get('resourceFormat', '?')}"
              f"  編碼: {dist.get('resourceCharacterEncoding', '?')}")
        print(f"    網址  : {dist.get('resourceDownloadUrl', '—')}")
        amt = dist.get("resourceAmount")
        if isinstance(amt, int):
            print(f"    筆數  : {amt:,}")
        qc = dist.get("resourceQualityCheckTime")
        if qc:
            print(f"    檢核  : {qc}")
        fields = dist.get("resourceField") or []
        if fields:
            names = [f.get("name", "?") for f in fields]
            print(f"    欄位  : {'、'.join(names)}")
        print()


def sniff_encoding(raw, declared):
    """平臺宣告的編碼常常是錯的，所以實際解一次看看。"""
    cands = []
    if declared:
        cands.append(declared.lower().replace("-", "").replace("_", ""))
    order = {"utf8": "utf-8-sig", "utf8bom": "utf-8-sig",
             "big5": "big5", "ms950": "cp950", "cp950": "cp950"}
    tries = [order.get(c, c) for c in cands]
    tries += ["utf-8-sig", "cp950", "big5", "utf-8"]
    for enc in tries:
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8(取代不可解字元)"


def cmd_fetch(args):
    d = get_meta(args.dataset_id)
    dists = d.get("distribution") or []
    if not dists:
        die("這個資料集沒有掛任何檔案。")
    if args.index >= len(dists):
        die(f"--index {args.index} 超出範圍，這個資料集只有 {len(dists)} 個檔案（0~{len(dists)-1}）。")
    dist = dists[args.index]
    url = dist.get("resourceDownloadUrl")
    if not url:
        die(f"第 {args.index} 個檔案沒有下載網址。")

    fmt = (dist.get("resourceFormat") or "").upper()
    print(f"# {d.get('title', '')} — {dist.get('resourceDescription', '')}", file=sys.stderr)
    print(f"# {fmt} <- {url}", file=sys.stderr)

    r = http_get(url)
    if r.status_code != 200:
        die(f"下載失敗 HTTP {r.status_code}。原始檔在提供機關的伺服器上，"
            "平臺的中介資料可能比實際檔案新。")
    raw = r.content
    print(f"# 收到 {len(raw):,} bytes", file=sys.stderr)

    if args.out:
        with open(args.out, "wb") as fh:
            fh.write(raw)
        print(f"# 已寫入 {args.out}", file=sys.stderr)

    text, enc = sniff_encoding(raw, dist.get("resourceCharacterEncoding"))
    if enc:
        print(f"# 解碼用 {enc}", file=sys.stderr)

    if fmt == "CSV":
        rows = list(csv.reader(io.StringIO(text)))
        for row in rows[: args.limit + 1]:
            print(" | ".join(row))
        if len(rows) > args.limit + 1:
            print(f"... 共 {len(rows) - 1:,} 列（含標題列 {len(rows):,}），"
                  f"上面只顯示 {args.limit} 列")
    elif fmt == "JSON":
        try:
            obj = json.loads(text)
        except ValueError:
            print(text[:4000])
            return
        if isinstance(obj, list):
            print(json.dumps(obj[: args.limit], ensure_ascii=False, indent=2))
            print(f"... 共 {len(obj):,} 筆，上面只顯示 {args.limit} 筆")
        else:
            print(json.dumps(obj, ensure_ascii=False, indent=2)[:4000])
    else:
        print(text[:4000])
        if len(text) > 4000:
            print(f"\n... 全文 {len(text):,} 字；"
                  f"要完整內容請加 --out 檔名 存成檔案再處理")


def cmd_search(args):
    key = os.environ.get("DATA_GOV_TW_KEY")
    if not key:
        die("查詢/清單 API 需要金鑰，但環境變數 DATA_GOV_TW_KEY 沒設定。\n\n"
            "取得方式：到 https://data.gov.tw 註冊會員 → 會員專區 → API 金鑰申請。\n"
            "拿到後：export DATA_GOV_TW_KEY='你的金鑰'\n\n"
            "不想申請金鑰的話，就到 https://data.gov.tw/datasets/search?qs=關鍵字\n"
            "用網頁找，網址裡的數字就是 ID，再用 meta / fetch 子指令即可。")
    payload = {"q": args.keyword, "limit": args.limit}
    r = requests.post(API_BASE, json=payload, timeout=TIMEOUT,
                      headers={"User-Agent": UA, "Authorization": key,
                               "Content-Type": "application/json"})
    try:
        body = r.json()
    except ValueError:
        die(f"回應不是 JSON（HTTP {r.status_code}）：{r.text[:200]}")
    if not body.get("success"):
        err = body.get("error", {})
        die(f"{err.get('error_type', '未知')} — {err.get('message', '')}")
    print(json.dumps(body.get("result"), ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(
        description="政府資料開放平臺 data.gov.tw 查詢工具")
    p.add_argument("--ca-bundle",
                   help="自訂 CA 憑證檔，用於憑證鏈不完整的機關伺服器")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("meta", help="看資料集的中介資料")
    m.add_argument("dataset_id")
    m.add_argument("--json", action="store_true", help="輸出原始 JSON")
    m.set_defaults(func=cmd_meta)

    rs = sub.add_parser("resources", help="列出檔案、下載網址與欄位")
    rs.add_argument("dataset_id")
    rs.set_defaults(func=cmd_resources)

    f = sub.add_parser("fetch", help="下載實際資料並預覽")
    f.add_argument("dataset_id")
    f.add_argument("--index", type=int, default=0, help="第幾個檔案（預設 0）")
    f.add_argument("--limit", type=int, default=10, help="預覽幾列（預設 10）")
    f.add_argument("--out", help="另存成檔案")
    f.set_defaults(func=cmd_fetch)

    s = sub.add_parser("search", help="關鍵字查資料集（需要 API 金鑰）")
    s.add_argument("keyword")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=cmd_search)

    args = p.parse_args()
    global CA_BUNDLE
    if getattr(args, "ca_bundle", None):
        if not os.path.exists(args.ca_bundle):
            die(f"--ca-bundle 指到的檔案不存在：{args.ca_bundle}")
        CA_BUNDLE = args.ca_bundle
    args.func(args)


if __name__ == "__main__":
    main()
