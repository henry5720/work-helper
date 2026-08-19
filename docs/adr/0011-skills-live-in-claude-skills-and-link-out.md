# Skill 放 .claude/skills，往外拉線而不是搬家

這個 repo 的 skill 有三個消費端：Slack 上的 backlog agent（`work-agent-deploy` 把整個目錄 read-only mount 進 container 的 `/home/node/.claude/skills`）、在這個 repo 裡開的 agent、以及在別的 repo 裡開的 agent。放在 `.claude/skills/` 讓前兩者不用任何額外設定就成立：那是 Claude Code 的 project level 正規位置，而 container 那份掛成 personal level，永遠載入且優先權最高。第三方 skill 用 `npx skills add <repo> -s <skill> -a claude-code --copy` 裝進同一個目錄，來源與 hash 記在 `skills-lock.json`，之後 `npx skills update -p` 更新。`--copy` 不能省：預設是 symlink 到 agent 目錄，指到 mount 範圍以外，在 container 內是斷的。

第三個消費端靠 `bin/sync-skills` 在 `~/.claude/skills/` 為每支 skill 建一條 symlink，而不是把整個目錄指過來。那個目錄是多來源共用的命名空間——目前 40 個項目裡只有 6 個來自這裡，32 個來自 `npx skills -g`，還有直接放進去的實體目錄，Claude Code 同步 claude.ai 的 skill 也寫在同一層。整個目錄指向本 repo 會讓其他來源消失，並把別的工具的寫入導進版本控制裡。規則是一個 skill 名稱在磁碟上只留一份檔案，`~/.claude/skills/<name>` 一律是指過去的 symlink：personal 蓋過 project，同名的兩個不同檔案會讓本機和 bot 跑到不同版本而且沒有提示。
