# Skill 放 `.claude/skills`，以實體內容作為正本

本 repo 管理的 agent skill 正本放在 `.claude/skills/`。第三方 skill 用
`npx skills add <repo> -s <skill> -a claude-code --copy` 放入，來源與 hash 由
`skills-lock.json` 記錄，更新用 `npx skills update -p`。

`--copy` 不能省：只攜帶 `.claude/skills/` 的執行環境可能讀不到 repo 外的 symlink 目標。
`bin/sync-skills` 再把每支 skill 個別連到全域 skill 目錄，不把整個目錄替換掉，避免覆蓋
其他來源；既有實體目錄則比對內容，不直接覆蓋。

## 不變量

- `.claude/skills/<name>/SKILL.md` 是本 repo 的 skill 正本。
- 同一支 skill 的內容不一致才算 drift；共存的來源本身不是錯。
