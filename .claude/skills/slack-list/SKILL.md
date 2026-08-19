---
name: slack-list
description: 讀寫 Slack「Bug/需求總表」上的待辦，並在該列的留言串回報進度。當使用者問「PM 有什麼待辦」「新增待辦」「Bug/需求總表」「PM 有沒有回我」時使用；要建立或指派 Slack list 待辦、設定回報對象、加回覆／留言／回報進度／通知 PM 驗收時也用。
---

# PM 的待辦表

PM（chieh）與授權使用者把 bug 與需求記在 Slack 的一張 List：**Bug/需求總表**。
讀它、看懂它、把處理進度回報回去，都走 `~/code/work-helper/bin/slack-list`。

**不要自己組 curl，也不要用 Slack MCP 做這件事。** 腳本已經處理翻頁、
錯誤翻譯、欄位對應、討論串對應。繞過它就是重寫一次，而且會寫錯。

> 📁 **路徑假設**：這份文件裡的 `~/code/xxx` 假設所有 repo 都是 `~/code/` 底下的兄弟目錄
> （`work-helper`、`teamsync-frontend`、`teamsync-backend`、`work-docs`）。
> **這台機器不是這樣擺的話，`ls ~/code` 看一眼；還是找不到就問使用者，不要猜。**
> 換過機器（例如手機的 Termux）路徑一定不一樣。

---

## 🚫 先講會做壞的三件事

1. **拿 `敘述` 欄當完整規格** —— 很多列的 `敘述` 只有「功能...」這種被截斷的字，
   真正的規格在那一列的**留言串**裡。`slack-list replies Rec0B…` 就讀得到，
   **派工或開 issue 之前一定要先讀**。實際發生過：PM 早就在留言裡裁決了，
   而我們照 `敘述` 開 issue，等於重問一次他已經答過的事。
   讀完還是不足才說「這列規格不夠」，**不要自己補一個看起來合理的需求**。
2. **假設一列 = 一張 issue** —— 實際看過的例子裡，一列的留言串包含 3 個獨立問題
   （UX 疑慮 / bug / 需求變更）。顆粒度還沒定案，不要自作主張拆或合。
3. **改 `狀態` 欄** —— 那是 PM 在維護的。唯一的例外是 `ready` 指令，
   它只會寫「PM確認中」這一個值。其他狀態一律不要碰。

---

## 📋 讀

```bash
cd ~/code/work-helper
./bin/slack-list rows                      # 一行一列，只印未完成
./bin/slack-list rows 庫存                  # 關鍵字比對整列文字，不分欄位
./bin/slack-list rows --assignee U0B…       # 指派給某人
./bin/slack-list rows --created-by U0B…     # 某人建立的列
./bin/slack-list rows --status PM確認        # 狀態欄子字串比對
./bin/slack-list rows --assignee U0B… --status 前端完成   # 條件可疊加
./bin/slack-list rows --all                # 連已完成的也印
./bin/slack-list mine                      # local 專用：等同 --assignee 自己
./bin/slack-list json                      # 壓平後的 JSON，要程式處理時用
./bin/slack-list fields                    # 不確定欄位叫什麼的時候先跑這個
```

`todo`／`assigned` 是 `rows` 的舊別名，還能用，但新的查詢一律用 `rows` —— 條件加在 flag 上，
不用再記哪個子指令支援哪個條件。

⚠️ **預設只印未完成的列。** 全表 409 列裡 234 列已完成；未完成是 3 萬字，全表是 9 萬字，
而那些字會整包進你的 context。**所以找不到一件事的時候，加 `--all` 再找一次才算找過**，
不要直接回「表上沒有這件事」—— 它很可能只是已完成。每次印完 stderr 都會告訴你這是哪一種視角。

`--status` 沒比對到任何列時，stderr 會列出這個範圍裡實際出現過的狀態值。空結果配上那份清單，
才分得出是「真的沒有」還是「你把狀態值打錯了」。狀態值是 PM 在表上自由維護的，不要寫死。

