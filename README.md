# work-helper

工作用的 agent 能力：指令放 `bin/`，自己寫的 skill 放 `skills/`。
**離職就用不到的東西放這裡** —— 跨工作還要用的環境設定在 `dotfiles`，純文件在 `work-docs`。

```
bin/slack-list          讀寫「Bug/需求總表」，並把處理進度回報到 Slack
bin/sync-skills         把 skills/ 全部拉線到 agent 讀得到的位置（新增 skill 後跑一次）
skills/slack-todo/      ↑ 的 skill：讓 agent 知道有這個東西、什麼時候用
skills/daily-worklog/   從 git commit 產工作日誌（產出寫進 work-docs）
skills/fleet-recon/     平行查一批待辦的現況、每件寫成一份草稿（fleet 第一波）
skills/fleet-worktree/  一份草稿或一個 issue 開成隔離 worktree + 派長駐 agent（fleet 第二波）
drafts/                 偵察的草稿（消耗品，gitignore，看完就派工或開 issue 然後刪）
docs/fleet-flow.md      fleet 的架構與規則：誰是誰、誰跟誰交接、你在哪介入
docs/fleet-dry-run-checklist.md  跑一輪 fleet 的打勾表（消耗品，跑完清空）
docs/adr/               架構決定與當初的理由（含 fleet 的七個），改之前先讀
CONTEXT.md              這條線上會混淆的詞（待辦列、任務、草稿、指紋…）
```

## 裝成 skill

```bash
bin/sync-skills
```

它把 `skills/` 底下每個有 `SKILL.md` 的資料夾拉線到**兩個地方** ——
`~/.agents/skills/`（工具中立層，opencode 讀這裡）和 `~/.claude/skills/`（Claude Code 讀這裡），
順便清掉指向這個 repo、但來源已經刪掉的死連結。可以重複跑。

**新增或改名 skill 之後要再跑一次** —— 拉線是一次性的，`git pull` 只更新內容，
不會替新資料夾建連結。

`~/.agents/skills/` 是跨工具的共用位置（`npx skills` 裝的東西也在那）。
opencode 官方文件列的搜尋路徑包含 `~/.agents/skills/*/SKILL.md`、
`~/.claude/skills/*/SKILL.md` 和 `~/.config/opencode/skills/*/SKILL.md`，
所以兩邊都拉最保險 —— 不用去賭它跟不跟隨 symlink。

## 需要什麼

- Python 3（標準函式庫就夠，不用裝套件）
- 一個 Slack app。只讀的話 `lists:read` 就夠；要回報進度還需要
  `lists:write`、`chat:write`、`files:write`，私人 channel 再加 `groups:read` + `groups:history`
- 那張 List 要分享給這個 app，不然會回 `not_found`

## 設定

```bash
cp .env.example .env
# 填 SLACK_BOT_TOKEN、SLACK_LIST_ID、SLACK_MY_USER_ID
# 沒有 GitHub credential 的 backlog agent 再設 WORK_HELPER_ISSUE_MODE=manual
```

`.env` 在 `.gitignore` 裡，不會被 commit。

`SLACK_LIST_ID` 從那張表的網址列取。

`SLACK_MY_USER_ID` 是你自己的 Slack 成員 ID（`U` 開頭），`mine` 指令要用。
Slack 點自己頭像 → 個人檔案 → 右上「⋮」→ 複製成員 ID。
**不能靠 API 問出來** —— `xoxb-` token 打 `auth.test` 回的是 bot 自己的 ID，
要解別人的 ID 或用 email 反查都需要 `users:read`，這個 app 沒有那個 scope。

## 用

```bash
bin/slack-list env      # 先確認設定讀到了（token 會遮起來）
bin/slack-list count    # 通不通，看這個最快
bin/slack-list fields   # 這張表有哪些欄位、各是什麼型別
bin/slack-list todo     # 一行一列，人看的
bin/slack-list mine     # 只印指派給我的列
bin/slack-list mine 庫存 # 指派給我、而且整列文字含「庫存」的
bin/slack-list assigned U0B… 庫存 # 共享 agent：指派給當次 Slack sender 的列
bin/slack-list json     # 壓平後的 JSON，給程式吃
bin/slack-list raw      # Slack 原始回應，不加工
bin/slack-list sample   # 只印第一列的原始結構

# OpenAB sender context → 待辦列 + 完整留言 JSON
bin/slack-list context --channel C0B9… --thread-ts 1234567890.123456
```

`todo` 是預設，`bin/slack-list` 不帶參數就是它。

