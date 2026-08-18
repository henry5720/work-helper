# 用 `merge --no-ff` 併進一條長命的整合分支

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
- **worktree 最後才收。** 整合測試沒過要回去修，先收掉就得重開重裝。
- **子 branch 一律不 push**，否則 GitHub 會累積一堆永遠不開 PR 的分支。
- **其他還在跑的 worktree 不要動。** 在 agent 做到一半改它的 base，
  它腦裡的檔案狀態會跟磁碟對不上。