從 terminal/local agent問「我身上有什麼事」「跟 X 有關的」用 `mine`。
從 OpenAB 回應 Slack 訊息時，「我」是 `openab.sender.v1.sender_id`，用
`rows --assignee <sender_id> [關鍵字]`。不要用共享環境的 `SLACK_MY_USER_ID`，也不要自己撈
`json` 再土炮過濾。

每一列開頭的 `[Rec0B…]` 就是 record ID，回報時要用。

跑不動時先 `./bin/slack-list env`（確認 `.env` 讀到了）再 `count`（確認通得到）。
`.env` 沒設定會直接報哪個變數缺，照 `work-helper/README.md` 設定。

OpenAB 每則訊息會附 `openab.sender.v1` JSON。人在 item 留言串直接 `@bot` 時，用裡面的
`channel_id` 和 `thread_id` 反查待辦列，不要叫人再貼 record ID：

```bash
./bin/slack-list context --channel <channel_id> --thread-ts <thread_id>
```

## ➕ 建立待辦

`add` 是 single-writer command，只由 OpenAB backlog agent執行。Local agent不要跑 `add`；local與
遠端不共享process lock，同時查重後可能各建一列。其他讀取、`reporter`、`progress`、`ready`
仍照各自權限在local使用。

只有使用者明確要求「新增／建立待辦」才寫入。使用者明確給標題時直接建立；若要從一大段話
濃縮標題或敘述，先把準備寫入的內容貼出來確認。到期日按 `Asia/Taipei` 換成實際
`YYYY-MM-DD`，回覆時也顯示該日期；沒把握就問，不要猜。

OpenAB 一律把當次 `sender_id` 同時傳給 `--assignee` 與 `--requested-by`：

```bash
./bin/slack-list add \
  --title "<使用者明確給出或已確認的標題>" \
  --description "<選填>" \
  --due YYYY-MM-DD \
  --assignee <openab.sender.v1.sender_id> \
  --requested-by <openab.sender.v1.sender_id> \
  --source-channel <openab.sender.v1.channel_id> \
  --source-thread <openab.sender.v1.thread_id>
```

使用者明確說「回報給 @某人」時，從 Slack mention 取可靠的 `U…` ID，加
`--report-to U…`。說「不要通知任何人」才加 `--no-reporter`。不能用顯示名稱猜 ID，
app 沒有 `users:read`。沒特別說時預設回報給 sender。

`add` 會自行處理精確同名：active列存在時不建第二列，而是把 sender 追加到 assignees，
並補一則再次回報的來源；原本就有 sender 時只補來源。既有列在「PM確認中」時不改指派，
只回既有連結。使用者確認是復發或另一件事後，才用同一組參數加 `--force`。
命中既有列時保留原回報對象，`add` 的 `--report-to` / `--no-reporter` 不套用；使用者看過合併結果後
仍要改，才另跑 `reporter`。

從既有 item 留言串要求新增時，**即使標題不同也先顯示目前待辦與準備新增的內容，確認是另一件事**。
腳本也會擋下第一次呼叫；確認後才加 `--force`。不要為了省一次對話直接略過。

成功後只回新增／合併結果、實際到期日及 deep link。若工具說列已建立但來源／回報設定失敗，
照實回報；不要重跑 `add`，否則可能建出重複列。若是「建立結果不明」，也先到List搜尋同名列，
不能直接重跑。這支工具不修改標題、敘述、日期，也不刪列。

### 設定既有列的回報對象

任何授權使用者都能在 item 留言串明確要求變更；用 `context` 取得 record ID後執行：

```bash
./bin/slack-list reporter Rec0B… --user U0B…  # 回報給被 mention 的一人
./bin/slack-list reporter Rec0B… --default    # 真人建立者／bot 建列發起者
./bin/slack-list reporter Rec0B… --none       # 驗收時不 @ 人
```

一列可以有多位指派對象，但回報對象至多一位。不要從 assignee 猜該通知誰。

---

## 🔍 被派去查一件待辦時

