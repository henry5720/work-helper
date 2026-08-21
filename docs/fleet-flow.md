# Fleet：TeamSync 控制面交接規則

這份是 work-helper 的 Fleet 唯一正本。Fleet 只管待辦、草稿、issue、slug、scope 與
handoff 的資料和決策交接，不處理 runtime。

## 責任表與流程

| 角色 | 只負責什麼 |
| --- | --- |
| **remote backlog bot** | 讀 Slack 待辦與 item 留言串，產出草稿；交稿後停止 |
| **Fleet dispatcher** | 集中查重、決定顆粒度、比對 scope、建立 issue／label、寫 handoff metadata |
| **handoff 接收方** | 接收已完成的 Fleet handoff |
| **一個任務** | 一個 slug、一個 primary worktree、一個 root agent |

流程：**remote backlog bot → Fleet dispatcher（目前人手動）→ 指定 host 的 handoff → 一個
slug 的 primary worktree／root agent。**

remote backlog bot 只交草稿，不接單、不發布 issue、不選 host。Fleet dispatcher 是 TeamSync
的集中入口，不把 runtime 動作塞進 `bin/fleet`。

## 現況與範圍

- work-helper 是共用 `bin/` 與 `.claude/skills/` 的正本，只描述自己的工具、skill、Slack 待辦
  資料與 Fleet handoff 規則。
- 目前 `bin/fleet` 尚未實作；未來若加入，只能做 TeamSync adapter：草稿、issue、label、
  scope、host assignment 與 handoff metadata。
- `bin/fleet` 不建立或管理任何 runtime；它只處理 TeamSync handoff 資料。

## TeamSync handoff

### Slack 待辦列 → 草稿

- Slack 待辦列和它的原生 item 留言串是需求來源；`敘述` 不足時一定要讀留言串。
- 草稿是消耗品，格式照目標 repo 的 issue 規範；至少要有現況、驗收條件、方向與改動範圍。
- 草稿只交一行路徑給 dispatcher。它不是第二套 backlog，也不是 issue 的替代快取。

### dispatcher 集中決策

dispatcher 發布前必須集中完成：

1. 讀草稿和 Slack item 留言串，確認核准者已看過。
2. 用 Slack `record_id` 查 issue 指紋；衍生任務用母 issue 編號查重。
3. 決定一列要拆成幾個任務；不能讓平行偵察各自拆／合。
4. 比對每份草稿的改動範圍；有 scope 交集就合併或排隊。
5. 決定是否建立 issue，並在需要時套用正確 label。
6. 把 issue、slug、來源指紋、scope、指定 host 與 handoff metadata 一起交出去。

issue 是跨天任務的 backlog 正本；Slack 待辦列仍是 PM 的介面。當天能完成的工作不必建立
issue，但仍要沿用同一個 handoff 與 slug 規則。相關理由見
[ADR-0001](./adr/0001-report-into-the-native-item-comment-thread.md)、
[ADR-0003](./adr/0003-issues-are-the-backlog-not-markdown-in-the-repo.md)、
[ADR-0006](./adr/0006-recon-writes-a-draft-not-an-issue.md)、
[ADR-0008](./adr/0008-same-day-work-skips-the-issue.md) 與
[ADR-0009](./adr/0009-authorized-reviewers-approve-drafts.md)。

## 不變量

- 一個 slug 只能有一個 primary worktree 和一個 root agent；不能因為不同角色或不同環境
  再開第二份。見 [ADR-0002](./adr/0002-one-slug-one-worktree-one-agent.md)。
- handoff 必須能辨識 issue、slug、來源 record、scope、指定 host 與 primary worktree／root
  agent；這些是資料欄位。
- 未來有多台 writable host 時，必須先有單一 dispatcher 和 machine-readable host claim，
  再把任務交給一台 host；不能讓各 host 各自掃同一批 `ready-for-agent`。

## 驗證邊界

本文件只驗證資料是否完整、決策是否集中、handoff 是否唯一。

搭配 [`fleet-dry-run-checklist.md`](./fleet-dry-run-checklist.md) 試跑。
