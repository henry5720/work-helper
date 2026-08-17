# 進度與驗收回報寫進 list item 的原生留言串

Slack List 的 item 留言串**是真的 thread**，住在一個由 list id 推導出來的 channel
（`F0B9PSESQ2U` → `C0B9PSESQ2U`，把開頭的 `F` 換成 `C`）。parent 訊息由 `USLACKBOT`
發出、`subtype: "list_record_comment"`，並在 `slack_list.list_record_id` 帶著 record id。
bot 預設就是該 channel 的成員，`conversations.history` / `replies` 讀得到，
`chat.postMessage` 帶 `thread_ts` 也寫得進去（2026-08-17 實測 `ok: true`，
parent 的 `reply_count` 從 0 變 1）。

**所以 `progress` / `ready` 一律回進原生 item 留言串，不再自建討論串。**

## 為什麼原本沒這樣做

第一版查的是 `slackLists.*`，那組 API 確實沒有任何 comment 相關的 method，item 的回應裡
也沒有 `thread_ts` / `channel`，於是結論寫成「留言串讀不到」。**那個結論是對的問題問錯 API** ——
留言不歸 `slackLists.*` 管，歸 `conversations.*` 管。`F→C` 這個推導沒有出現在任何官方文件裡，
是從 `search.messages` 回傳的 channel id 反推出來的。

## 代價

- **失去 `reply_broadcast`。** 原生串沒有 channel 主畫面可以冒，通知完全靠 `@`。
  接受這點的前提是「PM 基本上不離開那張表」（2026-08-17 向 PM 確認過）。
- **綁死在一個沒有文件的推導上。** Slack 哪天改掉 `F→C`，整條線會斷。
  斷掉的訊號很明顯（`conversations.info` 回 `channel_not_found`），不是靜默失敗。

## 連帶刪掉的東西

自建串存在的唯一理由是「原生串碰不到」，前提沒了，圍繞它長出來的都跟著沒了：

- `state/threads.json` —— 四個欄位全是副本。`ts` / `permalink` 推導自 Slack、
  `title` 讀表上的「名稱」欄、`issues` 查 issue body 第一行的指紋。
  照這個 repo 原本就有的規矩「快取可以錯，正本不能錯」，最安全的快取是沒有快取。
- `link` 子命令 —— 它的工作就是維護那份快取。
- `open_thread()` —— 不需要建串。實測 398 列**全部**都已經有 parent，Slack 在建列時就開好了，
  這是查詢不是建立。
- 往「連結」欄寫 permalink —— 那格是 PM 放外部參考資料的地方
  （Google Docs spec、Figma、Canva、後台網址），bot 不該跟他搶。

## 這個錯誤實際造成的損失

改之前，PM 的回覆累積在原生串裡而這條線從來沒讀過（398 列中有 107 條串有人回過）。
2026-08-17 一天之內就撞到三次：

- **S01 匯入權限**：以為要回去問 PM 裁決，PM 在 08-04 就答了（「要請後端調整」）。
- **V03 待確認數字**：PM 08-05 給過假說（「是不是計算到已取消的異動」），
  派工時沒帶上，開出來的 issue 少了這條線索。
- **A01 聊天室異動遺失**：原生串裡 PM 把範圍縮小成「只有異動紀錄沒記，庫存總覽是對的」，
  表上的 `敘述` 欄仍寫成兩個地方都壞。
