# 偵察寫草稿檔，issue 由 backlog 層集中開

偵察查完現況，把內容寫成一份草稿檔（`drafts/<日期>/<短名>.md`，不進版控），
**回覆只給一行路徑**。查重和 `gh issue create` 都不歸它管，由 backlog 層（`bin/fleet`）統一做。

## 為什麼不讓偵察自己開

第一版讓偵察自己開 issue，理由是「省掉為每件事寫一次粗單，issue 一出生就有內容」。
那個好處還在（草稿就是 body），但它換來兩個洞：

- **同一批裡的重複擋不住。** 每個偵察各自跑 `gh issue list --search` 查重，
  N 個平行跑的時候互相看不見 —— Slack 上兩列其實在講同一件事，兩邊都沒命中
  （issue 都還沒開），兩邊都開一張。指紋只擋得住跟**舊** issue 的重複。
- **顆粒度來不及。** ADR-0002 說顆粒度必須在開 issue 那一刻決定，
  但偵察各自開完你才看得到，想合併只能關掉一張。收到 backlog 層之後，
  合併發生在 issue 存在之前，改動範圍的交集也一樣。

## 為什麼回一行路徑，不回內容

回傳值會進總管理的 context。N 份完整 issue body 穿過去，等於又壓成一個 session ——
那正是分層要避開的東西。走檔案的話 context 一樣乾淨，而總管理要算交集時
只需要讀每份的「要改哪些檔案」那一段。

草稿放 `work-helper/drafts/`（`.gitignore` 忽略），不放 `~/.cache/`：
裝法本來就是 clone + symlink，那個資料夾一定在，而且出事時 `ls` 就看得到。
這裡用 `.gitignore` 是對的，不是 `.git/info/exclude` —— 那個坑是「已開好的 worktree
看不到剛加的 `.gitignore` 行」，work-helper 不開 worktree，而且這條規則該跟著 repo 給每個 clone。

## 偵察還是不能開 worktree —— 是循環不是成本

worktree 要 branch 名 → branch 名要 issue 編號 → issue 還沒開。

所以偵察坐在**共用 checkout** 上，N 個同時讀同一份工作區。
而 agent 的 cwd 在 spawn 那一刻就定死（herdr 的 `--cwd` 只在 `pane split`，
`pane move` 不改 cwd），所以「偵察 → 接單」一定會換 agent。

## 代價：共用 checkout 沒有強制力

「只讀」是規則不是機制。發生過一次：回頭在偵察的 pane 裡下了實作指令，
4 個檔案被改掉，而另外 4 個偵察正在讀同一份工作區（讀到改一半的檔案會產出錯的結論）。

兩條防護，主藥是第一條：

1. **共用 checkout 只拿來偵察。要改檔案就開 worktree** —— 沒有「順手在這裡改一下」。
2. 收工前 `git status --short`。不乾淨的話，那段時間寫的草稿錨點要重驗。
   這條擋得住兩種根因，但只在事後抓得到。

## 草稿的 body 照目標 repo 的 issue 規範

不要自己定一套。第一版在這裡自訂了格式，結果跟 repo 的 issue 規範打架，
產出讀起來像 spec。一個欄位只能有一個權威。草稿等於 issue body，所以規範是同一份。