**規則不在這裡，在 [`fleet-recon`](../fleet-recon/SKILL.md)** —— 偵察怎麼查、任務怎麼寫、
`✅` / `⚠️` 怎麼標，那支是唯一權威。架構與規則見
[`docs/fleet-flow.md`](../../../docs/fleet-flow.md)。

這裡只補一件 `fleet-recon` 不可能知道的事，因為它不碰 Slack：

⚠️ **`敘述` 欄常常只有「功能…」，真規格在那一列的留言串裡**（`bin/slack-list replies`）。
沒讀留言就去查 repo，你拿到的需求會比實際的少一半。

## 🔑 開 issue 一定要先埋指紋

先跑 `./bin/slack-list env` 看 `ISSUE_MODE`：

- `agent`：照本節既有流程，用 `gh` 查重並開 issue。
- `manual`：**沒有 GitHub credential，不准嘗試 `gh` 或要求 token。** 偵察寫完草稿後，用
  `slack-list draft` 把 Markdown、指紋搜尋頁與 New issue 頁交回原生 item 留言串，然後停。
  只有既有待辦列能走這條發布流程；DM 或一般 channel 的口述需求要先用 `add` 對應到待辦列。

```bash
./bin/slack-list draft Rec0B… \
  --md drafts/<日期>/<短名>.md \
  --repo ShuChenAI/<repo> \
  --summary "<一句定位結論>" \
  --requested-by <openab.sender.v1 的 sender_id>
```

`manual` mode 的核准動作是人從 GitHub 網頁提交，或把附件交給有 `gh` 權限的 local agent。
不要聲稱已完成 GitHub 查重；只能提供搜尋連結讓核准者確認。

**開 issue 前必做，不是加分項。** 待辦從 Slack 進 GitHub 的流程裡，開 issue 的是 agent
不是人，沒有人在那個位置擋重複，所以這步漏掉就一定會開出重複的任務。

```bash
# 1. 先比對，任何一筆命中就不要開，去那張既有的 issue 上留言
gh issue list --search "Rec0B…" --state all

# 2. 沒命中才開。body 第一行放這個，然後才是簡報
> Slack 來源：[Rec0B…](https://shuchenai-rdpm.slack.com/lists/T0B54FC26FR/<LIST_ID>?record_id=Rec0B…)
```

**開完不用另外記。** 那行指紋就是正本，`--search` 立刻查得到，工具不留副本。

`Rec0B…` 就是 `todo` / `mine` / `assigned` 每列開頭印的那串。`<LIST_ID>` 從 `.env` 的 `SLACK_LIST_ID` 拿。

⚠️ **指紋要「看得見」，不要藏在 `<!-- -->` 裡。** GitHub 搜尋會不會索引 HTML 註解沒有定論，
而整套去重就靠這個查詢，賭不起。放成可見的引言行還有兩個好處：你點得回 Slack 那列，
別人看 issue 也知道來源。

⚠️ **不要靠 GitHub 自己的重複偵測。** 那個只在網頁表單被證實，
`gh issue create` 走不走得到官方沒講。當它不存在。

### 一列預設一張 issue

拆成多個任務是**例外**（顆粒度還沒定案，見最下面）。真的拆了，每一個都各自埋同一個指紋，
再用 `slack-list progress` 在該列的留言串貼一則「拆成 #1801 #1802 #1803」讓後面的人看得到。

### 只有正本，沒有快取

「這一列對到哪幾張 issue」的唯一答案是 `gh issue list --search "Rec0B…" --state all`。
工具不存副本 —— 存了就是養一份會過期的東西（見
`docs/adr/0001-report-into-the-native-item-comment-thread.md`）。

issue 格式走 `~/code/teamsync-frontend` 的
`docs/guides/workflow/github-issue-standards.md`
與 `docs/agents/issue-tracker.md`（`gh issue create --type` 是必要的），
規格不足的掛 `needs-triage`。整套工作流見
`~/code/work-docs/docs/ai/herdr/agent-fleet-workflow.md`。

---

## 📣 回報

