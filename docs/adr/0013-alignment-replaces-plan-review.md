# 對齊取代看計畫：接單後停在 pane 裡談，談完直接實作

接單的 agent 讀完 issue，白話講幾句它理解的是什麼，**停在 pane 裡等人**。
不先寫 issue comment。你進去談，談完它直接實作。

這推翻 [ADR-0004](./0004-plans-go-into-issue-comments-not-interactive-approval.md) 的關卡設計，
並修正 [ADR-0007](./0007-align-inside-the-worktree-and-never-hand-off.md) 一個隱含前提。兩份原文都留著。

## ADR-0004 輸在哪

它的對照表（互動核可 vs 計畫進 comment）現在讀起來還是對的 —— 它沒有算錯任何一格。
它輸在表上沒有的一欄：**那些 comment 沒有讀者。**

計畫寫進 issue 換到的是「批次看 N 份」。實際跑起來，要談的時候你會直接進 pane 談，
不會先讀那份 comment；不用談的時候那份 comment 也不影響任何決定。
兩種情況它都沒有被讀 —— 一份沒有讀者的產出，是純成本。

`fleet-dry-run-checklist.md` 的 5b 本來就預留了這個出口：
「跑完一輪一份都沒擋到的話記下來 —— 那表示任務已經夠好，這關可以改成只留給複雜的」。

## 批次沒有掉，換了形式

ADR-0004 怕的是「10 個 agent 在 3 小時內隨機打斷你 10 次」。**那個風險在這個停點不存在**：
接單後的停是**確定的**（bootstrap 完幾秒內），不是隨機的。
N 個 agent 可以全停在那裡，你 `herdr agent list` 看誰 `idle`，一個一個進去談。

批次從「讀 N 份計畫」變成「談 N 次」。少掉的是那份沒人讀的 comment，
多出來的是你本來就要花的談話時間。

## ADR-0007 的前提修正

ADR-0007 從「comment 帶得走結論、帶不走推導」推到「**所以不換 agent**」。
那一步的隱含前提是「交接載體只能是 comment」。

handoff 檔是整段對話的壓縮，**它帶得走推導**。前提破了，結論就只剩「別用 comment 換手」。
換 agent 本身沒有被禁止 —— 載體對就行。

⚠️ `handoff` skill 的預設是寫進 OS 的 temp 目錄（明文寫 "not the current workspace"），
那份會跟著重開機消失，跨裝置更不成立。接單的任務要換手，handoff 檔寫在 worktree 裡、
用 `info/exclude` 忽略，跟身分卡同一個機制。

## 紀錄寫不寫，由人當場決定

**談完就實作，不預先總結。** 共識活在那個 agent 的 context 裡。

要留紀錄的時機只有兩個，判準是「**這件事會不會跨過今天**」——
跟 [ADR-0008](./0008-same-day-work-skips-the-issue.md)「當天做完不開 issue」同一條線，不是新概念：

| 時機 | 載體 |
| --- | --- |
| 要換手（這個 agent 收不掉） | handoff 檔（在 worktree 裡） |
| 跨過今天（要拆、PM 補規格、人被叫去開會） | issue comment，連推導一起寫 |

**為什麼不預先寫。** 想過在 `CLAUDE.local.md` 身分卡裡固定加一節「已達成的共識」，否決了：
多數任務兩個時機都不會到，而每個任務都要付這個成本。
真的要留，講一句 agent 就寫了 —— 寫進 skill 是 no-op。

代價講清楚：**共識沒有落檔，agent 在實作到驗收之間 compact 掉的話，推導就是掉了。**
它會知道結論（issue 上有改動範圍和驗收條件），但不知道為什麼排除了 B。
那時候你重講一句話。接受這個代價，換掉「每個任務都預先寫一份可能沒人看的東西」。

## 這條沒有動到的

- **對齊期間不准改檔案**（ADR-0007 的第一條防護）—— 不受影響。
- **一個 slug 一個 worktree 一個 agent**（ADR-0002）—— 不受影響。
- **`blocked` / `idle` 是通知管道** —— 不受影響。只是接單後的停不需要 `agent wait`，
  `herdr agent list` 看一眼就夠；`agent wait` 留給「做到一半需要人」。
