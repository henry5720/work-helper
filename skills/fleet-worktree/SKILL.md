---
name: fleet-worktree
description: 接單 —— 把一張已發布的任務單（issue）開成隔離的 worktree，派一個長駐 agent 進去做完。當使用者說「派工 #1234」「接這張單」「開始做這張」「開 worktree 給這張」時使用；一張 issue 掛上 ready-for-agent 之後要動工時也用。
---

# 接單：一張任務單，一個 worktree，一個負責人

一張已發布的**任務單**（掛了 `ready-for-agent` 的 issue）＝ 一次接單。

**一個 slug 只准出現在一個 worktree，一個 worktree 只准有一個 agent。沒有例外。**

slug ＝ **issue 編號 + 短名**，它同時決定四樣東西：

| 東西 | 長什麼樣 |
| --- | --- |
| issue | `#1788` |
| branch | `fix/1788-spc-codegen` |
| worktree | herdr 自己配的路徑 |
| agent name | `fix-1788-spc-codegen` |

編號寫在 branch 名裡，所以**重複做同一件事會當場現形**。

> **為什麼這樣設計**：[`docs/fleet.md`](../../docs/fleet.md)。改規則改這份 SKILL.md，改判斷邊界改那份。

> 📁 **路徑假設**：`~/code/` 底下是兄弟目錄。這台機器不是這樣擺的話 `ls ~/code` 看一眼，找不到就問使用者。

---

## 1. 從整合分支開 worktree

一個模組一條長命的整合分支（例如 `fix/inventory`），所有 worktree 從它開、做完 merge 回它。

```bash
SLUG=fix-1788-spc-codegen
ISSUE=1788

PANE=$(herdr worktree create \
  --base <整合分支> \
  --branch "fix/1788-spc-codegen" \
  --label "$SLUG" --no-focus \
  | jq -r '.result.root_pane.pane_id')
```

⚠️ Termux PRoot 不一定有 `jq`，那邊用 `python3 -c 'import sys,json; print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])'`。

**完成條件**：`$PANE` 有值。

## 2. Bootstrap 三行

```bash
# 依賴（讓它能自我驗證）
<套件管理器> install --frozen-lockfile

# issue 快照（省 context）
gh issue view $ISSUE --comments > .claude/handoff.md

# 身分卡（活過 compact）
cat > CLAUDE.local.md <<EOF
你 own issue #$ISSUE，slug 是 \`$SLUG\`。
權威是 \`gh issue view $ISSUE --comments\`；\`.claude/handoff.md\` 只是 bootstrap 當時的快照。
compact 之後、或我叫你重讀時，回去讀 issue 本身。
EOF
```

三行各自為什麼不能省：

| | 為什麼 |
| --- | --- |
| 裝依賴 | 沒有 `node_modules` 就沒有測試、lint、typecheck，agent 只能盲寫。hardlink 的套件管理器（pnpm）實體只有一份，幾秒的事 |
| issue 快照 | agent 讀本地檔省 context |
| 身分卡 | project-root 的 `CLAUDE.md` / `CLAUDE.local.md` 在 `/compact` 之後會被重新讀入。**沒有它，agent 失憶後會回頭讀那份過期的快照** |

⚠️ **`CLAUDE.local.md` 要在目標 repo 的 `.gitignore` 裡**（`git check-ignore -v CLAUDE.local.md` 要命中）。沒加它會出現在 `git status`，把偵察那輪的守門訊號汙染掉。

⚠️ **不要複製 `.env.local` 過去。** 測試 / lint / typecheck 都不碰 env，而複製出去的秘密檔副本會靜靜過期，散越多份越難清。

**完成條件**：`git status --short` 只有你預期的東西（理想是空的）。

## 3. 起 agent，給它 name

```bash
herdr agent start "$SLUG" --kind claude --pane "$PANE"
```

**一定要給 name。** 手打 `claude` 起來的 agent 在 `herdr agent list` 裡沒有 `name`，只能用 `wR:pH` 這種 pane id 當 target —— 你記不住，等於失去「不切畫面就能丟訊息」的能力。已經手打起來的用 `herdr agent rename <pane-id> <slug>` 補。

⚠️ name 必須符合 `[a-z][a-z0-9_-]{0,31}`，**不接受大寫**。而且 agent 退出或被取代時 name 會清掉，不是永久的。

**完成條件**：`herdr agent list` 裡看得到 `$SLUG`。

## 4. 派工：先要計畫，不要先要 code

