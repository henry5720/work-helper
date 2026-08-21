# work-helper

這個 repo 放兩樣東西：`bin/` 底下自己寫的工具，和 `.claude/skills/` 底下 agent 讀的規矩。
它沒有產品程式碼，所以「改壞」的形式幾乎都是**工具會了一件事、說明還說它不會**。

## 先讀

1. `CONTEXT.md`：兩條線（待辦線、日誌線）與會混淆的詞。
2. 要動哪支工具，就讀它對應的 `.claude/skills/<name>/SKILL.md`。
3. `docs/adr/`：不容易從程式看懂的決策理由。

## 唯一正本

| 要改什麼 | 正本 |
|---|---|
| 領域詞彙 | `CONTEXT.md` |
| 指令實際行為、參數、錯誤訊息 | `bin/<tool>` |
| agent 用這支工具的規矩與判斷 | `.claude/skills/<name>/SKILL.md` |
| 第三方 skill 的來源與版本 | `skills-lock.json`（用 `npx skills update -p`，不要手改） |
| 人看的入口與安裝 | `README.md` |
| 決策理由 | `docs/adr/` |

## 修改規則

- **動了 `bin/` 的能力，同一個 commit 要改對應的 SKILL.md。** 工具多一個指令而 skill 沒寫，
  agent 就會繼續回「這件事辦不到」；反過來 skill 寫了工具沒有，agent 會去跑不存在的指令。
  兩種都發生過（`slack-list users` 上線後，SKILL.md 有兩處還寫著「app 沒有 `users:read`」）。
- **README 不列第二份指令清單。** 完整清單只在 SKILL.md，README 給一句話入口再連過去。
  兩份清單一定會有一份先腐爛。
- **不要把只有某台機器成立的路徑寫進工具或 skill。** `~/code`、`~/code/work-docs` 這種是
  個人習慣，不是前提；預設值要對別人也成立，需要縮小範圍讓使用者自己給。
- 不提交 token、`.env`、`drafts/` 底下的草稿。
- 沒有使用者明確要求，不 commit、不 push。

## 驗證

```bash
bash -n bin/sync-skills                                        # bash 那支
python3 -m py_compile bin/slack-list && rm -rf bin/__pycache__  # python 那支
./bin/slack-list env              # 有 .env 時：設定讀得到嗎
./bin/slack-list count            # 有 token 時：真的打得到 Slack
```

改 `bin/slack-list` 的輸出格式或段落檢查時，跑一次真的指令看它罵什麼，
不要只讀程式判斷。