**回報寫進該列原生的 item 留言串** —— PM 本來就在那裡講話。
Slack 在建列時就替每一列開好串了，腳本只查既有串、不另建串，對應關係也不用維護
（Slack 自己是正本）。

```bash
# 中間進度：只回在串裡，不 @ 人、不改狀態
./bin/slack-list progress Rec0B… "後端改完，佈建零失敗行"

# 可以驗收了：@ 回報對象 + 狀態改成「PM確認中」
./bin/slack-list ready Rec0B… \
  --url    https://fix-spc-update.teamsync-frontend.pages.dev \
  --report drafts/<日期>/reports/report-<issue>-<短名>.md

# 沒有畫面可看的單（後端、純文件）：沒有 QA table 可寫，用 flag
./bin/slack-list ready Rec0B… --no-url \
  --changed "生產單建立時就佔料，完工才落帳" \
  --verify  "建一張生產單，確認投入明細出現在異動紀錄"
```

四條規矩：

- **`ready` 只在使用者說可以驗收時跑。** 它會推播吵到 PM。
  你自己覺得寫完了不算；測試綠了也不算；**沒 push 的 commit 不算**。
  不確定就跑 `progress`，那個不吵人。
  **這一列如果拆成多張 issue，要全部關掉才算** —— 跑之前先
  `gh issue list --search "Rec0B…" --state open`，有東西回來就不要跑。
  （`ready` 自己不查 GitHub，這步是你的責任。）
- **`ISSUE_MODE=manual` 時不跑 `ready`。** 遠端 backlog agent 看不到 private GitHub issue，
  無法證明這一列拆出的任務全關了；驗收由有 GitHub 權限的 local implementation agent 回報。
- **前端單一律 `--report`，不要用 `--changed`／`--verify` 湊。** 模板見下面那節。
  「怎麼驗收」寫得出來才算做完，那是 PM 唯一真正需要的東西 ——
  「測試一下」等於沒寫，要寫成「開哪個頁面 → 做什麼 → 看到什麼」。
  白話：PM 不看 commit，不要貼 SHA 或函式名。
- **`--url` 要帶測試連結，`ready` 才跑得動。** 前端的分支預覽網址是
  branch 名稱把 `/` 與其他非英數字元換成 `-`，接
  `.teamsync-frontend.pages.dev` —— `fix/spc-update` →
  `https://fix-spc-update.teamsync-frontend.pages.dev`。
  **腳本自己不推導**（它在 `work-helper` 目錄跑，`git` 問到的是 work-helper 的 branch），
  所以要你算出來傳進去；發出去之前它會先確認連得到，連不到就中止。
  分支預覽要 CI 跑完才會有；後端單、純文件單這種本來就沒有畫面可看的，用 `--no-url`。

`--quiet` 不 `@` 人，只有使用者明講「先別吵他」時才用。

⚠️ **`@` 的是「回報對象」，不是「指派對象」。** 明確 `reporter` 設定優先；沒有設定時，
真人建立的列用 `created_by`，bot 代建的列用來源註記裡的發起者。找不到就不 `@` 人，
絕不拿 assignee 猜。

沒有任何刪除指令。要撤回已發的訊息，跟使用者說，讓他自己刪。

### 驗收報告固定四段

`--report` 吃一份 md，整份就是 Slack 訊息本體。**照 [`report-template.md`](report-template.md) 寫**，
四段是 `改了什麼` → `⚠️ 要先知道的一件事`（有才寫）→ `怎麼驗收` → `QA case` 表格。
少任何一段腳本就不發，所以模板不用背 —— 忘了就跑一次看它罵什麼。

- **✅ 只能來自實際跑過的測試。** 先跑（例：`vitest run src/app/modules/inventory`），
  再把 `describe`／`it` 標題翻成 PM 看得懂的情境。**憑印象打勾就是給 PM 一份假的覆蓋率**，
  而這件事腳本驗不了 —— 只有你會知道你沒跑。
- **⬜ 後面要寫為什麼測不到**（「純顏色，要人工看」「你 08/17 驗過，這次沒動」）。
  只打一個框，PM 分不出那是漏掉還是刻意不測。（這條腳本會擋。）
