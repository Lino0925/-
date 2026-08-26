# 已安裝的 Claude Code Skills

這個資料夾裡的 skill 會在「這個 repo 的任何 Claude Code session」自動載入
（Claude Code 會讀取專案根目錄的 `.claude/skills/`）。全部都是從上游 repo 直接複製，內容未改動。

---

## 一、寫作 / 文字

| 資料夾 | skill 名稱 | 用途 | 來源 |
| --- | --- | --- | --- |
| `humanizer-zh-tw` | `humanizer-zh-tw` | 繁體中文去 AI 味 | [kevintsai1202/Humanizer-zh-TW](https://github.com/kevintsai1202/Humanizer-zh-TW) |
| `text-watermark-cleaner-zh-tw` | `text-watermark-cleaner-zh-tw` | 檢查／清除隱形 Unicode、zero-width、AI provenance 標記 | 同上（附屬 skill） |
| `stop-slop` | `stop-slop` | 英文版去 AI 味：8 類 AI 寫作痕跡（禁用詞、陳腔濫調、被動語態、破折號、空泛斷言） | [hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop) |
| `output-skill` | `full-output-enforcement` | 逼 agent 輸出完整內容，不要偷懶省略 | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) |

`humanizer-zh-tw` 管繁中、`stop-slop` 管英文，兩個不衝突。
要清隱形字元一律用 `text-watermark-cleaner-zh-tw`，不要跟去 AI 味混用。

## 二、前端 / 設計

