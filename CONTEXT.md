# work-helper

這個 repo 有兩條線。**待辦線**：PM 與授權使用者把待辦記在 Slack 的「Bug/需求總表」上，
`bin/slack-list` 讀寫它、並把處理進度回報回去。**日誌線**：`daily-worklog` 從 git commit
產出給主管看的工作日誌，不碰 Slack。下面是這兩條線上會混淆的詞 —— 混淆的代價實際發生過，
見 `docs/adr/`。

這個 repo 同時是完整 **skill catalog**：它列出 work-helper 可提供的 skills，但 catalog 不等於
permission。remote bot 的 OMO 試用採單一 container，直接掛載既有完整 catalog，保留既有
skill、MCP 與 plugin 設定；deployment registry／allowlist projection 是日後可選的發布控制，
不是這次試用的前置阻礙。具體決策見 [ADR-0014](docs/adr/0014-skill-catalog-uses-remote-allowlist-projection.md)。

## Language

**skill catalog**:
work-helper 所有可提供 skills 的目錄。它描述「有哪些」，不表示任何執行權限。

**deployment projection**:
未來若需要發布控制，從 skill catalog 選出要提供給特定 deployment 的 skills 投影；不是權限
本身。這次單 container 試用不要求先建立 projection。

**remote allowlist**:
未來 registry 可選的遠端發布名單。它不是這次單 container 試用的前置條件；試用可以掛載完整
catalog。allowlist 也不等於 runtime permission，真正的限制仍由 runtime gate 執行。

**待辦列**:
「Bug/需求總表」上的一列，一件事。由 `record_id`（`Rec…` 開頭）識別。
_Avoid_: item、單（「任務」是另一個東西，見下）

**item 留言串**:
掛在某一個待辦列底下的 Slack 對話串，PM 與開發者在這裡就那一件事來回。
Slack 原生提供，每一列在建立時就有一條，不需要也不能另外開。
_Avoid_: 討論串、回報串（這兩個曾經指「工具自己另開的那條」，那個做法已經廢除）

**原生 item thread context**:
deployment 提供的 `record_id`，以及能證明它屬於這張 List 原生留言串的 Slack runtime context。
`slack-list` 只接受這個範圍；它不是任意 OpenAB thread 的通用讀取器。沒有 context 時不能保證
artifact 或回報能回到原 thread。

**artifact**:
由 remote runtime 產生、要附回原生 item 留言串的 regular file。local CLI 保留既有副檔名；
remote mode 只接受 PNG、Markdown、HTML，HTML 必須明確指示。upload 與 thread post 都成功後
才刪除來源；失敗時保留來源。container cleanup 只清理 `/home/node/drafts` 內已達 24 小時的
regular artifact，不追 symlink，也不離開 root。

**發起者**:
明確要求 bot 建立待辦列的 Slack 使用者；真人直接在 List 建列時沒有另一個發起者。
_Avoid_: 建立者（bot 代建時，Slack 記錄的建立者是 bot）

**指派對象**:
負責處理待辦列的人，一列可以有多位。加入指派不代表接手回報或驗收。
_Avoid_: 回報對象、發起者

**回報對象**:
驗收時該被 `@`、正在等結果的人，一列至多一位，也可以不指定。
沒有明確設定時，真人建立的列是建立者，bot 代建的列是發起者。
_Avoid_: 指派對象（那是負責做的人，可能有多位）

**回報設定**:
替一列指定回報對象、恢復預設或明確設成不通知；最新一次設定生效。
_Avoid_: 指派、訂閱

**核准者**:
看過草稿、決定它可以變成任務的人。通常是發起偵察的開發者或 PM；核准草稿不等於負責實作。
_Avoid_: 負責人、回報對象（這三個角色可能是不同的人）

**任務**:
一張 GitHub issue，一件**會跨過今天**、需要正式紀錄的事。
由偵察寫成草稿、核准者看過之後才開成 issue（掛 `ready-for-agent`）、負責人接。
當天做得完的不開任務，草稿直接派工。
它的編號就是 slug，貫穿 branch、worktree、agent name。
_Avoid_: 單、任務單、ticket

**草稿**:
偵察查完現況寫出來的一份檔案（`drafts/` 底下，不進版控），內容等於一個任務的 body。
**消耗品** —— 核准者看完就決定它變成任務、還是直接派工做掉然後刪掉。
_Avoid_: 粗單、草稿單、待開的 issue

**指紋**:
GitHub issue 內文第一行那句指回來源待辦列的可見連結。
它是「這張 issue 對應哪一列」的唯一正本，用來擋重複開任務。
_Avoid_: 快取、對照表（那些是可以錯的副本，指紋不能錯）

**驗收**:
PM 確認一件事真的做好了。工具把該列狀態改成「PM確認中」並通知回報對象，
球就在 PM 身上；他在 item 留言串裡回。
_Avoid_: 完成、結案

**進度**:
還沒到驗收的中途回報。只留在 item 留言串裡，不 `@` 人、不改狀態。

**工作日誌**:
一天（或一週）的 git commit 翻譯成主管看得懂的交付內容，貼進公司表單。
唯一讀者是那張表單，所以**不落檔**、不進版控；讀者也不是 PM，跟待辦線的「回報」無關。
_Avoid_: 日報單、進度（那是待辦線給 PM 的中途回報）、交付報告（那是 `ready` 發的驗收報告）

**預定進度清單**:
工作日誌裡跨日沿用的那幾行 `[模組]` 子項，git 產不出來，所以存成一份檔案
（預設 `~/.claude/worklog-backlog.md`，不在任何 repo 裡）。寫日誌時讀它、只更新 ✅、定稿後寫回。
_Avoid_: backlog（這條線上「backlog」指的是 Slack 那張總表）、待辦（那是待辦列）