```bash
herdr agent prompt "$SLUG" "讀 .claude/handoff.md，你 own issue #$ISSUE。
先把計畫 gh issue comment 回 issue，然後停 —— 這一輪不要改任何檔案。"
```

**短到不像話是對的。** 一長就代表你在替負責人想它該怎麼做，而該講的都在 issue 裡了。

**完成條件**：issue 上有一份計畫，而且它**停了**。不是「開始動工」—— 動工等下一步。
它也不該回頭問背景（問了就是 issue 寫得不夠，把它問的那句記下來，那是 issue 模板下一版要補的欄位）。

## 5. 使用者批次看計畫，過了才放行

```bash
herdr agent prompt "$SLUG" "計畫可以，開始做"
```

**計畫寫進 issue、不是停在 pane 裡等人按** —— 這樣 N 張單的計畫可以一次看完，
跟看 N 張任務單是同一個動作。互動式核可會讓 N 個 agent 各自隨機打斷使用者，
那正是這整套要避開的東西。

看的是「**有沒有理解對**」，不是「這是最好的做法嗎」。不對就直接在 comment 裡改方向，再叫它重讀。

⚠️ **要補東西補在 issue，不要改 `handoff.md`。** handoff 是快照、issue 是權威；改快照會讓兩邊分岔，而三天後回頭看只有 issue。`gh issue comment` 之後叫它重讀：

```bash
herdr agent prompt "$SLUG" "issue 有更新，回去讀 gh issue view $ISSUE --comments"
```

**完成條件**：agent 開始動工。

---

## 怎麼知道它需要人了

兩個狀態都表示「該你了」：`blocked`（在等權限核可）、`idle`（話講完了，停在輸入提示）。
**兩個都要等，只等一個會漏**：

```bash
herdr agent wait "$SLUG" --until idle --until blocked
```

這行會擋在那裡直到那個 agent 需要人 —— 不用輪詢、不用盯畫面。後面接 `herdr notification show` 發通知。

介入有兩個入口，都走 socket、**跟你人在哪個 pane 無關**，而且都是接續原本的對話不是重開：

```bash
herdr agent prompt "$SLUG" "..."   # 不切畫面丟一句進去（日常用這個）
herdr agent attach "$SLUG"         # 切過去自己打（要來回討論才用）
```

⚠️ `prompt` 不要加 `--wait`，那會擋住你的 terminal。丟完就回去做別的事。

## 驗收：兩道關

| 關 | 誰做 | 過關條件 |
| --- | --- | --- |
| 第一道 | worktree 裡，agent 自己 | 相關測試過、lint 過（只餵改動的檔案）、typecheck 過，而且 `git diff --name-only <整合分支>..HEAD` 的檔案**都在 issue 講的範圍內** |
| 第二道 | 整合分支 | **驗收**：任務單上寫的「怎樣算解完」達成了沒。有 e2e 覆蓋就跑 e2e，UI/UX 的主觀判斷才需要人看 |

**dev server 只開一個，就在整合分支那份 checkout。** worktree 裡不開 —— 驗收要人看的那部分是使用者的注意力，本來就一次一件。

### merge 與收尾

```bash
git -C <repo> merge --no-ff <slug>
```

`--no-ff` 的理由是整合測試掛掉時：一顆 merge commit 一個工作單位，`git revert -m 1 <merge-sha>` 就能把整合分支打回乾淨，而那條 worktree branch 完全沒被動到。

**收尾順序**：merge → 整合測試過 → 關 issue → **最後才** `herdr worktree remove --workspace <id>`。整合測試沒過你要回去修，先 remove 掉就得重開重裝。

⚠️ **測到問題回原 worktree 改，不要 revert。** merge 沒動到那條 branch、pane 裡的 process 還活著、context 都在：

```bash
herdr agent prompt "$SLUG" "整合測試發現：<現象>"
```

改完再 merge 一次，同一條 branch 長出第二顆 merge commit，正常。revert 掉一顆 merge commit 之後再 merge 同一條 branch，git 會認為那些 commit 併過了、內容不會回來。

⚠️ **子 branch 一律不 push。** 它們是本地的工作單位。只有整合分支推，最後由它開一個 PR。

⚠️ **其他還在跑的 worktree 不要動。** 等它各自跑完、你要給它下一件事之前，才在它裡面 merge 整合分支 —— 不要在 agent 做到一半改它的 base，它腦裡的檔案狀態會跟磁碟對不上。
