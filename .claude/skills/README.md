# 已安裝的 Claude Code Skills

這個資料夾裡的 skill 會在「這個 repo 的任何 Claude Code session」自動載入
（Claude Code 會讀取專案根目錄的 `.claude/skills/`）。

## 清單

| Skill | 用途 | 來源 |
| --- | --- | --- |
| `animation-reference` | 說不出名字的網頁／UI 動效，幫你找到它的正式名稱、參考站、可實作的 motion spec；也能檢視現有專案並建議該加什麼動畫 | [CHENG-LIANG1/awesome-animations](https://github.com/CHENG-LIANG1/awesome-animations) |
| `humanizer-zh-tw` | 繁體中文「去 AI 味」：改掉浮誇象徵、宣傳語氣、破折號濫用、三段式法則、AI 慣用詞等痕跡 | [kevintsai1202/Humanizer-zh-TW](https://github.com/kevintsai1202/Humanizer-zh-TW) |
| `text-watermark-cleaner-zh-tw` | 檢查／清除文字裡的隱形 Unicode：zero-width、tag characters、異形空白、文字型 AI provenance 標記 | 同上（該 repo 的附屬 skill） |

## 怎麼用

在對話裡直接叫它，或用 `/skill` 名稱：

```text
/animation-reference 我想讓產品卡片展開成全螢幕詳情頁，但不知道這個動畫叫什麼。

/humanizer-zh-tw 幫我把 劇本/紅衣/大綱.md 的語氣改得自然一點。

/text-watermark-cleaner-zh-tw 先檢查 article.md 有沒有隱形字元，先不要改內容。
```

多數情況你不用指名，描述需求時 Claude 會自己挑對的 skill。

## 兩個 humanizer skill 的分工

- **語氣不自然** → `humanizer-zh-tw`
- **要清隱形字元／浮水印** → `text-watermark-cleaner-zh-tw`

不要混用。`text-watermark-cleaner-zh-tw` 只做「可驗證的文字載體清理」，
不會宣稱內容已被證明為人類撰寫，也不處理圖片浮水印或檔案 C2PA/EXIF metadata。

### 附帶的 Python 腳本（已在 Linux + Python 3.11 實測可用）

```bash
# 只檢查，不改內容
python3 .claude/skills/text-watermark-cleaner-zh-tw/scripts/inspect_text.py article.md

# 清理，輸出到新檔（原檔保留）
python3 .claude/skills/text-watermark-cleaner-zh-tw/scripts/clean_text.py \
  article.md -o article.cleaned.md --stats
```

Windows PowerShell 使用者也可以走 skill 附的入口腳本：

```powershell
& .\.claude\skills\text-watermark-cleaner-zh-tw\scripts\run-text-watermark.ps1 `
  -Mode Inspect -InputPath .\article.md -Json
```

## 想改成全域安裝（所有專案都能用）

**macOS / Linux**

```bash
cp -R .claude/skills/animation-reference            ~/.claude/skills/
cp -R .claude/skills/humanizer-zh-tw                ~/.claude/skills/
cp -R .claude/skills/text-watermark-cleaner-zh-tw   ~/.claude/skills/
```

**Windows PowerShell**

```powershell
Copy-Item -Recurse .\.claude\skills\animation-reference          "$env:USERPROFILE\.claude\skills\"
Copy-Item -Recurse .\.claude\skills\humanizer-zh-tw              "$env:USERPROFILE\.claude\skills\"
Copy-Item -Recurse .\.claude\skills\text-watermark-cleaner-zh-tw "$env:USERPROFILE\.claude\skills\"
```

或用官方安裝器（會自動偵測你裝了哪些 AI agent）：

```bash
npx skills add kevintsai1202/Humanizer-zh-TW -a claude-code -g -y
```

`animation-reference` 上游是寫給 Codex 的（`~/.codex/skills/`），
但 SKILL.md 的格式與 Claude Code 相容，直接複製即可。

## 更新

三個 skill 都是直接從上游 repo 複製過來的，沒有改動內容。要更新就重新複製一次。