- **「怎麼驗收」要指名現成資料**，寫「`PMV 低庫存示範品`」不要寫「找一個低庫存的品項」——
  PM 得自己造資料的驗收步驟，等於沒寫。
- **⚠️ 那段沒有行為改變就整段刪掉。** 固定要寫就會被硬填，填出來的是廢話，PM 下次整段跳過。

md 的 H1 標題與「測試網址：」那行會被腳本拿掉（訊息本身已經有），檔案自己留著是對的。

⚠️ **不要再用 `--md` 附一份同樣的報告。** 報告本體已經在訊息裡了，`--md` 是給真正額外的
東西用的（截圖、PM 給的規格檔）。那個附件會寫進該列的「檔案」欄，而且是**累加**的
（`bin/slack-list:1263`）—— 每跑一次 `ready` 就多一份，最後那一欄是一疊同名的舊版本。

### 讀回覆

PM 的回覆都在該列的 item 留言串裡。

```bash
./bin/slack-list replies            # 掃整張表，只列「有別人回過」的
./bin/slack-list replies Rec0B…     # 看某一列（預設只印別人回的）
./bin/slack-list replies Rec0B… --all   # 連 bot 自己發的也印
```

**使用者問「PM 有沒有回我」「有什麼新回覆」就跑不帶參數那個。**
不要自己去開 Slack MCP 讀 channel —— 那會撈到一堆跟待辦無關的訊息。

---

## 🗂️ 這張表長什麼樣

實際欄位以 `./bin/slack-list fields` 為準。壓平後常見的鍵：

| 欄位 | 壓平後的鍵 | 內容 |
|---|---|---|
| 指派對象 | `todo_assignee` | user ID，例如 `U0B54FKJ93R`。**一列可以掛多人**，壓平後是空白分隔的字串 |
| 已完成 | `todo_completed` | checkbox；勾選或封存的列不擋同名新需求 |
| 到期日 | `todo_due_date` | `YYYY-MM-DD`，相對日期以 `Asia/Taipei` 換算 |
| 名稱 | `name` | 帶前綴代號，例如 `T04 退貨表供應商欄位刪除`、`V01 在途欄位調整` |
| 敘述 | `Col0B8E4BG7JT` | 一段說明，**常常被截斷或只有幾個字** |
| 狀態 | `Col0B9U6UHD16` | 多選，值是 `OptXXXX` 代碼**不是人看的字串**；要對照文字跑 `fields` |

三個要注意的：

- **assignee 只有 ID，沒有名字。** 解成名字要 `users:read`，app 沒有那個 scope。
  Local自己的 ID 從 `.env` 的 `SLACK_MY_USER_ID` 拿（`mine` 已經處理好）；OpenAB當次使用者
  從 `openab.sender.v1.sender_id` 拿，交給 `assigned`。
- **名稱前綴（`T` / `V` / `S` / `D` / `B` + 數字）是某種模組代號，但對應關係還沒確認。**
  不要憑字面猜它對到哪個模組，要用就先問使用者。
- **`狀態` 是多選，而且前端後端分開** —— 一件事可能同時牽涉
  `~/code/teamsync-frontend` 和 `~/code/teamsync-backend`。只看前端會漏。

---

## ⚠️ 撞到會浪費時間的

- **表的 schema 改不動。** 加欄位、加選項都回 `missing required field: id`，
  新元素的 id 只有 Slack 發得出來。要動欄位只能請使用者去 UI 改。
- **沒有 Events API。** Slack 不會推送 List 或討論串的變動。
  PM 在串裡回了什麼，要自己跑 `conversations.replies` 撈。
- **Slack 失敗時 HTTP 回 200**，錯誤在 body 的 `ok:false`。腳本已經翻成人話，照著做。
  `missing_scope` 一律是「加完 scope 要重裝 app，token 會換一組新的」。

---

## 🚧 還沒定案的（不要自己發明）

- **顆粒度**：一列開幾張 issue？前後端要不要拆兩張？討論過沒結論，遇到時**問使用者**。
