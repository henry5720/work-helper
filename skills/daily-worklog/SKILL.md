---
name: daily-worklog
description: 從 git commit 產生給主管看的每日工作日誌（繁中）。當使用者說「寫日誌」「日報」「工作日誌」「把今天的 commit 整理給主管」「worklog」時使用。
---

# 每日工作日誌產生器

把一天的 git commit 翻譯成主管看得懂的工作日誌。

**這不是 `git log` 美化。** 主管不看 commit message，他看的是「做出了什麼、對誰有用、卡在哪」。
你的工作是翻譯，不是搬運。

---

## 🚫 先講會做壞的三件事

1. **只讀 `%s`（commit 標題）就開始寫** —— 標題只有 8 個字，寫出來的日誌會是
   「修好 tooltip」這種主管看不出價值的句子。真正的內容在 **commit body (`%b`)** 裡。
2. **不加 `--all`** —— 當天的 commit 幾乎都在 feature branch 上，站在 `main` 跑 `git log`
   會漏掉一半以上。這是實測踩過的坑。
3. **git 沒有的東西自己編** —— 上下班時間、開會、code review 別人的 PR、口頭討論、
   還沒 commit 的調查，git 全都看不到。**缺的就問，不要補一個看起來合理的數字。**

---

## 📋 步驟

### 1. 決定範圍

- **日期**：使用者沒說就是今天。日誌檔名和標題用這個日期。
- **author**：`git config user.name` 拿到（例：`henry`）。
  ⚠️ 同一個人可能有多個 git 身分（`henry` / `henry5720` / GitHub noreply email）。
  `--author=henry` 是 substring 比對，剛好三種都涵蓋，所以**用名字不要用完整 email**。
- **repo**：預設掃 `~/code/` 底下所有 repo，不要只看當前目錄。
  一天的工作常常散在 frontend + backend + 文件 repo。

### 2. 抓出當天的 commit

掃所有 repo，找出哪幾個有當天的 commit：

```bash
DAY=2026-08-11; NEXT=2026-08-12; WHO=henry
for d in ~/code/*/; do
  [ -d "$d/.git" ] || continue
  n=$(git -C "$d" log --all --author="$WHO" --since="$DAY 00:00" --until="$NEXT 00:00" --oneline 2>/dev/null | wc -l)
  [ "$n" -gt 0 ] && echo "$n  $d"
done
```

然後對有 commit 的 repo，抓**完整內容**（重點是 `%b`，不是只有 `%s`）：

```bash
git -C <repo> log --all --author="$WHO" --since="$DAY 00:00" --until="$NEXT 00:00" \
  --reverse --date=format:"%H:%M" \
  --format="=== %h %ad%n%s%n%n%b%n"
```

搭配檔案異動規模（判斷「這件事有多大」用的）：

```bash
git -C <repo> log --all --author="$WHO" --since="$DAY 00:00" --until="$NEXT 00:00" \
  --no-merges --format="=== %h %s" --stat
```

### 3. 算出「提交數 / PR 數」

主管日誌開頭那句「N 筆提交 / M 個 PR」要這樣算，不要用總數：

```bash
# 提交數：排除 merge commit
git -C <repo> log --all --author="$WHO" --since="$DAY 00:00" --until="$NEXT 00:00" --no-merges --oneline | wc -l

# PR 數 + 編號：只看 merge commit
git -C <repo> log --all --author="$WHO" --since="$DAY 00:00" --until="$NEXT 00:00" --merges --format="%s"
# → "Merge pull request #1737 from ShuChenAI/fix/forms-table-header-align"
```

實測（2026-08-11）：14 個 commit = 10 筆提交 + 4 個 merge → 日誌寫「10 筆提交 / 4 個 PR」。

> merge commit 不算「做了幾件事」，但它是**唯一能拿到 PR 編號**的地方，兩個都要抓。

### 4. 補 git 看不到的部分（可選，有 `gh` 才做）

commit body 沒交代清楚時，去看 PR 描述和相關 issue：

```bash
gh pr view 1737 --json title,body,files --jq '.title, .body'
gh issue list --author "@me" --state all --search "created:$DAY OR updated:$DAY"
```

commit 有動到 ADR / 規格文件時，**直接讀那份 md** —— 設計決策的理由都在裡面，
比 commit body 更完整。

### 5. 翻譯成主管語言

