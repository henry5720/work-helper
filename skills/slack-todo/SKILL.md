---
name: slack-todo
description: 讀 PM 記在 Slack「Bug/需求總表」上的待辦。當使用者說「看看 PM 有什麼待辦」「Slack 上有什麼問題」「今天要處理什麼」「Bug 總表」「需求總表」時使用。
---

# 讀 PM 的待辦表

PM（chieh）把 bug 與需求記在 Slack 的一張 List：**Bug/需求總表**。
這個 skill 負責把那張表拿下來、看懂、然後告訴使用者裡面有什麼。

**目前只做「讀」。** 自動開 issue 的判準還沒定案，見最下面。

---

## 🚫 先講會做壞的三件事

1. **拿 `敘述` 欄當完整規格** —— 很多列的 `敘述` 只有「功能...」這種被截斷的字。
   真正的規格在那一列的**留言串**裡，而留言串 **API 讀不到**（見下方限制）。
   資訊不足就說「這列要看 Slack 留言」，**不要自己補一個看起來合理的需求**。
2. **假設一列 = 一張 issue** —— 實際看過的例子裡，一列的留言串包含 3 個獨立問題
   （UX 疑慮 / bug / 需求變更）。顆粒度還沒定案，不要自作主張拆或合。
3. **動到那張表** —— 這個 app 只有 `lists:read`，寫不了。就算之後給了寫入權，
   `狀態` 欄是 PM 在維護的，不要碰。

---

## 📋 怎麼拿資料

```bash
cd ~/code/work-helper
./bin/slack-list todo     # 一行一列，人看的
./bin/slack-list json     # 壓平後的 JSON，要程式處理時用
./bin/slack-list fields   # 不確定欄位叫什麼的時候先跑這個
```

第一次跑或報錯時：

```bash
./bin/slack-list env      # 確認 .env 讀到了（token 會遮起來）
./bin/slack-list count    # 通不通，這個最快
```

`.env` 沒設定的話會直接報「`.env` 裡沒有 SLACK_BOT_TOKEN」，照
[repo README](../../README.md) 設定，**不要試圖繞過或自己拼 curl**。

### 錯誤怎麼看

Slack 失敗時 HTTP 還是回 200，錯誤在 body 的 `ok:false`。腳本已經翻成人話了，直接照著做：

| error | 意思 |
|---|---|
| `not_found` | list id 錯，或那張表沒分享給 app |
| `missing_scope` | 少 `lists:read`。加完 scope 要重裝 app，token 會換一組新的 |
| `invalid_auth` | token 錯或過期 |
| `ratelimited` | Tier 2，每分鐘 20+ 次，等一下再跑 |

---

## 🗂️ 這張表長什麼樣

實際欄位以 `./bin/slack-list fields` 為準。已知的有：

| 欄位 | 內容 |
|---|---|
| 名稱 | 帶前綴代號，例如 `T04 退貨表供應商欄位刪除`、`V01 在途欄位調整`、`B03 審核中心審核紀錄filter` |
| 敘述 | 一段說明，**常常被截斷或只有幾個字** |
| 狀態 | `前端完成` / `後端完成` / `暫停中（待觀察）` / `PM確認中` / 空白 |

兩個要注意的：

- **名稱前綴（`T` / `V` / `S` / `D` / `B` + 數字）是某種模組代號，但對應關係還沒確認。**
  不要憑字面猜它對到哪個模組，要用就先問使用者。
- **`狀態` 欄把前端和後端分開** —— 代表一件事可能同時牽涉
  `~/code/teamsync-frontend` 和 `~/code/teamsync-backend`。只看前端會漏。

---

## ⚠️ 已知限制（不要試圖繞過）

- **留言串讀不到。** `slackLists.*` 沒有任何 comment 相關的 method，
  `slackLists.items.info` 的回應裡也沒有 `thread_ts` / `channel`，定位不到那串對話。
  有些項目的規格 100% 在留言裡，那些只能靠人補。
- **沒有 Events API。** Slack 不會推送 List 的變動，只能定時輪詢。
- **只有讀取權。** app 的 scope 只有 `lists:read`。

---

## 🚧 還沒定案的（不要自己發明）

以下都討論過但沒有結論，遇到時**問使用者，不要自作主張**：

- **顆粒度**：一列開幾張 issue？前後端要不要拆兩張？
- **判準**：什麼樣的列算「規格夠清楚可以直接動工」？
- **開單流程**：已經定的部分只有兩條 ——
  issue 走 `~/code/teamsync-frontend` 的
  [`docs/guides/workflow/github-issue-standards.md`](../../../teamsync-frontend/docs/guides/workflow/github-issue-standards.md)，
  規格不足的掛 `needs-triage`。其他還沒定。
- **冪等性**：構想是把 list item 的 id 寫進 issue body 當指紋
  （`<!-- slack-list-item: <id> -->`），開單前先 `gh issue list --search` 比對。
  **構想而已，還沒實作，不要當成既定作法。**
