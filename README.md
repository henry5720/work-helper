# work-helper

工作用的 agent 能力：指令放 `bin/`，自己寫的 skill 放 `skills/`。
**離職就用不到的東西放這裡** —— 跨工作還要用的環境設定在 `dotfiles`，純文件在 `work-docs`。

```
bin/slack-list          讀「Bug/需求總表」，並把處理進度回報到 Slack
skills/slack-todo/      ↑ 的 skill：讓 agent 知道有這個東西、什麼時候用
skills/daily-worklog/   從 git commit 產工作日誌（產出寫進 work-docs）
state/threads.json      record_id → 討論串，由 progress / ready 自己維護
```

## 裝成 skill

skill 沒有安裝程式，就是把資料夾拉線進 `~/.claude/skills/`：

```bash
for s in ~/code/work-helper/skills/*/; do
  ln -sfn "$s" ~/.claude/skills/"$(basename "$s")"
done
```

之後 `git pull` 就自動更新，跟 `dotfiles` 部署 `.zshrc` 是同一招。

## 需要什麼

- Python 3（標準函式庫就夠，不用裝套件）
- 一個 Slack app，scope 只要 `lists:read`
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

Slack List 的項目留言串**沒有任何 API**（試過的都回 `unknown_method`），
所以進度不寫在項目裡，寫在一個 channel 的討論串裡，再用連結兩邊互指。
一個項目一條串。

```bash
# 中間進度：只回在串裡，不 @ 人、不改狀態
bin/slack-list progress Rec0B… "後端改完，佈建零失敗行"

# 可以驗收了：@ 指派對象 + 冒到 channel 主畫面 + 狀態改成「PM確認中」
bin/slack-list ready Rec0B… \
  --changed "生產單建立時就佔料，完工才落帳" \
  --verify  "建一張生產單，確認投入明細出現" \
  --verify  "帳頁按確認完工，確認成品進來" \
  --md 驗收說明.md      # 可選，複雜時才附
```

`--changed` 跟至少一個 `--verify` 是必填。訊息本身不交代這兩件事的話，
PM 收到的就只是一句「可以驗收了」，然後他會回頭問你。

`--quiet` 不 `@` 人也不 broadcast，批次補狀態時用。

第一次對某一列下 `progress` 或 `ready` 就會開串，之後都回同一條。
對應存在 `state/threads.json`；**該列的「連結」欄本來是空的**才會順手寫一份
給人點 —— PM 自己放的連結不會被蓋掉（398 列裡有 15 列本來就有連結）。

`ready` 先發訊息、後改狀態。反過來的話訊息發失敗會留下
「表上寫 PM確認中 但沒人被通知」，那正是把兩件事綁進同一支指令要防的東西。

沒有任何刪除 Slack 內容的指令，這是刻意的。

### 這條線需要的東西

- `.env` 多一個 `SLACK_PROGRESS_CHANNEL`（channel ID，`C` 開頭）
- 那個 channel 要把 `@work-helper` 加進去
- scope：`chat:write`、`files:write`、`lists:write`；
  channel 是**私人**的話還要 `groups:read` + `groups:history`（公開的用 `channels:*`）

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
- List item 的**留言串**讀不到 —— `slackLists.*` 沒有任何 comment 相關的 method，item 的回應裡也沒有 `thread_ts` / `channel`。有些項目的真正規格全在留言裡（`敘述` 欄只有「功能...」），那些只能靠人補。`progress` / `ready` 的討論串是繞路，不是把留言串接通了。
- 沒有 Events API，只能定時輪詢。PM 在討論串裡回了什麼，得自己跑 `conversations.replies` 去撈，bot 不會被主動叫醒。
- 表的 schema 改不動：加欄位、加選項都回 `missing required field: id`（新元素的 id 只有 Slack 發得出來）。要動欄位只能去 UI。
- `conversations.rename` 比 UI 嚴格 —— 注音符號會被擋，而且回的是誤導的 `name_taken`。改 channel 名走 UI。
- 沒有轉移頻道管理員的 API（`conversations.setManagers` 之類全是 `unknown_method`，`admin.*` 要 Enterprise Grid）。channel 讓自己建，不要讓 bot 建。
