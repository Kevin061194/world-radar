# WORLD RADAR 個人全球國際情報中心

每天台灣時間 07:30，自動蒐集全球新聞 → 篩選十大 → AI 用繁體中文分析 → 更新網站 → 推播 Telegram。
全部跑在 GitHub 的雲端機器上，**你的電腦關機也會照常執行**。

## 誠實說明（請先看）
- 只用 Python 標準庫，不需安裝任何套件。
- 新聞來源是 RSS 與 GDELT 的**標題與摘要**，不是全文。AI 只能根據這些內容分析，所以分析深度有限，且每則都附原文連結供你查證。
- Reuters、AP 沒有官方 RSS，改用 Google News 的站內搜尋 RSS，連結會先經過 Google 轉址。
- 各媒體的 RSS 網址可能改版失效。失效時系統會記錄並跳過，不會停止；失效的來源會顯示在「設定」頁。
- 「重要性分數」由程式依來源數量、可信度、關鍵字計算，AI 負責解釋，不負責打分。
- 世界地圖是以國家首都座標標點的格線圖，沒有海岸線底圖。
- 「立即更新」「重新整理」按鈕在 Telegram 裡是網址按鈕（開啟 GitHub Actions 頁面／網站），因為純排程架構沒有常駐機器人可以接收指令。

## 費用
| 項目 | 費用 |
|---|---|
| GitHub 帳號、公開倉庫、Actions、Pages | 免費（公開倉庫的 Actions 不限分鐘） |
| Telegram Bot | 免費 |
| RSS、GDELT | 免費 |
| Gemini API | 有免費額度（有每分鐘/每日上限，請以 Google AI Studio 當下說明為準） |
| OpenAI 或其他相容 API | 付費，依用量計費 |
| Claude Code 訂閱 | **不包含** Claude API 額度，本專案沒有使用 |

每天約 11 次 AI 呼叫（10 則新聞各 1 次 + 1 次總覽）。

## 設定步驟（約 20 分鐘，一步一步做）

### 步驟 1：把專案放上 GitHub
1. 登入 https://github.com ，右上角「+」→「New repository」。
2. Repository name 隨意（例如 world-radar），選 **Public**，按「Create repository」。
3. 在新頁面點「uploading an existing file」，把本資料夾**全部內容**（含隱藏的 `.github` 資料夾）拖進去，按「Commit changes」。
   - 若 `.github` 資料夾上傳不了，改用 git 指令：`git init && git add . && git commit -m init && git remote add origin <你的倉庫網址> && git push -u origin main`

### 步驟 2：取得 AI API Key（以 Gemini 為例）
1. 開啟 https://aistudio.google.com/apikey ，登入 Google 帳號。
2. 按「Create API key」，複製那一串字。

### 步驟 3：建立 Telegram 機器人
1. 在 Telegram 搜尋 **@BotFather**，傳送 `/newbot`，依指示取名。
2. 它會給你一串 Token（長得像 `123456:ABC...`），複製起來。
3. 在 Telegram 搜尋你剛建立的機器人，按「Start」，隨便傳一句話給它。
4. 在瀏覽器開啟 `https://api.telegram.org/bot你的Token/getUpdates`（把「你的Token」換掉），找到 `"chat":{"id":` 後面的數字，那就是 Chat ID。

### 步驟 4：把金鑰放進 GitHub Secrets（不會公開）
倉庫頁面 → 上方「Settings」→ 左側「Secrets and variables」→「Actions」→「New repository secret」。依序新增三個：
- Name：`AI_API_KEY`　Secret：步驟 2 的 Key
- Name：`TELEGRAM_BOT_TOKEN`　Secret：步驟 3 的 Token
- Name：`TELEGRAM_CHAT_ID`　Secret：步驟 3 的數字

### 步驟 5：設定網址（Variables，同一頁的「Variables」分頁）
按「New repository variable」新增：
- `SITE_URL`：`https://你的GitHub帳號.github.io/倉庫名/`
- `ACTIONS_URL`：`https://github.com/你的GitHub帳號/倉庫名/actions/workflows/daily.yml`
（若用 OpenAI：再新增 `AI_PROVIDER`=`openai`、`AI_MODEL`=`gpt-4o-mini`。其他相容服務再加 `AI_BASE_URL`。）

### 步驟 6：開啟網站（GitHub Pages）
Settings → 左側「Pages」→ Source 選「Deploy from a branch」→ Branch 選 `main`、資料夾選 `/docs` → Save。幾分鐘後網址就是 SITE_URL。

### 步驟 7：第一次手動執行
倉庫上方「Actions」→ 左側「WORLD RADAR daily」→ 右側「Run workflow」→ 綠色按鈕。約 2～5 分鐘後，Telegram 會收到簡報，網站出現資料。之後每天 07:30 自動執行（GitHub 排程可能延遲數分鐘到數十分鐘）。

## 在自己電腦上測試（可選）
1. 複製 `.env.example` 為 `.env`，填入金鑰。
2. 測試：`python -m unittest discover -s tests -v`
3. 執行：`python -m worldradar.run`（加 `--no-ai`、`--no-telegram` 可略過）
4. Telegram 測試：`python -m worldradar.telegram chatid`（查 Chat ID）、`python -m worldradar.telegram test`（送測試訊息）
5. 看網站：`python -m http.server 8000 -d docs`，瀏覽器開 http://localhost:8000

## 專案結構
- `worldradar/collect.py` RSS／GDELT 蒐集　`process.py` 去重、合併、評分、選十大
- `worldradar/ai.py` 可替換 AI Provider（gemini / openai 相容）與一致性檢查
- `worldradar/telegram.py` 長訊息分段推播　`report.py` 簡報格式　`db.py` SQLite
- `worldradar/run.py` 每日 11 個步驟主流程
- `docs/` 網站（PWA）與每日資料　`data/worldradar.db` 歷史資料庫　`data/logs/` 執行日誌
- `tests/` 離線測試（內含的假新聞只存在於測試，不會進入正式資料）

## 可靠性機制
單一來源失敗自動跳過；網路自動重試 3 次；24 小時時效與網址去重；同事件合併；來源 URL 有效性檢查；單一來源事件標示「尚未交叉驗證」；AI 摘要中的數字若未出現在來源會被標記；十大不足 10 則時如實說明；AI 或 Telegram 失敗不會讓網站資料遺失；每次執行寫入 `runs` 資料表與日誌檔。