| 資料夾 | skill 名稱 | 用途 | 來源 |
| --- | --- | --- | --- |
| `taste-skill` | `design-taste-frontend` | 反 AI 味前端主 skill：landing page、作品集、改版 | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) |
| `minimalist-skill` | `minimalist-ui` | 極簡風變體 | 同上 |
| `brutalist-skill` | `industrial-brutalist-ui` | 工業／粗獷風變體 | 同上 |
| `soft-skill` | `high-end-visual-design` | 高級感 soft-ui 變體 | 同上 |
| `redesign-skill` | `redesign-existing-projects` | 既有專案改版，先 audit 再動手 | 同上 |
| `image-to-code-skill` | `image-to-code` | 設計圖轉程式碼 | 同上 |
| `unslop-ui` | `unslop-ui` | 拆掉「一看就 AI 做的」網站特徵：預設 shadcn/Tailwind、紫色漸層、emoji 當 icon、置中 hero + 三張卡片。基於 47 個 subreddit、320 萬則貼文的分析 | [JCarterJohnson/vibecoded-design-tells](https://github.com/JCarterJohnson/vibecoded-design-tells) |
| `animation-reference` | `animation-reference` | 說不出名字的網頁／UI 動效 → 正式名稱、參考站、可實作的 motion spec | [CHENG-LIANG1/awesome-animations](https://github.com/CHENG-LIANG1/awesome-animations) |

`taste-skill` 上游還有 `brandkit`、`stitch-skill`、`imagegen-frontend-web/mobile`、`gpt-tasteskill`、
`taste-skill-v1` 等變體沒裝（重複或非 Claude Code 取向）。要補裝就從上游 repo 的 `skills/` 複製對應資料夾進來。

## 三、工程 / 研究

| 資料夾 | skill 名稱 | 用途 | 來源 |
| --- | --- | --- | --- |
| `improve` | `improve` | 掃整個 codebase，產出可交給便宜模型執行的改進計畫。**對原始碼唯讀，自己不動手改** | [shadcn/improve](https://github.com/shadcn/improve) |
| `loopy` | `loopy` | 把一次性 prompt 變成會自我改進的重複流程；能找出重複性工作、比對已發布的 loop、稽核與修補 | [Forward-Future/loop-library](https://github.com/Forward-Future/loop-library) |
| `last30days` | `last30days` | 掃 Reddit、X、YouTube、TikTok、HN、Polymarket、GitHub 近 30 天討論，依真實互動量排序成一份簡報 | [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) |
| `watch` | `watch` | 讓 Claude「看」影片：yt-dlp 下載、ffmpeg 抽格、抓帶時間軸的逐字稿 | [bradautomates/claude-video](https://github.com/bradautomates/claude-video) |
| `book-to-skill` | `book-to-skill` | 把書或文件（PDF / EPUB / DOCX / HTML / MD / RTF / MOBI）轉成結構化的 agent skill — 抽出框架、心智模型、原則、技法、反模式，不是做摘要 | [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill) |

### book-to-skill 的兩件事

**一、只用官方 repo。** 上游有一份 [安全公告](https://github.com/virgiliojr94/book-to-skill/blob/master/SECURITY-NOTICE.md)：
`Leutenegger/book-to-skill` 是惡意的再上傳版本，會關掉 TLS 驗證、把主機與 repo 資訊送到外部
Cloudflare Worker、列舉本機加密貨幣錢包與 Ledger 的瀏覽器擴充套件資料並上傳，
在 Windows 上還會解壓執行夾帶的 EXE。這裡裝的是官方的 `virgiliojr94/book-to-skill`
（commit `8a2cae6`，2026-08-26），已對照公告描述的行為掃過，無命中。

**二、它會自己裝 Python 套件。** 轉檔要用的 parser（pypdf、ebooklib 等）是按需安裝的，
`--install-missing ask|yes|no` 可以控制。先跑 `--check` 看目前有哪些：

```bash
python3 .claude/skills/book-to-skill/scripts/extract.py --check
```

MOBI/AZW 要另外裝 [Calibre](https://calibre-ebook.com)。用法：

```text
/book-to-skill ~/path/to/your-book.pdf
```

### 這兩個要額外裝東西才能跑

**`watch`** 需要 `ffmpeg`、`ffprobe`、`yt-dlp`：

```bash
# macOS
brew install ffmpeg yt-dlp
# Windows
winget install Gyan.FFmpeg && winget install yt-dlp.yt-dlp
# Linux
sudo apt install ffmpeg && pipx install yt-dlp
```

影片沒有內建字幕時要走 Whisper，需要 `GROQ_API_KEY`（較便宜）或 `OPENAI_API_KEY`，
寫進 `~/.config/watch/.env`。不想設就加 `--no-whisper`，只拿畫面不拿逐字稿。

**`last30days`** 的資料源多半要 API key（`SCRAPECREATORS_API_KEY`、`BRAVE_API_KEY`、
`EXA_API_KEY`、`PERPLEXITY_API_KEY` 等，看你要開哪些來源）。
skill 內附 `doctor` 健檢指令，可以先跑它看哪些源沒設好。
上游的 14 MB demo 素材（範例圖片與 mp3）沒有複製進來，不影響功能。

---

## 沒辦法裝進這裡的三個

那份 Top 10 清單裡有三個不是 Claude Code skill，得各自安裝：

| 項目 | 為什麼 | 怎麼裝 |
| --- | --- | --- |
| **GOG (Workspace CLI)** #6 | OpenClaw 專用，不是 skill 格式 | `openclaw skills install @steipete/gog`（要先有 OpenClaw） |
| **Security Unbroker** #3 | Hermes-native，跑在 [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) 上 | `hermes skills install official/security/unbroker`（要先有 Hermes） |
| **Shannon Pentester** #4 | 是一整套獨立應用（pnpm monorepo + Temporal worker + 瀏覽器自動化），不是 skill | `npx @keygraph/shannon setup`，見 [KeygraphHQ/shannon](https://github.com/KeygraphHQ/shannon) |

Shannon 會對執行中的目標站真的打 exploit，**只能對自己擁有或已獲授權的系統跑**。
它另外需要 LLM API key 和一個跑起來的目標應用，所以沒有放進這個 repo。

---

## 怎麼用

在對話裡描述需求，Claude 通常會自己挑對的 skill；要指定就打斜線：

```text
/improve 掃一下這個 repo，給我前五個最值得動的改進點。
/last30days AI 影片工具
/watch https://www.youtube.com/watch?v=xxxx 這支影片在講什麼？
/humanizer-zh-tw 幫我把 劇本/紅衣/大綱.md 的語氣改自然一點。
/text-watermark-cleaner-zh-tw 先檢查 article.md 有沒有隱形字元，先不要改內容。
/animation-reference 我想讓產品卡片展開成全螢幕詳情頁，但不知道這動畫叫什麼。
```

### text-watermark-cleaner 附帶的腳本（已在 Python 3.11 實測）

```bash
python3 .claude/skills/text-watermark-cleaner-zh-tw/scripts/inspect_text.py article.md
python3 .claude/skills/text-watermark-cleaner-zh-tw/scripts/clean_text.py \
  article.md -o article.cleaned.md --stats
```

---

## 想改成全域安裝（所有專案都能用）

**macOS / Linux**

```bash
cp -R .claude/skills/*/ ~/.claude/skills/
```

**Windows PowerShell**

```powershell
Get-ChildItem .\.claude\skills -Directory |
  ForEach-Object { Copy-Item -Recurse $_.FullName "$env:USERPROFILE\.claude\skills\" }
```

## 更新

全部是直接複製上游的，要更新就重抓一次對應 repo 再蓋掉。
