---
name: data-gov-tw
description: 從政府資料開放平臺 data.gov.tw 查詢與下載開放資料。當使用者提到「政府開放資料」、「data.gov.tw」、「開放平臺」、「資料集」、「dataset ID」、「政府統計」，或想抓某個部會／地方政府公開的 CSV/JSON/XML 資料時使用。處理中介資料查詢、檔案下載網址、編碼偵測（UTF-8/Big5/CP950）與各機關伺服器的 TLS 問題。
---

# 政府資料開放平臺 data.gov.tw

## 這個平臺實際上長什麼樣

**平臺只存中介資料，不存檔案。** 每個資料集的實際檔案放在各機關自己的
伺服器上（`ws.dgbas.gov.tw`、`opendata.cwa.gov.tw`、`opendata.tycg.gov.tw`…）。
所以平臺說有資料 ≠ 檔案抓得到。這是最常踩的坑。

## API 的真實樣貌（已實測）

| 端點 | 方法 | 金鑰 | 狀態 |
| --- | --- | --- | --- |
| `/api/v2/rest/dataset/{數字ID}` | GET | 不用 | 可用 |
| `/api/v2/rest/dataset` | POST | **要** | 查詢／清單 |
| `/api/v1/datasets` | — | — | **不存在（404）** |

`/api/v1/datasets` 是很多文章上寫的，但平臺實際回 404。正確的是 v2，
而且單筆查詢的路徑最後要接**數字 ID**，接 `search`、`list` 都會回
「Expected number」。

金鑰用 `Authorization: <金鑰>` 標頭傳，**不是** `Bearer <金鑰>`。

## 用法

```bash
# 個人安裝（所有專案都能用）
S=~/.claude/skills/data-gov-tw/scripts/datagov.py
# 專案安裝
# S=.claude/skills/data-gov-tw/scripts/datagov.py

python3 $S meta 6019              # 中介資料：標題、更新頻率、有幾個檔
python3 $S resources 6019         # 每個檔的格式、下載網址、欄位名
python3 $S fetch 8409 --limit 20  # 下載實際資料並預覽
python3 $S fetch 8409 --out d.csv # 存檔
python3 $S fetch 6068 --index 2   # 抓第 3 個檔（多檔資料集）
python3 $S search 空氣品質         # 需要金鑰
```

**資料集 ID 怎麼找**：平臺網址 `https://data.gov.tw/dataset/6019` 裡的
`6019` 就是。網站搜尋是前端渲染的，抓 HTML 拿不到結果，所以沒有金鑰時
請使用者自己在 `https://data.gov.tw/datasets/search?qs=關鍵字` 找 ID。

**申請金鑰**：data.gov.tw 註冊會員 → 會員專區 → API 金鑰申請，
然後 `export DATA_GOV_TW_KEY='...'`。

## 已知的坑（都實測過）

**1. TLS 憑證驗證失敗。** 有些機關伺服器（例如主計總處 `ws.dgbas.gov.tw`）
送出的憑證鏈掛在中華電信 ePKI Root G2，或中繼憑證漏送，一般信任庫驗不過。
腳本會給明確診斷而不是 traceback。**不要用 `verify=False` 繞過**——
那等於放棄驗證伺服器身分。要處理就用 `--ca-bundle` 指定含正確憑證的檔案，
或請使用者用瀏覽器手動下載。

**2. 宣告編碼常常是錯的。** 平臺欄位寫 UTF-8 但檔案是 Big5 很常見。
腳本會實際試解（`utf-8-sig` → `cp950` → `big5` → `utf-8`）並印出真正用的編碼。

**3. CSV 常有兩列標題。** 第一列英文欄名、第二列中文欄名（內政部的檔尤其如此）。
寫解析程式時記得跳過第二列，不然會被當成資料。

**4. 中介資料的機關欄位不是人看的。** `dataProvider` 是平臺帳號
（像 `bannanng30`），`license` 一律是 `"1"`。要知道是哪個機關，看
`title` 和 `identifier` 前綴的機關代碼。

**5. `resourceAmount`（筆數）是平臺記的，不保證跟現在的檔案一致。**
機關換檔不一定會回頭更新中介資料。

## 交叉引用

要抓的是**台股／金融**資料（證交所、櫃買、期交所、公開資訊觀測站）時，
用 `data-extraction` skill，那邊有專門的來源與容錯邏輯，不要用這個。
