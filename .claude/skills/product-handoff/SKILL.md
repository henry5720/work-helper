---
name: product-handoff
description: 讀 Slack item thread 與指定 repo，整理成給下一個 agent 或 reviewer 的 handoff draft；只產 draft，不修改 repo 或 Git。
---

# Product handoff

這支 skill 把產品需求的來源、repo 現況與決策整理成一份可接手的 **draft**。它可以讀
Slack 原生 item 留言串、讀指定 repo 的檔案與 git 狀態，但不代替實作者做修改。

## 邊界

- 只產出 handoff draft；不要建立、刪除或改寫 repo 檔案。
- 不 `git add`、`commit`、`checkout`、`reset`、`merge`、`push`，也不建立 branch 或 worktree。
- 不把「未執行」寫成「已驗證」；每個結論都附來源或明確標成未知。
- 來源是 Slack 的原生 item thread。要回報或交付 draft 時，沿用同一條 thread，不另開
  channel 或討論串；若 runtime 沒有原 thread context，停下來回報這項限制。
- 保留 working tree 既有變更，不用 reset 或清理來取得「乾淨」的證據。

## 讀取順序

1. 從 runtime context 取得 repo、Slack channel/thread 與原 thread permalink；缺任何一項就
   標成「未提供」，不要猜。
2. 讀原生 item thread 的完整訊息，整理需求、PM 決策、限制與仍未回答的問題。
3. 在指定 repo 讀相關檔案、設定、測試與 git 狀態；以檔案路徑、行號或 symbol 作為 code
   anchor。只讀，不改檔。
4. 把衝突或證據不足的地方放進「未決問題」，不要自行補決策。
5. 輸出下列固定格式的 draft；需要交回 Slack 時，交回原 item thread。

## Draft 格式

```markdown
# Product handoff draft: <一句話標題>

## Repo / commit
- repo: `<repo 名稱或絕對路徑>`
- commit: `<目前 HEAD SHA>`
- working tree: `<clean / 有既有變更；列出影響檔案>`

## Slack source
- item / record: `<record_id>`
- permalink: `<原 item thread 的 Slack permalink>`

## Code anchors
- `<path:line 或 symbol>` — <目前行為與證據>

## 決策
- <已由使用者或 PM 明確決定的事項；附 Slack 訊息或 anchor>

## 未決問題
- <尚未回答的問題；若沒有寫「無」>

## 驗收條件
- [ ] <可觀察、可判定的條件>

## 交接注意事項
- <限制、依賴、artifact 或尚未執行的驗證>
```

`repo/commit`、`code anchors`、`Slack permalink`、`決策`、`未決問題`、`驗收條件` 六個
區段不可省略。commit 是讀到的 HEAD，不是為了 handoff 新建的 commit。若需要附上 PNG、
Markdown 或明確要求的 self-contained HTML，記錄檔名、用途與它應回到的原 thread；實際
產生圖片走 `company-imagegen`，實際附檔走 `slack-list artifact`。
