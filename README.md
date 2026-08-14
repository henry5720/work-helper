# work-helper

把工作上的雜事包成指令，給人和 agent 共用。

現在只有一件事：**讀 Slack 上那張「Bug/需求總表」**。
其他（分析 repo、開 issue、跟人討論）等這個能用了再加。

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