`mine` 給沒有 Slack message context 的 local agent使用，以 `.env` 的
`SLACK_MY_USER_ID` 解釋「我」。OpenAB收到 Slack訊息時已知道當次 `sender_id`，要用
`assigned <sender_id>`；不要把共享環境裡的固定 ID當成目前說話的人。

## 建立待辦與設定回報

`add` 一次寫入名稱、指派對象及選填的敘述／到期日。同名未完成列已存在時不建第二列，
而是把 assignee 追加到既有列，並在原生 item 留言串留下再次回報的來源。

```bash
bin/slack-list add \
  --title "庫存匯出缺少批號" \
  --description "匯出的 Excel 沒有批號欄" \
  --due 2026-08-21 \
  --assignee U0B… \
  --requested-by U0B… \
  --source-channel C0B… \
  --source-thread 1234567890.123456

# 明確改成回報給另一個人，或取消／恢復預設
bin/slack-list reporter Rec0B… --user U0B…
bin/slack-list reporter Rec0B… --none
bin/slack-list reporter Rec0B… --default
```

`add` 是 single-writer command，只由單一 OpenAB backlog agent執行；local implementation agent不跑，
避免兩個不共享lock的runtime同時查重後各自建列。`--requested-by`必填，`--assignee`必須和它相同，
也就是只建立給當次sender。省略`--report-to`時回報對象預設是`--requested-by`，也可以明確帶
`--report-to U…`或`--no-reporter`。相對日期先按`Asia/Taipei`換成`YYYY-MM-DD`再傳入。

查重只比對正規化後完全同名、尚未完成且未封存的列。既有列已在「PM確認中」時只回連結，
不追加 assignee；確認是復發或另一件事後，才用 `--force` 另建。從既有 item 留言串呼叫時
也必須先向使用者確認，再帶 `--force`。

命中既有列時不改原本的回報對象，即使 `add` 帶了 `--report-to` / `--no-reporter`；確定要改時
再跑 `reporter`。若 `add` 回「建立結果不明」，Slack可能已收下request，先到List搜尋同名列，
不要直接重跑。

List 沒有「回報對象」欄。工具把回報設定寫成 item 留言串裡可見、帶結構化block ID的bot訊息，
最新一則生效；任意留言或由bot轉貼的marker文字都不算設定。完整理由見
[ADR 0010](docs/adr/0010-store-reporter-settings-in-item-threads.md)。

## 回報進度

回報寫進**該列原生的 item 留言串** —— PM 本來就在那裡講話。
Slack 在建列時就替每一列開好串了，這支工具只查既有串、不另建串（推導方式與取捨見
[ADR 0001](docs/adr/0001-report-into-the-native-item-comment-thread.md)）。

```bash
# 中間進度：只回在串裡，不 @ 人、不改狀態
bin/slack-list progress Rec0B… "後端改完，佈建零失敗行"

# 可以驗收了：@ 回報對象 + 狀態改成「PM確認中」
bin/slack-list ready Rec0B… \
  --url    https://fix-spc-update.teamsync-frontend.pages.dev \
  --report drafts/2026-08-19/reports/report-1786-stock-status.md

# 沒有畫面可看的單（後端、純文件）：沒有 QA table 可寫，用 flag
bin/slack-list ready Rec0B… --no-url \
  --changed "生產單建立時就佔料，完工才落帳" \
  --verify  "建一張生產單，確認投入明細出現"

# 沒有 GitHub credential 時，把完整 issue 草稿交回原生 item 留言串
bin/slack-list draft Rec0B… \
  --md drafts/2026-08-18/inventory.md \
  --repo ShuChenAI/teamsync-frontend \
  --summary "已定位成前端庫存表欄位映射問題" \
  --requested-by U0B…
```

`--report` 是一份 md，整份當訊息本體發出去，模板固定四段 —— 改了什麼／⚠️ 要先知道的（有才寫）
／怎麼驗收／QA case。範本是 `skills/slack-todo/report-template.md`，缺段就不准發。
表格靠 Slack 的 `markdown` block 送，Slack 會在伺服器端把它拆成原生 blocks（`## 標題` 變
`header`、pipe table 變 `table`），所以 QA case 在 Slack 裡是一張真的表格，不是一堆 `|`。
上限是一則訊息 12,000 字，破了才改用 `--md` 當附件。

沒有畫面可看的單（後端、純文件）才走 `--changed` + `--verify`，兩個都必填、都可以重複給。
訊息本身不交代這兩件事的話，PM 收到的就只是一句「可以驗收了」，然後他會回頭問你。

