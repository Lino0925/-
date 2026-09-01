# OpenStory 安裝指南

把劇本直接變成連貫的分鏡影片。丟一份劇本進去，它自動拆場次、排鏡頭，
輸出同一種風格的圖片／影片／音訊片段，跨鏡頭維持角色、場景、光位的一致性。

> **原始碼已經放進這個 repo 的 [`openstory/`](openstory/) 資料夾了**，
> `git pull` 之後跑 `bun install && bun dev` 就能開。

來源：[openstory-so/openstory](https://github.com/openstory-so/openstory)，
commit `776cf85`（2026-08-26），1771 個檔案、32 MB，只含 git 追蹤的檔案。

---

## 需求

**只需要 [Bun](https://bun.com/docs/installation) >= 1.3.0。**
不用 Docker、不用外部資料庫、不用 Cloudflare 帳號 — 本機開發時整套（D1 資料庫、
R2 儲存、Workflows、Durable Objects、寄信）都跑在 Miniflare 裡。

```powershell
# Windows PowerShell
powershell -c "irm bun.sh/install.ps1 | iex"
```

```bash
# macOS / Linux
curl -fsSL https://bun.sh/install | bash
```

---

## 啟動

```bash
cd openstory
bun install --ignore-scripts
bun dev
```

開 <http://localhost:3000>。

**`--ignore-scripts` 這個參數不要拿掉**，原因見下面〈lefthook 會污染外層 repo〉。

`bun dev` 會一次做完：產生 `.env.local`（含 auth 與加密金鑰）、跑資料庫 migration、
灌入種子資料、啟動 dev server。第一次啟動大約 30 秒。

實測（Bun 1.3.11 / Linux）：`bun install --ignore-scripts` 1129 個套件 exit 0，
`bun dev` 完成 migration 與 seed、`ready in 31224 ms`、`localhost:3000` 回 200。

---

## 要用 AI 生成功能就得補兩把 key

```bash
bun setup      # 互動式填入，或直接編輯 .env.local
```

| Key | 用途 | 去哪拿 |
| --- | --- | --- |
| `FAL_KEY` | 圖片、影片、音訊生成 | [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys) |
| `OPENROUTER_KEY` | LLM 劇本分析、自動拆場次 | [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) |

沒填這兩把也能啟動、能點介面，但生不出東西。
其他選用設定（Google OAuth、Stripe、PostHog、遠端 R2）看 `openstory/.env.example`。

**`.env.local` 不會進版控** — `openstory/.gitignore` 已經擋掉 `.env*`。
你自己的 key 只留在你機器上。

---

## lefthook 會污染外層 repo

`openstory/` 是複製進這個 repo 的，它自己沒有 `.git`。
OpenStory 用 [lefthook](https://lefthook.dev) 管 git hooks，而 lefthook 的 postinstall
會呼叫 `git rev-parse --show-toplevel` 找 git 根目錄 —— 找到的是**這個 repo 的根目錄**，
不是 `openstory/`。結果是直接跑 `bun install` 會：

1. 在 repo 根目錄生一個全部註解掉的範例 `lefthook.yml`
2. 在 `.git/hooks/` 裝一個 `prepare-commit-msg`，指向 `openstory/node_modules/` 裡的 lefthook

兩個都不是你要的東西。**用 `bun install --ignore-scripts` 就不會發生**，
已實測：加了參數之後根目錄乾淨，`bun dev` 照常跑到 `localhost:3000` 回 200
（被跳過的只有 lefthook 的 git hook 安裝，那是 OpenStory 自己開發用的，你不需要）。

`LEFTHOOK=0` **擋不住**（實測過，環境變數只讓 hook 執行時跳過，不會阻止安裝）。

已經不小心跑過沒加參數的 `bun install`？清掉就好：

```bash
rm -f lefthook.yml .git/hooks/prepare-commit-msg
```

如果你比較想避開整件事，就別用 repo 裡這份，改在別的地方獨立 clone 一份 —
那樣 `openstory/` 自己有 `.git`，lefthook 就只會裝進它自己裡面：

```bash
git clone https://github.com/openstory-so/openstory.git ~/openstory
cd ~/openstory && bun install && bun dev
```

---

## 常用指令

| 指令 | 說明 |
| --- | --- |
| `bun dev` | 建環境 + migrate + seed + 啟動 |
| `bun setup` | 互動式填 AI key（`--prod` 用於部署） |
| `bun storybook` | 開 Storybook（port 6006） |
| `bun run build` | production build（注意不是 `bun build`） |
| `bun db:studio:local` | 用 Drizzle Studio 看本機資料庫 |
| `bun run test` | Vitest 單元測試 |
| `bun test:e2e` | Playwright end-to-end |

---

## 跟你現有的東西怎麼搭

repo 裡的 `劇本/` 已經有《紅衣》等分集大綱與導演聖經。
OpenStory 吃的是劇本文字，所以那些內容可以直接丟進去拆場次、出分鏡。

它跟你帳號層級那幾個 skill（`cinematic-video-production`、`seedance-director`、
`ltx-video-studio`、`lira-image-prompts`）是互補的：那些負責把劇本編譯成各家生成器的
提示詞，OpenStory 則負責把整份劇本排成連貫的鏡頭序列並實際生成。

---

## 部署到 Cloudflare（選用）

repo README 有一鍵 Deploy to Cloudflare 按鈕，會 clone 並自動開好 Workers、D1、R2。
本機跑不需要 Cloudflare 帳號。

---

## 想更新到上游最新版

`openstory/` 是直接複製進來的（不是 submodule），要更新就重抓：

```bash
git clone --depth 1 https://github.com/openstory-so/openstory.git /tmp/os
rm -rf openstory && mkdir openstory
git -C /tmp/os archive --format=tar HEAD | tar -x -C openstory
cd openstory && bun install --ignore-scripts
```

注意這會蓋掉整個資料夾，先確認 `.env.local` 有備份（它不在版控裡）。
