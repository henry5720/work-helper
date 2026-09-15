# 用 `merge --no-ff` 併進一條長命的整合分支

> ⚠️ **git 層的正本 2026-09-16 搬到 repo 了**：teamsync-frontend 的
> `docs/guides/workflow/branch-integration-flow.md`，`CLAUDE.md` 有對應的四條鐵則。
> 理由是量出來這個模式**不是 fleet 專用** —— 2026-06～09 之間 `origin/dev` 上有 16 條這種分支，
> Lexi 8 條、foojiawen 4 條、daniel-yeh 2 條、henry 2 條，而 repo 的文件裡一個字都沒寫，
> 結果四個人各踩各的（抽樣 21 條子分支，9 條還躺在 origin）。那份不提 herdr、只講 git，團隊用得上。
>
> 詞彙同步統一：**整合分支**（收攏用的那條）＋ **子分支**（併進它的那些）。
>
> **本 ADR 留兩樣**：這個決定的由來（下面全文），以及只有 fleet 才成立的連帶規則。
> 衝突時以 repo 那份為準。
>
> ⚠️ 下面「整合分支最後會被 squash 進 `dev`」這句要小心 —— repo 的
> `frontend-release-flow.md` 把 squash / 一般 merge 寫成**每次自己判斷**（判準是 changelog 顆粒度），
> 不是固定 squash。代價是不是零要看那次選哪個。

一個模組一條整合分支（例如 `fix/inventory`），所有 worktree 從它開、做完 merge 回它，
最後由它對 `dev` 開一個 PR。**驗收只在整合分支，一次只 merge 一件。**

`--no-ff` 讓一顆 merge commit 剛好等於一個工作單位 —— 整合測試掛掉時
`git revert -m 1 <sha>` 就能打回乾淨。整合分支最後會被 squash 進 `dev`，
所以保留這些 merge commit 的代價是零。

## 但測到問題要回原 worktree 改，不要 revert

revert 掉一顆 merge commit 之後再 merge 同一條 branch，**內容不會回來**。
git 判斷「要併什麼進來」是看**歷史圖，不是看內容**：那條 branch 的 commit
已經是整合分支的祖先了，算出來的 merge base 包含它們 → 結論是「沒有新東西」。
而那顆「把改動反掉」的 commit 還在，所以 code 就是回不來。
要救得 revert 那顆 revert，很反直覺 —— 所以規則直接寫成「不要 revert」。

## 連帶規則

- **dev server 只開一個**（worktree 裡不開）。worktree 的價值在「agent 同時在寫」，
  不在「你同時在測」；你的注意力本來就一次一件。
- **~~worktree 最後才收~~ → 驗過就收**（2026-09-16 改）。原本的理由是「整合測試沒過要回去修，
  先收掉就得重開重裝」，但重開的成本沒那麼高，而 worktree 會越積越多（改這條的當天有 14 個、
  本地分支 46 條）。**判準改成「在整合分支那份 checkout 上驗過、確定不用回去改」就收**，
  不是「merge 完就收」，也不是「全部留到最後」。
  要回去修的時候從整合分支重開，拿到的是**合併後**的狀態，比舊子分支更適合改。
- **子 branch 一律不 push**，否則 GitHub 會累積一堆永遠不開 PR 的分支。
  例外只有三個：**換裝置、換人接手、過夜離開機器想要備份**；推了就在合併後當天
  `git push origin --delete`。⚠️ **不要拿「怕 worktree 被收掉弄丟」當理由** ——
  分支 ref 住在主 checkout 的 `.git/refs/heads/`，`worktree remove` 不刪分支也不刪 commit。
- **其他還在跑的 worktree 不要動。** 在 agent 做到一半改它的 base，
  它腦裡的檔案狀態會跟磁碟對不上。
