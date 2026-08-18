# 核准草稿的是發起偵察的授權使用者

草稿不再限定由 Henry 看過。發起偵察的授權使用者，不論是開發者或 PM，都可以核准草稿；
發布者可以是有 GitHub credential 的 agent，也可以是從 GitHub 網頁提交的人。

## 為什麼

Slack backlog agent 讓 PM 可以直接查 repo、要求偵察。如果草稿最後仍必須轉交 Henry 核准，
流程只是從「PM → Henry → agent」變成「PM → agent → Henry」，沒有消除轉述。

核准和實作是兩個角色。核准者確認範圍、驗收條件與顆粒度；負責人接到 GitHub issue 後，
仍會在任務層對齊做法。讓 PM 核准草稿，不會讓 PM 取得 code write 或 push 權限。

## 為什麼不讓偵察自動發布

ADR-0006 的兩個問題仍存在：同批偵察無法互相查重，顆粒度也必須在 issue 出生前決定。
所以草稿一定先停在人前。沒有 GitHub credential 的環境則把 Markdown 交到 item 留言串，
由核准者或 local agent發布；不把 broad GitHub credential交給遠端 backlog agent。

## 代價

同一份草稿可能由不同人發起、核准、發布。草稿和 issue body要留下 Slack 發起者、核准者與
可見指紋，不能再用 GitHub author 猜誰做了哪個決定。
