---
name: moj-law
description: 查詢全國法規資料庫 law.moj.gov.tw 的法規條文原文。當使用者要查某條法條、要某部法律的全文或編章節結構、要在一部法規裡搜關鍵字、或提到「法規資料庫」、「法務部」、「moj」、「第幾條」、「pcode」時使用。可取得官方每日更新的整包資料，或 kong0107 鏡像的一法一檔版本。
---

# 全國法規資料庫 law.moj.gov.tw

取得**法條原文**。要做合約審查或法律風險分析，用 `taiwan-claude-legal`
plugin 的 `/audit`；這個 skill 是它的資料層，負責把正確的條文抓出來。

## 兩個來源，各有取捨（已實測）

| | 官方 API | kong0107 鏡像 |
| --- | --- | --- |
| 位置 | `law.moj.gov.tw/api` | `github.com/kong0107/mojLawSplitJSON` |
| 更新 | 每日（實測資料日 2026-08-21） | 每週（實測 2026-08-14） |
| 形式 | 整包 ZIP，1,346 部法律擠一個 25 MB JSON | 一法一檔，11,792 個中文檔 |
| 編章節 | 只有夾在條文陣列裡的文字列 | `divisions` 結構化樹狀 |
| 適合 | 要最新、要全庫掃描 | 要查單一條文、要章節結構 |

**新鮮度會變**，動手前先跑 `freshness` 確認，不要憑印象。

## 版本審核結論（kong0107 那三個 repo）

- **`mojLawSplitJSON`** ← **就用這個**。最新 tag `20260814_arrange`，688 個 tag，仍在更新。
- `mojLawSplitXML`：最新 tag `20260807`，只有 274 個 tag，切自**舊版 XML**，落後。
- `mojLawSplit`：只有程式碼，沒有資料，最後的 tag 停在 2022。要自己重跑轉檔才用。

`mojLawSplitJSON` 的分支：`arranged`（重整版，有 `divisions`，**預設用這個**）、
`split`（純切版，貼近官方原始欄位）、`gh-pages`（網頁）。

## 用法

```bash
# 個人安裝（所有專案都能用）
M=~/.claude/skills/moj-law/scripts/mojlaw.py
# 專案安裝
# M=.claude/skills/moj-law/scripts/mojlaw.py

python3 $M article B0000001 184     # 民法第184條（侵權行為）
python3 $M article B0000001 15-1    # 「之N」條號寫 15-1
python3 $M law B0000001             # 概要 + 編章節樹
python3 $M grep J0070017 攝影        # 在著作權法裡搜關鍵字
python3 $M bulk --kind law           # 下載官方整包（快取到 ~/.cache/moj-law）
python3 $M find 勞動基準             # 用法規名稱找 pcode（需先跑 bulk）
python3 $M freshness                 # 比對官方與鏡像的資料日期
python3 $M --lang en article B0000001 184   # 英譯版
```

常用 pcode：民法 `B0000001`、公司法 `J0080001`、勞動基準法 `N0030001`、
著作權法 `J0070017`、個人資料保護法 `I0050021`。忘了就用 `find`。

## 條號編碼（鏡像版的關鍵細節）

`articles[].number` 是**條次 × 100 + 之N**，不是條次本身：

| 條文 | number |
| --- | --- |
| 第 1 條 | 100 |
| 第 15 條 | 1500 |
| 第 15 條之1 | 1501 |
| 第 164 條之1 | 16401 |

`divisions` 的 `start`／`end` 用同一套編碼。直接拿 `number` 當條次會全錯。

## 已知的坑

**1. 法規資料庫沒有「所有」法規。** 許多行政規則、自治條例、自治規則不在裡面。
查不到不代表沒這條法，可能只是不在這個庫。

**2. 官方 API 的 `UpdateDate` 和 ZIP 打包日不一樣。** 實測差了 7 天
（資料日 2026-08-21，打包日 2026-08-28）。要判斷新鮮度看 `UpdateDate`，
不要看檔案時間——`freshness` 兩個都會印。

**3. 英譯版的更新日期跟中文版不同步。** 引用英譯條文前先確認中文版有沒有後續修正。

**4. 2018 年以前的「歷史法規」只有行政命令層級。** 法律層級的歷史沿革要另外
從立法院抓，這裡沒有。

**5. 官方新版 API 的鍵名把 `attachment` 拼成 `attachement`。** 不是筆誤，照著寫。

**6. 舊版法規（多數已廢止）用換行排版**，解析時空白處理要小心。

## 引用法條的原則

回答法律問題時，把條號和原文一起附上，讓使用者能自己回去核對。
這個 skill 只提供條文原文，不是法律意見；真的要簽約或訴訟還是要找律師。
