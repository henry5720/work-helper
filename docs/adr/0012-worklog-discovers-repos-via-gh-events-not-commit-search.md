# 日誌的 repo 發現層用 gh events，不是 gh search commits

`daily-worklog` 要先知道「今天動過哪些 repo」才能去讀 commit body。原本的做法是掃 `~/code/*/`，
那是寫死的個人習慣：實測 2026-08-20 當天有 4 筆 commit 在 `~/.local/share/chezmoi`
（GitHub 上是 `henry5720/dotfiles`），掃 `~/code` 永遠看不到，日誌就少了一整塊工作。改用 GitHub
當發現層是對的，但**不能用 `gh search commits`**：它只索引預設分支，而當天的 commit 幾乎都在
feature branch 上。實測 `c55d9a0f1`（`style(ams): 收件人名單讀得出來`）確實推上了
`origin/feat/vivispa-idle-slot-broadcast`（`gh api repos/ShuChenAI/teamsync-frontend/commits/c55d9a0f1`
查得到），但 `gh search commits "收件人名單" --repo ShuChenAI/teamsync-frontend` 回的 5 筆全是 main
上的，沒有它。加上 commit 的 email（`henry5720@hotmail.com.tw`）沒跟 GitHub 帳號連結，
`--author=@me` 當天回 0 筆、`--author-name=henry` 回的 6 筆是同名陌生人在
`Hencerel4/contribution-backfill-2025-2026` 的 commit。所以「有沒有推」不是關鍵，「有沒有 merge
進預設分支」才是，而日誌不能等 merge。

定案是 `gh api users/<login>/events` 當發現層、local git 當內容層。events 撈得到 private repo、
feature branch、以及 `~` 底下任何位置的 repo，代價是四個要寫進 skill 的限制：時間是 UTC
（本地日界要換算，直接用本地日期字串比對會回空陣列）、payload 沒有 commit 內容
（`payload.size` 與 `payload.commits` 都是 `null`）、分頁上限約 300 筆 / 90 天（第 4 頁回 422）、
未推的 commit 看不到（刻意接受：沒推的算還沒做完）。gh 不可用或要補更早的日誌時退回掃 `$HOME`
（`-maxdepth 6`，實測 28 個 repo、連 `git log` 迴圈 2.8 秒），prune 清單刻意**不含 `.local`** ——
chezmoi 的 repo 就在那底下。