這是整個流程的核心。逐條 commit 問自己：**「這件事修好之後，使用者少了什麼麻煩？」**

| 原始 commit | ❌ 搬運 | ✅ 翻譯 |
|---|---|---|
| `fix(chat/forms): tooltip for every truncated column header` | 修好表頭 tooltip | 長欄名被截斷時滑過去看完整名稱 —— 原本只有部分欄位有效（必填欄位名後面那顆紅星讓程式抓不到文字），現在必填／非必填 × 排序／批量編輯四種狀況行為一致，並補 4 項自動化測試 |
| `chore(config): untrack agent artifacts, ignore output dirs` | 清理 gitignore | 清掉 20 個被誤上傳到版控的一次性產物（PNG／Excel／報表，約 3.3MB），並補上忽略規則，避免下次又被帶進來 |
| `feat(review): 審核授權設定` | 新增審核授權功能 | 定案七項設計決定，並查證出三件會影響做法的事：現成權限畫面不能重用、後端沒有「改角色」動作、三個模組的授權畫面該共用的是零件不是整個畫面 |

翻譯守則：

- **講白話**，術語能換就換（「TanStack Query 快取失效」→「切換後資料沒更新」）。
  但**專有名詞保留**：模組名、PR 編號、issue 編號。
- **帶上實測數字**。commit body 裡的「錯位 0px」「1051 個檔案」「3.3MB」「4 項測試」
  是日誌最有說服力的部分，一定要撈出來。
- **不要每個 commit 一條**。同一件事的多個 commit 要合併成一條；
  順手改的 lint / format / rename 直接不寫。
- **卡住的、有風險的要寫出來**，用 ⚠️ 標。主管最怕的是事後才知道。
  例：「把權限發給職級 3 以下目前不會生效，缺口在後端（已開單 backend#902）」。

### 6. 排版輸出

固定用這個格式（`✅` 已完成、`⚠️` 風險或限制、`📝` 進行中）：

```markdown
日期：MMDD
上班時間：HHMM
下班時間：HHMM

▪️本日預定進度與時間（✅為今日已完成）

💻 <大分類，例：系統開發（TeamSync 前端，10 筆提交 / 4 個 PR 併入 dev）>

<事情一的名字（PR #1737）>

- ✅ <做了什麼、對使用者的意義、實測數字>
- ✅ <...>

<事情二的名字（PR #1736）>

- ✅ <...>
- ⚠️ <風險或已知限制>

▪️新增或調整工作事項（無則免填）

📝 <進行中設計（今日完成調查與定案，尚未進 PR）>

- ✅ <...>
- ⚠️ <...>
```

### 7. 收尾一定要問

git 抓不到、**必須跟使用者確認**的：

- 上班 / 下班時間
- 有沒有開會、教育訓練、支援別人 debug
- 有沒有 review 別人的 PR（那不會是自己的 commit）
- 有沒有「今天想了很久但還沒 commit」的調查
- 有沒有不想寫進日誌的內容

**問完再定稿。** 不要先送一份有空白欄位的版本。

---

## 💾 存檔

產出存到 `~/code/work-docs/docs/logs/worklog/`：

- 日報：`YYYY-MM-DD_日報.md`
- 週報：`YYYY-MM-DD_MMDD_本週工作內容.md`（沿用既有檔名慣例）

週報只是把範圍從一天拉成一週，多做兩件事：
開頭加**一句話總結**，結尾加**時間分佈表**（依 repo / 模組估工時）。

---

## 🕳️ 已知陷阱

| 陷阱 | 症狀 | 解法 |
|---|---|---|
| 沒加 `--all` | commit 數量明顯偏少 | 一律加 `--all` |
| 用 email 當 `--author` | 漏掉 GitHub noreply 身分的 commit | 用名字做 substring 比對 |
| 把 merge commit 算進提交數 | 數字虛胖 | 提交數用 `--no-merges`，PR 用 `--merges` |
| 只讀 `%s` | 日誌乾癟、沒有數字 | 一律撈 `%b` |
| 只看當前 repo | 漏掉後端 / 文件 repo | 掃 `~/code/*/` |
| 跨午夜的 commit | 邊界抓錯 | `--since`／`--until` 是本地時間；深夜 commit 先問使用者算哪一天 |
| commit body 是英文 | 日誌混語言 | 日誌一律繁中，技術名詞保留英文 |
