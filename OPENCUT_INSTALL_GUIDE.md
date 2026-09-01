# OpenCut 安裝指南

OpenCut 是開源的影片剪輯器（CapCut 的替代品），檔案留在自己電腦上、功能不上鎖。

> **原始碼已經放進這個 repo 的 [`opencut/`](opencut/) 資料夾了**，你 `git pull` 之後
> 只要跑 `bun install` 就能用，不用再 clone。詳見下面「已經裝好的部分」。

## 先搞清楚要裝哪一個 repo

你給的連結是 `OpenCut-app/OpenCut` — **那個 repo 正在整個重寫，現在裝不出可用的東西**，
官方 README 自己也寫了：目前該用的是 classic 版本，`opencut.app` 線上跑的也是 classic。

| Repo | 狀態 | 該不該裝 |
| --- | --- | --- |
| [opencut-app/opencut-classic](https://github.com/opencut-app/opencut-classic) | 已封存但可正常執行，功能完整 | ✅ **裝這個** |
| [opencut-app/opencut](https://github.com/opencut-app/opencut) | 重寫中，不接受外部貢獻，尚無可用版本 | ❌ 想追進度再看 |

另外，如果你只是想「用」而不是「改」，最快的方式是直接開 <https://opencut.app> — 不用裝任何東西，
影片一樣是在瀏覽器本機處理。以下步驟是給你要在自己電腦跑一份的情況。

---

## 需求

- [Bun](https://bun.sh/docs/installation)（必要）
- [Docker Desktop](https://docs.docker.com/get-docker/)（選用；只跑前端可以不裝，
  但沒有它就沒有本機資料庫與 Redis，登入／專案雲端同步那類功能會不能用）

安裝 Bun：

```powershell
# Windows PowerShell
powershell -c "irm bun.sh/install.ps1 | iex"
```

```bash
# macOS / Linux
curl -fsSL https://bun.sh/install | bash
```

裝完關掉終端機再開一次，確認 `bun -v` 有反應。

---

## 安裝步驟

以下步驟在 Linux + Bun 1.3.11 + Node 22 實測過，`bun install` 裝完 1951 個套件，
`bun dev:web` 起得來，`http://localhost:3000` 回 200。

**第 1 步已經幫你做完了** — 原始碼就在 `opencut/`，直接 `cd opencut` 從第 2 步開始。
（想自己另外抓一份的話第 1 步指令也一併留著。）

```bash
# 1. 取得原始碼（已完成，opencut/ 就是這個）
# git clone https://github.com/opencut-app/opencut-classic.git opencut
cd opencut

# 2. 建立環境設定檔（.env.example 的預設值就對得上 docker compose，不用改）
cp apps/web/.env.example apps/web/.env.local

# 3.（選用）啟動本機資料庫與 Redis — 沒裝 Docker 就跳過這步
docker compose up -d db redis serverless-redis-http

# 4. 安裝套件並啟動
bun install
bun dev:web
```

Windows PowerShell 的第 2 步改成：

```powershell
Copy-Item apps/web/.env.example apps/web/.env.local
```

跑起來後開 <http://localhost:3000>。

---

## 另一種：整包用 Docker 跑

不想碰 Bun、只想要一個能用的服務，在 `opencut/` 資料夾裡執行：

```bash
docker compose up -d
```

開 <http://localhost:3100>（注意是 3100，不是 3000）。這個模式跑的是 production build，
改程式不會即時反應，適合單純拿來用。

---

## 常見狀況

**`bun dev:web` 出現 `Failed to download Inter from Google Fonts`**
連不到 Google Fonts 而已，會自動退回系統字型，不影響功能。網路正常的機器不會遇到。

**沒裝 Docker 就啟動，登入或專案儲存出錯**
預期行為。純剪輯（匯入影片、時間軸、匯出）不需要資料庫；要完整功能就把第 3 步的 Docker 補上。

**想改 `rust/wasm` 底層**
需要另外裝 Rust toolchain、`wasm-pack`、`cargo-watch`，步驟在 classic repo 的
「Local WASM development」那節。一般使用不需要。

**桌面版 `apps/desktop`**
用 GPUI 寫的原生桌面版還在開發中，是 opt-in 的，只想用網頁版就完全不用理它。

---

## 已經裝好的部分

`opencut/` 是 [opencut-app/opencut-classic](https://github.com/opencut-app/opencut-classic)
在 commit `cf5e79e`（2026-05-17）的完整原始碼，1128 個檔案、12 MB，
只含 git 追蹤的檔案（沒有 node_modules、沒有 build 產物、沒有上游的 .git）。

在這次的雲端容器裡實跑驗證過：

- `bun install` → 1951 個套件裝完，exit 0
- `bun dev:web` → `✓ Ready in 1254ms`，`localhost:3000/` 與 `/projects` 都回 200

容器裡那份 `node_modules`（2.2 GB）不會進 git — `opencut/.gitignore` 已經擋掉了，
`apps/web/.env.local` 也一樣。所以你拉下來之後要自己跑一次 `bun install`。

### 你要用的時候

```bash
cd opencut
cp apps/web/.env.example apps/web/.env.local   # Windows: Copy-Item apps/web/.env.example apps/web/.env.local
bun install
bun dev:web
```

開 <http://localhost:3000>。

### 想更新到上游最新版

`opencut/` 是直接複製進來的（不是 submodule），要更新就重新抓一次：

```bash
git clone --depth 1 https://github.com/opencut-app/opencut-classic.git /tmp/oc
rm -rf opencut && mkdir opencut
git -C /tmp/oc archive --format=tar HEAD | tar -x -C opencut
```

不過 classic 已經封存、不再維護，上游大概不會再動了。
