# Skill catalog 可完整掛載；registry projection 是日後可選的發布控制

work-helper 是完整 **skill catalog**。這次 remote bot 的 OMO 試用採單一 container，直接掛載
既有 catalog，並保留既有 skill、MCP 與 plugin 設定。未來若 deployment 數量、發布流程或
變更審核需要更窄的集合，再導入 registry 的 allowlist projection；它不是這次試用能否開始的
前置條件，也不是 permission。

## 定案

- 這次試用以單一 remote container 為邊界，掛載完整 catalog；不先做 remote allowlist
  projection，也不因 projection 缺席而阻擋試用。
- 保留既有 skill、MCP 與 plugin 設定；本次不做 allowlist projection 的硬切換，也不實作獨立
  broker。
- registry 是日後可選的發布控制。若導入 projection，每個被投影的 skill 應記錄來源、version、
  hash、類型、side effect、依賴與可用 runtime。
- catalog 與 registry 都是可見性／發布範圍描述，不是 permission。真正的權限邊界是 runtime
  gate；掛載完整 catalog 也不繞過 runtime gate。

## 為什麼

catalog 的責任是完整收錄可用內容；單一 container 試用的目標是先驗證 OMO 與既有設定能否
一起工作，不應為了尚未需要的多 deployment 發布控制先增加阻礙。完整掛載不代表所有 skill
都能執行，runtime gate 仍是 permission 邊界。

未來導入 registry projection 時，registry 會讓遠端集合成為可追蹤的發布決定；來源、version、
hash 與 skill 的類型、side effect、依賴及 runtime 記錄，則讓每個遠端項目可以被辨識和檢查。
在那之前，完整 catalog 可直接掛載，且不需要為此建立獨立 broker。
