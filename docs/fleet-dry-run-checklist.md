# Fleet handoff 試跑清單

> 這份只驗證 Fleet handoff 的資料與決策交接。
> 規則見 [fleet-flow.md](./fleet-flow.md)。

## 這輪設定

日期／目標 repo：　Slack record_id：　issue／slug：　指定 host：

## 1. 來源完整

- [ ] 讀了 Slack 待辦列的完整內容。
- [ ] 讀了該列原生 item 留言串；留言串才是規格來源。
- [ ] 分流沒有自行猜需求或改變待辦顆粒度。

## 2. 草稿交接

- [ ] remote backlog bot 只交一行草稿路徑，沒有接單或發布 issue。
- [ ] 草稿照目標 repo 的 issue 規範。
- [ ] 草稿包含現況、驗收條件、方向與具體改動範圍。
- [ ] 草稿是單一問題，不是多件事拼成的 spec。

草稿路徑：

## 3. dispatcher 決策

- [ ] 核准者看過草稿。
- [ ] 用 Slack `record_id` 查過既有 issue；衍生任務用母 issue 編號查重。
- [ ] 顆粒度已決定，沒有讓不同偵察各自拆／合。
- [ ] 已比對「要改哪些檔案」的 scope；交集已合併或排隊。
- [ ] 已決定當天完成不開 issue，或跨天任務建立 issue。
- [ ] issue／label 已按決策建立或更新。

## 4. handoff 完整

- [ ] handoff metadata 可辨識 issue、slug、來源 record、scope、指定 host。
- [ ] handoff metadata 可辨識 primary worktree／root agent 的唯一性。
- [ ] 同一 slug 沒有第二份 primary worktree 或 root agent。
- [ ] 未來多 host 的流程已預留單一 dispatcher 與 machine-readable host claim。

- 缺少的來源資料：
- 查重／顆粒度／scope 結論：
- handoff 缺口：

跑完後只把 control-plane 的修正寫回 [fleet-flow.md](./fleet-flow.md)，清空本表再用。
