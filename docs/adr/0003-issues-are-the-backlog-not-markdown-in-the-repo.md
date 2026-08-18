# issue 是 backlog 的正本，不要搬進 repo 當 markdown

Slack 的「Bug/需求總表」只是入口之一（還有 PM 口述、做別件事順手發現）。
**跨過今天的事，正本一律是 GitHub issue** —— 它同時是**交接載體**（偵察 → 負責人）、
**去重指紋**、**推導的長期存放**、**slug 的來源**。
當天做得完的不進 backlog，見 ADR-0008。

⚠️ issue **不是**「PM 看得到的介面」。PM 只看 Slack 那張表 ——
`bin/slack-list` 整支沒有一個字提到 issue，回報全走 item 留言串（ADR-0001）。

## 為什麼不放 repo 裡

backlog 檔進 git 會讓 N 個 worktree 各改一份，**backlog 自己 merge conflict**。
而且 issue 是跨 repo 的，backlog 檔不是。

## 代價：去重指紋只有 Slack 那條入口有

Slack 來的有 `Rec…` record_id 可以比對（`gh issue list --search "Rec0B…" --state all`），
PM 口述和順手發現的沒有。所以「讓 agent 自己開 issue」**只有 Slack 那條入口是安全的**，
其他要嘛人自己開，要嘛派工那句話得指定用什麼關鍵字搜。
負責人衍生出來的任務用母單編號當指紋（第一行寫「從 #1769 衍生」）。

指紋要**看得見**，不要藏在 HTML 註解裡 —— GitHub 搜尋會不會索引註解沒有定論，
而整套去重就靠那一個查詢。也不要靠 GitHub 原生的重複偵測：
官方說明只講網頁表單，沒講 `gh issue create` 走不走得到。