`--url`（測試連結）跟 `--no-url` 也是二選一必填，**沒有預設值是刻意的**：驗收步驟寫得再清楚，
PM 沒有地方可以照著做還是等於沒寫，而「忘記附連結」不會有任何徵兆。二選一讓忘記變成跑不動。
前端的分支預覽是 branch 名稱把 `/` 與其他非英數字元換成 `-`，接 `.teamsync-frontend.pages.dev`。
腳本不自己從 git 推導 —— 它在 `work-helper` 目錄底下跑，`git` 問到的會是 work-helper 自己的
branch。發出去之前它會先問一下，連不到就中止（判的是 `>= 400`，不是只判 404 —— 還沒部署好的
分支預覽在 Cloudflare 上回的是 403）。

⚠️ **這個檢查一定要自報 User-Agent。** urllib 的預設值是 `Python-urllib/3.x`，Cloudflare 的
bot 規則直接擋掉 —— 實測同一個活著的網址：`Python-urllib/3.12` → 403、`python-requests` → 200。
而且 HEAD 被擋時要改用 GET 再問一次才算數；只認 405 的話，活著的網址會被判成死的（實際發生過）。

`--quiet` 不 `@` 人，批次補狀態時用。

`@` 的是**回報對象**，不是「指派對象」。明確的 `reporter` 設定優先；沒有設定時，
真人建立的列用 `created_by`，bot 代建的列用來源註記裡的發起者。兩者都找不到時不 `@` 人，
不會拿目前 assignee 來猜。

讀回覆 —— PM 回的東西都在這裡：

```bash
bin/slack-list replies            # 掃整張表，只列「有別人回過」的
bin/slack-list replies Rec0B…     # 看某一列（--all 連 bot 自己發的也印）
```

`ready` 先發訊息、後改狀態。反過來的話訊息發失敗會留下
「表上寫 PM確認中 但沒人被通知」，那正是把兩件事綁進同一支指令要防的東西。

`WORK_HELPER_ISSUE_MODE=manual` 的 agent 不持有 GitHub credential。它用 `draft` 上傳完整
Markdown，並附指紋搜尋頁和 New issue 頁；核准者從網頁提交，或把附件交給有 `gh` 權限的
local agent。這種 agent 也不能證明所有 GitHub issue 已關閉，所以不執行 `ready`。

沒有任何刪除 Slack 內容的指令，這是刻意的。

**issue 對到哪一列不存在這裡**，正本是 issue body 第一行那句可見的 Slack 來源，
查法是 `gh issue list --search "Rec0B…" --state all`。工具不留副本 ——
留了就是養一份會過期的東西。

### 這條線需要的東西

- 不用設 channel。留言串的 channel 由 list id 推導（`F…` → `C…`），bot 預設就在裡面
- scope：`chat:write`、`files:write`、`lists:write`，
  以及讀留言串要的 `groups:read` + `groups:history`

## 卡住的話

Slack 失敗時 HTTP 還是回 200，錯誤藏在 body 的 `ok:false`。腳本會把 `error` 印出來並附一句人話解釋。常見的：

| error | 意思 |
|---|---|
| `not_found` | list id 錯，或那張表沒分享給 app |
| `missing_scope` | 少 `lists:read`。加完 scope 要重裝 app，token 會換一組 |
| `invalid_auth` | token 錯或過期 |
| `ratelimited` | Tier 2，每分鐘 20+ 次 |

## 還沒做的

- `fields` 跑出來之前，`todo` 印的欄位名是 Slack 給的原始 key，不一定好看。看過真實資料再調。
- 有些項目的真正規格全在留言裡（`敘述` 欄只有「功能...」）。`slack-list replies` 讀得到，但**沒有任何東西會提醒你去讀** —— 派工前要自己先看過那一列的留言串，不然拿到的需求會比實際的少一半。
- 沒有 Events API，只能定時輪詢 —— **bot 不會被主動叫醒**。PM 在討論串裡回了什麼要自己去問（`slack-list replies`），不會有人通知你。
- 表的 schema 改不動：加欄位、加選項都回 `missing required field: id`（新元素的 id 只有 Slack 發得出來）。要動欄位只能去 UI。
- `conversations.rename` 比 UI 嚴格 —— 注音符號會被擋，而且回的是誤導的 `name_taken`。改 channel 名走 UI。
- 沒有轉移頻道管理員的 API（`conversations.setManagers` 之類全是 `unknown_method`，`admin.*` 要 Enterprise Grid）。channel 讓自己建，不要讓 bot 建。
