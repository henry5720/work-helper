---
name: slack-todo
description: 讀 PM 記在 Slack「Bug/需求總表」上的待辦，並把處理進度回報回去。當使用者問「PM 有什麼待辦」「Bug/需求總表」時使用；做完一張要通知 PM 驗收時也用。
---

# PM 的待辦表

PM（chieh）把 bug 與需求記在 Slack 的一張 List：**Bug/需求總表**。
讀它、看懂它、把處理進度回報回去，都走 `~/code/work-helper/bin/slack-list`。

**不要自己組 curl，也不要用 Slack MCP 做這件事。** 腳本已經處理翻頁、
錯誤翻譯、欄位對應、討論串對應。繞過它就是重寫一次，而且會寫錯。

---

## 🚫 先講會做壞的三件事

1. **拿 `敘述` 欄當完整規格** —— 很多列的 `敘述` 只有「功能...」這種被截斷的字。
   真正的規格常在那一列的**留言串**裡，而留言串 API 讀不到。
   資訊不足就說「這列要看 Slack 留言」，**不要自己補一個看起來合理的需求**。
2. **假設一列 = 一張 issue** —— 實際看過的例子裡，一列的留言串包含 3 個獨立問題
   （UX 疑慮 / bug / 需求變更）。顆粒度還沒定案，不要自作主張拆或合。
3. **改 `狀態` 欄** —— 那是 PM 在維護的。唯一的例外是 `ready` 指令，
   它只會寫「PM確認中」這一個值。其他狀態一律不要碰。

---

## 📋 讀

```bash
cd ~/code/work-helper
./bin/slack-list todo      # 一行一列，人看的
./bin/slack-list mine      # 只印指派給使用者自己的列
./bin/slack-list mine 庫存  # 再加關鍵字過濾（比對整列文字，不分欄位）
./bin/slack-list json      # 壓平後的 JSON，要程式處理時用
./bin/slack-list fields    # 不確定欄位叫什麼的時候先跑這個
```

問「我身上有什麼事」「跟 X 有關的」用 `mine`，不要自己撈 `json` 再土炮過濾。

每一列開頭的 `[Rec0B…]` 就是 record ID，回報時要用。

跑不動時先 `./bin/slack-list env`（確認 `.env` 讀到了）再 `count`（確認通得到）。
`.env` 沒設定會直接報哪個變數缺，照 [repo README](../../README.md) 設定。

---

## 📣 回報

**一列一串**：每個項目在 `SLACK_PROGRESS_CHANNEL` 有且只有一條討論串，
所有更新都回在裡面。腳本自己維護 `record_id → 討論串` 的對應，你不用管。

這條串存在的原因是 **Slack List 項目的留言串沒有任何 API** ——
每個候選 method 都回 `unknown_method`。所以進度寫在 channel 的串裡，
再用連結兩邊互指。它是繞路，不是把留言串接通了。

```bash
# 中間進度：只回在串裡，不 @ 人、不改狀態
./bin/slack-list progress Rec0B… "後端改完，佈建零失敗行"

# 可以驗收了：@ 指派對象 + 冒到 channel 主畫面 + 狀態改成「PM確認中」
./bin/slack-list ready Rec0B… \
  --changed "生產單建立時就佔料，完工才落帳" \
  --verify  "建一張生產單，確認投入明細出現在異動紀錄" \
  --verify  "回帳頁按「確認完工」，確認成品進來" \
  --md 驗收說明.md      # 可選，複雜時才附
```

三條規矩：

- **`ready` 只在使用者說可以驗收時跑。** 它會推播吵到 PM。
  你自己覺得寫完了不算；測試綠了也不算；**沒 push 的 commit 不算**。
  不確定就跑 `progress`，那個不吵人。
- **`--verify` 寫得出來才算做完。** 那是 PM 唯一真正需要的東西。
  「測試一下」等於沒寫。要寫成「開哪個頁面 → 做什麼 → 看到什麼」。
- **`--changed` 用白話。** PM 不看 commit，不要貼 SHA 或函式名。

`--quiet` 不 `@` 人也不 broadcast，只有使用者明講「先別吵他」時才用。

沒有任何刪除指令。要撤回已發的訊息，跟使用者說，讓他自己刪。

---

## 🗂️ 這張表長什麼樣

實際欄位以 `./bin/slack-list fields` 為準。壓平後常見的鍵：

| 欄位 | 壓平後的鍵 | 內容 |
|---|---|---|
| 指派對象 | `todo_assignee` | user ID，例如 `U0B54FKJ93R`。**一列可以掛多人**，壓平後是空白分隔的字串 |
| 名稱 | `name` | 帶前綴代號，例如 `T04 退貨表供應商欄位刪除`、`V01 在途欄位調整` |
| 敘述 | `Col0B8E4BG7JT` | 一段說明，**常常被截斷或只有幾個字** |
| 狀態 | `Col0B9U6UHD16` | 多選，值是 `OptXXXX` 代碼**不是人看的字串**；要對照文字跑 `fields` |

三個要注意的：

- **assignee 只有 ID，沒有名字。** 解成名字要 `users:read`，app 沒有那個 scope。
  自己的 ID 從 `.env` 的 `SLACK_MY_USER_ID` 拿（`mine` 已經處理好），別人的就只能是 ID。
- **名稱前綴（`T` / `V` / `S` / `D` / `B` + 數字）是某種模組代號，但對應關係還沒確認。**
  不要憑字面猜它對到哪個模組，要用就先問使用者。
- **`狀態` 是多選，而且前端後端分開** —— 一件事可能同時牽涉
  `~/code/teamsync-frontend` 和 `~/code/teamsync-backend`。只看前端會漏。

---

## ⚠️ 撞到會浪費時間的

- **表的 schema 改不動。** 加欄位、加選項都回 `missing required field: id`，
  新元素的 id 只有 Slack 發得出來。要動欄位只能請使用者去 UI 改。
- **沒有 Events API。** Slack 不會推送 List 或討論串的變動。
  PM 在串裡回了什麼，要自己跑 `conversations.replies` 撈。
- **Slack 失敗時 HTTP 回 200**，錯誤在 body 的 `ok:false`。腳本已經翻成人話，照著做。
  `missing_scope` 一律是「加完 scope 要重裝 app，token 會換一組新的」。

---

## 🚧 還沒定案的（不要自己發明）

開 issue 這條線討論過但沒有結論，遇到時**問使用者**：

- **顆粒度**：一列開幾張 issue？前後端要不要拆兩張？
- **判準**：什麼樣的列算「規格夠清楚可以直接動工」？
- **冪等性**：構想是把 record ID 寫進 issue body 當指紋
  （`<!-- slack-list-item: <id> -->`），開單前先 `gh issue list --search` 比對。
  **構想而已，還沒實作。**

已經定的只有一條：issue 走 `~/code/teamsync-frontend` 的
[`docs/guides/workflow/github-issue-standards.md`](../../../teamsync-frontend/docs/guides/workflow/github-issue-standards.md)，
規格不足的掛 `needs-triage`。
