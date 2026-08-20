# Skill 放 .claude/skills，往外拉線而不是搬家

這個 repo 的 skill 有三個消費端：Slack 上的 backlog agent（`work-agent-deploy` 把整個目錄 read-only mount 進 container 的 `/home/node/.claude/skills`）、在這個 repo 裡開的 agent、以及在別的 repo 裡開的 agent。放在 `.claude/skills/` 讓前兩者不用任何額外設定就成立：那是 Claude Code 的 project level 正規位置，而 container 那份掛成 personal level，永遠載入且優先權最高。第三方 skill 用 `npx skills add <repo> -s <skill> -a claude-code --copy` 裝進同一個目錄，來源與 hash 記在 `skills-lock.json`，之後 `npx skills update -p` 更新。`--copy` 不能省：預設是 symlink 到 agent 目錄，指到 mount 範圍以外，在 container 內是斷的。

第三個消費端靠 `bin/sync-skills` 在 `~/.claude/skills/` 為每支 skill 建一條 symlink，而不是把整個目錄指過來。那個目錄是多來源共用的命名空間——2026-08-20 實測 66 個項目裡只有 6 個來自這裡，另外 60 個是指向 `~/.agents/skills/` 的連結（`npx skills -g` 裝的），Claude Code 同步 claude.ai 的 skill 也寫在同一層。整個目錄指向本 repo 會讓其他來源消失，並把別的工具的寫入導進版本控制裡。規則是 `~/.claude/skills/<name>` 一律是指過去的 symlink，同一層不放第二份實體檔案：personal 蓋過 project，同名的兩個不同檔案會讓本機和 bot 跑到不同版本而且沒有提示。

但「只留一份」不是跨層的規則，第三方 skill 在磁碟上刻意有兩份：`work-helper/.claude/skills/<name>`（記在 `skills-lock.json`，`npx skills update -p` 更新）和 `~/.agents/skills/<name>`（記在 `~/.agents/.skill-lock.json`，全域指令更新）。兩份都不能拿掉。repo 那份是 container 的唯一來源——`work-agent-deploy/compose.yaml:42` 只 mount `work-helper/.claude/skills`，指到 repo 外面的 symlink 在裡面是斷的，這也是第一段 `--copy` 不能省的同一件事。刪掉全域那份同樣沒用：lock 還記著它，下次全域更新會把實體目錄寫回來，或者直接寫進 `bin/sync-skills` 建的那條指向 repo 的 symlink，把別的工具的寫入導進版本控制——正是這篇不整個目錄指過來要避免的事。

所以要守的 invariant 不是「只有一份」，是「兩份不准跑掉」。`bin/sync-skills:40-48` 遇到同名實體目錄不覆蓋（`ln -sfn` 撞到實體目錄不會覆蓋，會把連結塞進那個目錄裡變成 `<name>/<name>`，而且不報錯），改成 `diff -rq` 比內容：一樣印 `same` 放過，不一樣印 `DRIFT` 並以非零結束。共存是設計，drift 才是這篇在意的那個沒有提示的錯。
