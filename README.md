# work-helper

工作用的 agent 能力：指令放 `bin/`，自己寫的 skill 放 `skills/`。
**離職就用不到的東西放這裡** —— 跨工作還要用的環境設定在 `dotfiles`，純文件在 `work-docs`。

```
bin/slack-list          讀「Bug/需求總表」，並把處理進度回報到 Slack
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

skill 沒有安裝程式，就是把資料夾拉線進去。**拉兩個地方**：

```bash
for s in ~/code/work-helper/skills/*/; do
  n="$(basename "$s")"
  ln -sfn "$s" ~/.agents/skills/"$n"    # 工具中立層，opencode 讀這裡
  ln -sfn "$s" ~/.claude/skills/"$n"    # Claude Code 讀這裡
done
```

`~/.agents/skills/` 是跨工具的共用位置（`npx skills` 裝的東西也在那）。
opencode 官方文件列的搜尋路徑包含 `~/.agents/skills/*/SKILL.md`、
`~/.claude/skills/*/SKILL.md` 和 `~/.config/opencode/skills/*/SKILL.md`，
所以兩邊都拉最保險 —— 不用去賭它跟不跟隨 symlink。

之後 `git pull` 就自動更新，跟 `dotfiles` 部署 `.zshrc` 是同一招。

## 需要什麼

- Python 3（標準函式庫就夠，不用裝套件）
- 一個 Slack app。只讀的話 `lists:read` 就夠；要回報進度還需要
  `lists:write`、`chat:write`、`files:write`，私人 channel 再加 `groups:read` + `groups:history`
- 那張 List 要分享給這個 app，不然會回 `not_found`

## 設定

```bash
cp .env.example .env
# 填 SLACK_BOT_TOKEN、SLACK_LIST_ID、SLACK_MY_USER_ID
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
bin/slack-list json     # 壓平後的 JSON，給程式吃
bin/slack-list raw      # Slack 原始回應，不加工
bin/slack-list sample   # 只印第一列的原始結構
```

`todo` 是預設，`bin/slack-list` 不帶參數就是它。

## 回報進度

回報寫進**該列原生的 item 留言串** —— PM 本來就在那裡講話。
Slack 在建列時就替每一列開好串了，這支工具只查不建（推導方式與取捨見
[ADR 0001](docs/adr/0001-report-into-the-native-item-comment-thread.md)）。

```bash
# 中間進度：只回在串裡，不 @ 人、不改狀態
bin/slack-list progress Rec0B… "後端改完，佈建零失敗行"

# 可以驗收了：@ 回報對象 + 狀態改成「PM確認中」
bin/slack-list ready Rec0B… \
  --changed "生產單建立時就佔料，完工才落帳" \
  --verify  "建一張生產單，確認投入明細出現" \
  --verify  "帳頁按確認完工，確認成品進來" \
  --md 驗收說明.md      # 可選，複雜時才附
```

`--changed` 跟至少一個 `--verify` 是必填。訊息本身不交代這兩件事的話，
PM 收到的就只是一句「可以驗收了」，然後他會回頭問你。

`--quiet` 不 `@` 人，批次補狀態時用。

`@` 的是**回報對象**，也就是把這一列寫上表的人（`created_by`）——
不是「指派對象」，那欄是負責做的人，通常就是你自己。

讀回覆 —— PM 回的東西都在這裡：

```bash
bin/slack-list replies            # 掃整張表，只列「有別人回過」的
bin/slack-list replies Rec0B…     # 看某一列（--all 連 bot 自己發的也印）
```

`ready` 先發訊息、後改狀態。反過來的話訊息發失敗會留下
「表上寫 PM確認中 但沒人被通知」，那正是把兩件事綁進同一支指令要防的東西。

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
