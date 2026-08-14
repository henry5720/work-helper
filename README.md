# work-helper

工作用的 agent 能力：指令放 `bin/`，自己寫的 skill 放 `skills/`。
**離職就用不到的東西放這裡** —— 跨工作還要用的環境設定在 `dotfiles`，純文件在 `work-docs`。

```
bin/slack-list          讀 Slack 上那張「Bug/需求總表」
skills/slack-todo/      ↑ 的 skill：讓 agent 知道有這個東西、什麼時候用
skills/daily-worklog/   從 git commit 產工作日誌（產出寫進 work-docs）
```

Slack 那條線目前**只做讀取**，分析 repo、開 issue、跟人討論等能讀了再加。

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
# 填 SLACK_BOT_TOKEN 和 SLACK_LIST_ID
```

`.env` 在 `.gitignore` 裡，不會被 commit。

`SLACK_LIST_ID` 從那張表的網址列取。

## 用

```bash
bin/slack-list env      # 先確認設定讀到了（token 會遮起來）
bin/slack-list count    # 通不通，看這個最快
bin/slack-list fields   # 這張表有哪些欄位、各是什麼型別
bin/slack-list todo     # 一行一列，人看的
bin/slack-list json     # 壓平後的 JSON，給程式吃
bin/slack-list raw      # Slack 原始回應，不加工
bin/slack-list sample   # 只印第一列的原始結構
```

`todo` 是預設，`bin/slack-list` 不帶參數就是它。

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
- List item 的**留言串**讀不到 —— `slackLists.*` 沒有任何 comment 相關的 method，item 的回應裡也沒有 `thread_ts` / `channel`。有些項目的真正規格全在留言裡（`敘述` 欄只有「功能...」），那些只能靠人補。
- 沒有 Events API，只能定時輪詢。
