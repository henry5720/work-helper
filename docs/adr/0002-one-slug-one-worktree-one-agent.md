# 一個 slug 只出現在一個 worktree，一個 worktree 只有一個 agent

「一件事」這個單位必須落在檔案上，不能只在腦裡。slug ＝ **issue 編號 + 短名**，
它同時決定 issue（`#1769`）、branch（`fix/1769-export-warehouse-only`）、
worktree 路徑、herdr agent name。編號寫在 branch 名裡，所以重複做同一件事會當場現形。

## 為什麼要有這條

第一版沒有。結果同一份改動被 commit 進兩條 branch —— 兩個 agent 共用一個 worktree，
兩份 context 都在人腦裡搬，而人腦記不住哪個 agent 做到哪。

## 連帶的三個結果

- **偵察不能開 worktree**，因為 worktree 要 branch 名 → 要 issue 編號 → issue 還沒開。
  這是循環，不是成本問題。見 ADR-0006。
- **顆粒度必須在開 issue 那一刻決定。** 「合成一個還是拆兩個」定的是 slug，
  接單之後才想改就來不及了。這是 `⚠️ 範圍未定` 要在發布前談的原因。
- **負責人做到一半發現新問題，只能開 issue、不能自己接。** 自己接就是一個 worktree 兩個 slug。

## 代價

worktree 開起來要裝環境（`node_modules`、`.env`），所以「順手做一下」的成本變高。
接受這點，因為「順手」正是第一版出事的那個動作。
