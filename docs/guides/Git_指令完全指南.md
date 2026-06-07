# Git 指令完全指南

## 目錄
1. [基礎概念](#一基礎概念)
2. [初始設定](#二初始設定)
3. [創建與複製倉庫](#三創建與複製倉庫)
4. [基本工作流程](#四基本工作流程)
5. [分支管理](#五分支管理)
6. [合併變更](#六合併變更)
7. [與遠端倉庫同步](#七與遠端倉庫同步)
8. [撤銷與時光旅行](#八撤銷與時光旅行)
9. [進階但實用的功能](#九進階但實用的功能)
10. [工作流程最佳實踐](#十工作流程最佳實踐)

---

## 一、基礎概念

### 什麼是 Git？

**Git** 是一個分散式版本控制系統（Distributed Version Control System, DVCS）。簡單來說，它幫助你記錄代碼的每一次變化，就像「作文的歷史版本」一樣。

**為什麼需要 Git？**
- 📝 追蹤每一次代碼變更
- 👥 多人協作時不會互相覆蓋
- ⏮️ 可以回到任何過去的版本
- 🔀 可以同時進行多個開發分支

### 版本控制的重要性

想像你在寫論文：
- **沒有版本控制**：論文有 V1.doc、V1改.doc、V1改改.doc...各種版本混亂
- **有版本控制**：清楚地記錄每次修改是誰、什麼時候、改了什麼內容

Git 就是做這件事的工具。

### 本地倉庫 vs 遠端倉庫

- **本地倉庫**：你電腦上的 Git 倉庫，包含完整的歷史記錄
- **遠端倉庫**：存在於伺服器上的倉庫（例如 GitHub、GitLab），用於備份和協作

```
你的電腦 (本地倉庫) ←→ GitHub (遠端倉庫)
```

---

## 二、初始設定

### 安裝與環境檢查

#### `git --version`

**作用**：檢查 Git 是否安裝以及版本號

**基本語法**：
```bash
git --version
```

**範例**：
```bash
$ git --version
git version 2.40.0
```

✅ 有出現版本號表示 Git 已安裝成功

---

### `git config`

**作用**：查看或修改 Git 的設定

**基本語法**：
```bash
git config [--global] <key>              # 查看設定
git config [--global] <key> <value>      # 修改設定
```

**常用參數**：
- `--global`：全域設定（對所有倉庫有效）
- 不加 `--global`：只對目前倉庫有效

**設定級別**：
1. `--local`：只對目前倉庫有效
2. `--global`：對目前使用者有效
3. `--system`：對整個系統有效

---

### `git config --global user.name`

**作用**：設定你的名字（會顯示在提交記錄上）

**基本語法**：
```bash
git config --global user.name "你的名字"
```

**範例**：
```bash
$ git config --global user.name "John Doe"
$ git config --global user.name
John Doe
```

⚠️ **注意**：這個名字會永久記錄在每一次提交中，所以要用你真實的名字或常用的昵稱

---

### `git config --global user.email`

**作用**：設定你的信箱（會顯示在提交記錄上）

**基本語法**：
```bash
git config --global user.email "你的信箱@example.com"
```

**範例**：
```bash
$ git config --global user.email "john@example.com"
$ git config --global user.email
john@example.com
```

💡 **小提示**：如果使用 GitHub，建議使用註冊 GitHub 時使用的信箱

---

### 檢查所有設定

**查看所有全域設定**：
```bash
git config --global --list
```

**查看目前倉庫的所有設定**：
```bash
git config --list
```

**範例輸出**：
```
user.name=John Doe
user.email=john@example.com
core.editor=vim
...
```

---

## 三、創建與複製倉庫

### `git init`

**作用**：初始化一個新的本地 Git 倉庫

**基本語法**：
```bash
git init [目錄名稱]
```

**範例**：

1️⃣ **在目前目錄初始化**：
```bash
$ cd my-project
$ git init
Initialized empty Git repository in /Users/john/my-project/.git/
```

2️⃣ **創建新目錄並初始化**：
```bash
$ git init my-new-project
Initialized empty Git repository in /Users/john/my-new-project/.git/
$ cd my-new-project
```

✅ **成功標示**：會出現 `.git` 資料夾（隱藏資料夾），裡面存放所有 Git 資訊

💡 **小提示**：執行後，資料夾名稱旁會出現 `(master)` 或 `(main)` 標示

---

### `git clone`

**作用**：複製遠端倉庫到本地

**基本語法**：
```bash
git clone <倉庫網址> [本地目錄名稱]
```

**常用參數**：
- `--depth <深度>`：只克隆最近 N 次提交（快速複製）
- `--branch <分支>`：只克隆特定分支

**範例**：

1️⃣ **基本複製**：
```bash
$ git clone https://github.com/user/repo.git
Cloning into 'repo'...
remote: Counting objects: 100% (50/50), done.
remote: Compressing objects: 100% (40/40), done.
Receiving objects: 100% (50/50), 5.00 KB, done.
```

2️⃣ **複製並指定本地目錄名稱**：
```bash
$ git clone https://github.com/user/repo.git my-local-name
```

3️⃣ **只克隆最近 10 次提交（節省空間）**：
```bash
$ git clone --depth 10 https://github.com/user/repo.git
```

✅ **成功標示**：出現 `Receiving objects: 100%` 並創建了本地目錄

---

### `git status`

**作用**：檢視倉庫目前的狀態（有哪些檔案被修改、新增或刪除）

**基本語法**：
```bash
git status
```

**常用參數**：
- `-s` 或 `--short`：簡潔格式

**範例**：

1️⃣ **詳細狀態**：
```bash
$ git status
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update the working directory)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   README.md

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        new_file.txt

nothing added to commit but untracked changes present (working directory)
```

2️⃣ **簡潔格式**：
```bash
$ git status -s
 M README.md
?? new_file.txt
```

**狀態符號說明**：
- `M`（Modified）：檔案已修改
- `A`（Added）：檔案已新增
- `D`（Deleted）：檔案已刪除
- `??`（Untracked）：未追蹤的檔案

💡 **小提示**：開發前後都可以用 `git status` 確認目前狀態

---

## 四、基本工作流程

Git 的基本工作流程就是：修改檔案 → 暫存 → 提交 → 推送

### `git add`

**作用**：將檔案變更加入暫存區（Staging Area），準備提交

**基本語法**：
```bash
git add <檔案名稱>
git add <路徑>
git add .
```

**常用方式**：
- `git add .`：暫存所有變更
- `git add <file>`：暫存特定檔案
- `git add *.js`：暫存所有 .js 檔案

**`git add .` vs `git add <file>`**：

| 指令 | 作用 | 適合時機 |
|------|------|--------|
| `git add .` | 暫存所有變更的檔案 | 確認所有改動都應該提交 |
| `git add <file>` | 只暫存特定檔案 | 只想提交部分變更 |

**範例**：

1️⃣ **暫存所有檔案**：
```bash
$ git add .
$ git status -s
 M app.js
 M config.json
A? new-feature.js
```

2️⃣ **暫存特定檔案**：
```bash
$ git add app.js
$ git status -s
M  app.js          # 已暫存
 M config.json     # 未暫存（前面是空格）
```

3️⃣ **分次暫存**：
```bash
$ git add feature1.js
$ git add feature2.js
# 最後一起提交
```

⚠️ **注意**：暫存後檔案名稱前面會有 `M`（沒有空格），表示已暫存

---

### `git commit`

**作用**：將暫存區的變更保存為一個「歷史快照」

**基本語法**：
```bash
git commit
git commit -m "提交訊息"
```

**常用參數**：
- `-m "訊息"`：直接在命令行指定提交訊息
- `-a`：跳過 `git add`，直接暫存並提交已追蹤的檔案
- `--amend`：修改上一次提交

**範例**：

1️⃣ **基本提交**：
```bash
$ git add .
$ git commit -m "Add login feature"
[main a1b2c3d] Add login feature
 2 files changed, 50 insertions(+)
 create mode 100644 login.js
```

2️⃣ **不寫訊息會打開編輯器**：
```bash
$ git commit
# 會打開 vim 或其他預設編輯器
# 你可以寫多行訊息
```

3️⃣ **跳過 add 步驟**（只對已追蹤的檔案有效）：
```bash
$ git commit -a -m "Update README"
# 等同於：
# git add .
# git commit -m "Update README"
```

📝 **提交訊息最佳實踐**：
```bash
# ✅ 好的訊息
git commit -m "Add user authentication"
git commit -m "Fix bug in payment processing"
git commit -m "Update documentation"

# ❌ 不好的訊息
git commit -m "fix"
git commit -m "update"
git commit -m "asdfgh"
```

💡 **小提示**：提交訊息要用英文或中文清楚描述這次改動做了什麼

---

### `git log`

**作用**：查看提交歷史記錄

**基本語法**：
```bash
git log
git log --oneline
```

**常用參數**：
- `--oneline`：單行顯示（簡潔）
- `-n <數字>`：顯示最近 N 次提交
- `--graph`：用圖表顯示分支
- `--author="名字"`：只顯示特定人員的提交
- `--since="2026-01-01"`：顯示特定時期後的提交

**範例**：

1️⃣ **詳細歷史**：
```bash
$ git log
commit a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
Author: John Doe <john@example.com>
Date:   Mon May 2 10:30:45 2026 +0800

    Add user authentication

commit b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1
Author: John Doe <john@example.com>
Date:   Sun May 1 15:20:30 2026 +0800

    Fix bug in payment processing
```

2️⃣ **簡潔格式**：
```bash
$ git log --oneline
a1b2c3d Add user authentication
b2c3d4e Fix bug in payment processing
c3d4e5f Update documentation
d4e5f6g Initial commit
```

3️⃣ **顯示最近 3 次提交**：
```bash
$ git log --oneline -n 3
a1b2c3d Add user authentication
b2c3d4e Fix bug in payment processing
c3d4e5f Update documentation
```

4️⃣ **用圖表顯示分支**：
```bash
$ git log --oneline --graph --all
* a1b2c3d Add user authentication
* b2c3d4e Fix bug in payment processing
* c3d4e5f Update documentation
```

5️⃣ **查看特定人員的提交**：
```bash
$ git log --author="John" --oneline
```

💡 **小提示**：按 `q` 可以退出 `git log` 的瀏覽模式

---

## 五、分支管理

分支就像是平行世界。你可以在一個分支上開發新功能，不影響主分支。

### `git branch`

**作用**：查看、創建、刪除分支

**基本語法**：
```bash
git branch                      # 查看本地分支
git branch <分支名稱>           # 創建新分支
git branch -a                   # 查看所有分支（包括遠端）
git branch -d <分支名稱>        # 刪除分支
git branch -D <分支名稱>        # 強制刪除分支
```

**常用參數**：
- `-a`：顯示所有分支（本地 + 遠端）
- `-v`：顯示分支以及最後一次提交
- `-d`：刪除分支（安全，已合併才能刪）
- `-D`：強制刪除分支
- `-m`：重新命名分支

**範例**：

1️⃣ **查看本地分支**：
```bash
$ git branch
  develop
* main
  feature/login
```
✅ `*` 表示目前所在分支

2️⃣ **創建新分支**：
```bash
$ git branch feature/user-profile
$ git branch
  develop
  feature/login
* feature/user-profile
  main
```

3️⃣ **查看所有分支（包括遠端）**：
```bash
$ git branch -a
  develop
  feature/login
* main
  remotes/origin/develop
  remotes/origin/main
```

4️⃣ **查看分支及最後提交**：
```bash
$ git branch -v
  develop              b2c3d4e Fix bug in payment
  feature/login        c3d4e5f Add login feature
* main                 a1b2c3d Add user authentication
```

5️⃣ **刪除分支**：
```bash
$ git branch -d feature/login
Deleted branch feature/login (was c3d4e5f).
```

6️⃣ **強制刪除未合併的分支**：
```bash
$ git branch -D feature/experimental
Deleted branch feature/experimental (was x1y2z3a).
```

7️⃣ **重新命名分支**：
```bash
$ git branch -m old-name new-name
```

---

### `git checkout`

**作用**：切換到另一個分支或回到之前的版本

**基本語法**：
```bash
git checkout <分支名稱>         # 切換分支
git checkout -b <分支名稱>      # 創建並切換到新分支
git checkout <commit-hash>      # 回到特定提交
git checkout -- <檔案>          # 丟棄檔案變更
```

**常用參數**：
- `-b`：創建並切換到新分支

**範例**：

1️⃣ **切換分支**：
```bash
$ git checkout develop
Switched to branch 'develop'
$ git branch
* develop
  main
```

2️⃣ **創建並切換到新分支**：
```bash
$ git checkout -b feature/payment
Switched to a new branch 'feature/payment'
$ git branch
* feature/payment
  develop
  main
```

3️⃣ **回到特定提交**：
```bash
$ git checkout a1b2c3d
HEAD is now at a1b2c3d Add user authentication
```

⚠️ **注意**：這樣會進入「分離頭指針」狀態，通常不建議這樣做

---

### `git switch`（新命令）

**作用**：切換分支（比 `checkout` 更簡潔）

**基本語法**：
```bash
git switch <分支名稱>           # 切換分支
git switch -c <分支名稱>        # 創建並切換到新分支
```

**與 `git checkout` 的區別**：
- `git switch` 只用來切換分支
- `git checkout` 能做的事更多（也更容易出錯）
- 新版 Git 建議用 `git switch`

**範例**：

1️⃣ **切換分支**：
```bash
$ git switch develop
Switched to branch 'develop'
```

2️⃣ **創建並切換到新分支**：
```bash
$ git switch -c feature/api
Switched to a new branch 'feature/api'
```

💡 **小提示**：如果 Git 版本較舊可能沒有 `git switch`，用 `git checkout` 替代

---

### `git branch -a`

**作用**：查看所有分支（包括遠端分支）

**基本語法**：
```bash
git branch -a
```

**範例**：
```bash
$ git branch -a
  develop
  feature/login
* main
  remotes/origin/develop
  remotes/origin/main
  remotes/origin/staging
```

✅ 前面沒有 `remotes/` 的是本地分支，有 `remotes/` 的是遠端分支

---

### `git branch -v`

**作用**：查看分支及最後一次提交

**基本語法**：
```bash
git branch -v
```

**範例**：
```bash
$ git branch -v
  develop              b2c3d4e Fix bug in payment
* main                 a1b2c3d Add user authentication
  feature/login        c3d4e5f Add login feature
```

💡 **小提示**：可以快速看出各分支目前的開發進度

---

### `git branch -d` 和 `git branch -D`

**作用**：刪除分支

**區別**：
- `-d`：安全刪除（如果分支未合併會拒絕）
- `-D`：強制刪除（忽略合併狀態）

**範例**：

1️⃣ **安全刪除**：
```bash
$ git branch -d feature/completed
Deleted branch feature/completed (was c3d4e5f).
```

2️⃣ **分支未合併時安全刪除會失敗**：
```bash
$ git branch -d feature/unmerged
error: The branch 'feature/unmerged' is not fully merged.
If you are sure you want to delete it, run 'git branch -D feature/unmerged'.
```

3️⃣ **強制刪除**：
```bash
$ git branch -D feature/unmerged
Deleted branch feature/unmerged (was x1y2z3a).
```

⚠️ **注意**：強制刪除後無法復原，要確認真的不需要這個分支

---

## 六、合併變更

### `git merge`

**作用**：將一個分支的改動合併到另一個分支

**基本語法**：
```bash
git merge <分支名稱>
git merge --no-ff <分支名稱>    # 保留合併記錄
git merge --squash <分支名稱>   # 壓縮所有提交為一個
```

**常用參數**：
- `--no-ff`：即使可以快進也創建合併提交（保留歷史）
- `--squash`：將所有提交壓縮為一個
- `--abort`：中止合併

**範例**：

1️⃣ **基本合併**：
```bash
$ git checkout main           # 先切換到目標分支
$ git merge feature/login     # 合併 feature/login 到 main
Merge made by the 'recursive' strategy.
 login.js | 50 ++++++++++++++++++++++
 1 file changed, 50 insertions(+)
```

2️⃣ **使用 --no-ff 保留合併記錄**：
```bash
$ git merge --no-ff feature/payment
# 會打開編輯器讓你寫合併訊息
```

3️⃣ **壓縮提交合併**：
```bash
$ git merge --squash feature/api
# 所有提交會被壓縮成一個，但不會自動提交
$ git commit -m "Add API endpoints"
```

💡 **小提示**：合併前最好確保你在正確的分支上（用 `git branch` 查看）

---

### 合併衝突說明

**什麼是合併衝突？**

當兩個分支修改了同一個檔案的同一行時，Git 不知道要保留哪一個，就會產生衝突。

**衝突標記**：
```
<<<<<<< HEAD
// main 分支的內容
your content here
=======
// feature 分支的內容
their content here
>>>>>>> feature/login
```

**解決步驟**：

1️⃣ **查看衝突狀態**：
```bash
$ git status
Both modified: app.js
```

2️⃣ **打開衝突檔案並手動解決**：
```bash
<<<<<<< HEAD
const PORT = 3000;
=======
const PORT = 5000;
>>>>>>> feature/login
```

2️⃣ **編輯檔案，決定保留哪個版本**：
```bash
// 決定保留 main 的設定
const PORT = 3000;
```

3️⃣ **移除衝突標記後暫存**：
```bash
$ git add app.js
$ git commit -m "Resolve merge conflict in app.js"
```

**解決衝突時的工具**：
```bash
# 使用圖形化工具解決衝突
git mergetool

# 保留 HEAD（目前分支）的版本
git checkout --ours app.js
git add app.js

# 保留另一個分支的版本
git checkout --theirs app.js
git add app.js
```

---

### `git merge --abort`

**作用**：中止合併（恢復到合併前的狀態）

**基本語法**：
```bash
git merge --abort
```

**範例**：
```bash
$ git merge feature/broken
CONFLICT (content): Merge conflict in app.js
Automatic merge failed; fix conflicts and then commit the result.

$ git merge --abort
```

✅ 合併被取消，回到合併前的狀態

---

## 七、與遠端倉庫同步

### `git remote`

**作用**：查看或管理遠端倉庫

**基本語法**：
```bash
git remote                      # 列出所有遠端
git remote -v                   # 顯示詳細資訊
git remote add <名稱> <網址>    # 新增遠端
git remote remove <名稱>        # 移除遠端
```

**範例**：

1️⃣ **列出所有遠端**：
```bash
$ git remote
origin
upstream
```

2️⃣ **顯示遠端詳細資訊**：
```bash
$ git remote -v
origin    https://github.com/user/repo.git (fetch)
origin    https://github.com/user/repo.git (push)
upstream  https://github.com/original/repo.git (fetch)
upstream  https://github.com/original/repo.git (push)
```

3️⃣ **新增遠端**：
```bash
$ git remote add upstream https://github.com/original/repo.git
$ git remote
origin
upstream
```

4️⃣ **移除遠端**：
```bash
$ git remote remove upstream
```

💡 **小提示**：
- `origin` 通常是你複製（clone）的倉庫
- `upstream` 通常是原始倉庫（當你有 fork 時）

---

### `git remote -v`

**作用**：顯示遠端倉庫的詳細資訊（包括網址）

**基本語法**：
```bash
git remote -v
```

**範例**：
```bash
$ git remote -v
origin    https://github.com/john/my-repo.git (fetch)
origin    https://github.com/john/my-repo.git (push)
```

✅ 一行顯示兩次：第一個用於拉取（fetch），第二個用於推送（push）

---

### `git push`

**作用**：將本地提交推送到遠端倉庫

**基本語法**：
```bash
git push                        # 推送目前分支
git push origin <分支>          # 推送指定分支
git push origin <本地>:<遠端>   # 推送到不同名稱的遠端分支
git push -u origin <分支>       # 推送並設定上游分支
```

**常用參數**：
- `-u`：推送並設定上游分支（下次可以直接 `git push`）
- `-f`：強制推送（不建議在共享分支使用）
- `--all`：推送所有分支

**範例**：

1️⃣ **推送目前分支**：
```bash
$ git push
Enumerating objects: 5, done.
Counting objects: 100% (5/5), done.
Writing objects: 100% (3/3), 250 bytes, done.
Total 3 (delta 0), reused 0 (delta 0), pack-reused 0
To https://github.com/john/my-repo.git
   a1b2c3d..d4e5f6g main -> main
```

2️⃣ **推送特定分支**：
```bash
$ git push origin feature/login
```

3️⃣ **第一次推送新分支（設定上游）**：
```bash
$ git push -u origin feature/payment
Branch 'feature/payment' set up to track remote branch 'feature/payment' from 'origin'.
```

4️⃣ **推送到不同名稱的遠端分支**：
```bash
$ git push origin feature/api:api-v2
# 本地的 feature/api 會推送到遠端的 api-v2
```

⚠️ **注意**：
- 推送前最好先拉取（`git pull`）最新變更，避免衝突
- 不要強制推送（`-f`）到共享分支，會覆蓋他人的工作

---

### `git push origin <branch>`

**作用**：將特定分支推送到遠端

**基本語法**：
```bash
git push origin <分支名稱>
```

**範例**：
```bash
$ git push origin develop
Total 3 (delta 0), reused 0 (delta 0), pack-reused 0
To https://github.com/john/my-repo.git
 * [new branch]      develop -> develop
```

✅ 成功推送後，遠端會有這個分支

---

### `git pull`

**作用**：拉取遠端最新變更並自動合併到本地

**基本語法**：
```bash
git pull
git pull origin <分支>
```

**常用參數**：
- `--rebase`：使用 rebase 而不是 merge（會改寫歷史）

**範例**：

1️⃣ **拉取目前分支**：
```bash
$ git pull
remote: Enumerating objects: 5, done.
Receiving objects: 100% (3/3), 250 bytes, done.
Updating a1b2c3d..d4e5f6g
Fast-forward
 app.js | 10 ++++++++--
 1 file changed, 8 insertions(+), 2 deletions(-)
```

2️⃣ **拉取特定分支**：
```bash
$ git pull origin develop
```

3️⃣ **如果有衝突**：
```bash
$ git pull
CONFLICT (content): Merge conflict in app.js
Automatic merge failed; fix conflicts and then commit the result.

# 解決衝突後
$ git add app.js
$ git commit -m "Resolve pull conflict"
$ git push
```

💡 **小提示**：每天開始開發前都應該 `git pull` 更新代碼

---

### `git fetch` vs `git pull`

**區別**：

| 指令 | 作用 | 何時用 |
|------|------|--------|
| `git fetch` | 只下載遠端變更，不合併 | 想先看遠端有什麼改動 |
| `git pull` | 下載並自動合併 | 想直接更新本地代碼 |

**視覺化**：
```
遠端倉庫
    ↓
git fetch → 本地遠端追蹤分支（如 origin/main）
    ↓
git merge → 本地分支（如 main）

git pull = git fetch + git merge
```

**範例**：

1️⃣ **先 fetch 再看**：
```bash
$ git fetch origin
$ git log --oneline -5 origin/main
d4e5f6g Add payment feature
a1b2c3d Add user authentication
...

$ git merge origin/main    # 確認無誤後才合併
```

2️⃣ **直接 pull**：
```bash
$ git pull origin main     # 一次完成 fetch + merge
```

---

## 八、撤銷與時光旅行

### `git diff`

**作用**：查看檔案的變更內容（比較版本差異）

**基本語法**：
```bash
git diff                        # 查看工作目錄 vs 暫存區
git diff --staged               # 查看暫存區 vs 最後提交
git diff <commit1> <commit2>   # 比較兩個提交
git diff <分支1> <分支2>       # 比較兩個分支
```

**常用參數**：
- `--staged` 或 `--cached`：查看已暫存的變更
- `-w`：忽略空白差異

**範例**：

1️⃣ **查看未暫存的改動**：
```bash
$ git diff
diff --git a/app.js b/app.js
index a1b2c3d..d4e5f6g 100644
--- a/app.js
+++ b/app.js
@@ -10,3 +10,5 @@ const app = express();
 app.use(express.json());
 
-const PORT = 3000;
+const PORT = 5000;
```

2️⃣ **查看已暫存的改動**：
```bash
$ git diff --staged
```

3️⃣ **比較兩個提交**：
```bash
$ git diff a1b2c3d d4e5f6g
```

4️⃣ **比較兩個分支**：
```bash
$ git diff main feature/login
```

💡 **小提示**：
- `+` 表示新增
- `-` 表示刪除
- 看起來複雜，但習慣了就很有用

---

### `git diff --staged`

**作用**：查看已暫存（staged）的變更

**基本語法**：
```bash
git diff --staged
git diff --cached          # 同義
```

**範例**：
```bash
$ git add app.js
$ git diff --staged
diff --git a/app.js b/app.js
index a1b2c3d..d4e5f6g 100644
--- a/app.js
+++ b/app.js
@@ -10,3 +10,5 @@ const app = express();
 app.use(express.json());
 
-const PORT = 3000;
+const PORT = 5000;
```

✅ 這是即將被提交的內容

---

### `git restore --staged`

**作用**：取消暫存（將檔案從暫存區移出，但保留變更）

**基本語法**：
```bash
git restore --staged <檔案>
```

**範例**：

1️⃣ **取消特定檔案的暫存**：
```bash
$ git status
Changes to be committed:
  modified:   app.js
  modified:   config.json

$ git restore --staged app.js
$ git status
Changes to be committed:
  modified:   config.json

Changes not staged for commit:
  modified:   app.js
```

2️⃣ **取消所有暫存**：
```bash
$ git restore --staged .
```

✅ 檔案的改動保留，只是從暫存區移出

---

### `git reset HEAD`

**作用**：取消暫存（等同於 `git restore --staged`）

**基本語法**：
```bash
git reset HEAD <檔案>
git reset HEAD            # 取消所有暫存
```

**範例**：
```bash
$ git reset HEAD app.js
Unstaged changes after reset:
M       app.js
```

💡 **小提示**：`git restore --staged` 和 `git reset HEAD` 功能相同，新版 Git 建議用前者

---

### `git restore`

**作用**：丟棄檔案的本地改動（恢復到最後提交或暫存區的狀態）

**基本語法**：
```bash
git restore <檔案>                # 丟棄未暫存的改動
git restore --source=<commit> <檔案>  # 恢復到特定提交的版本
```

**常用參數**：
- `--staged`：取消暫存
- `--source=<commit>`：恢復到特定版本

**範例**：

1️⃣ **丟棄檔案改動**：
```bash
$ git restore app.js
# 檔案恢復到上次提交的狀態
# ⚠️ 改動會永遠遺失！
```

2️⃣ **丟棄多個檔案**：
```bash
$ git restore app.js config.js
```

3️⃣ **丟棄所有檔案**：
```bash
$ git restore .
```

⚠️ **重大警告**：`git restore` 會永遠丟棄改動，執行前要確認！

---

### `git checkout -- <file>`

**作用**：丟棄檔案改動（舊方法，等同 `git restore`）

**基本語法**：
```bash
git checkout -- <檔案>
```

**範例**：
```bash
$ git checkout -- app.js
```

💡 **小提示**：新版 Git 建議用 `git restore` 替代

---

### `git reset`

**作用**：重置提交、暫存或工作目錄

**基本語法**：
```bash
git reset --soft <commit>       # 保留所有改動，只重置提交
git reset --mixed <commit>      # 保留工作目錄改動，重置暫存和提交
git reset --hard <commit>       # 完全重置（丟棄所有改動）
```

**三種重置模式**：

| 模式 | 暫存區 | 工作目錄 | 用途 |
|------|--------|----------|------|
| `--soft` | ❌ | ✅ | 撤銷提交，保留改動 |
| `--mixed` | ❌ | ✅ | 撤銷暫存，保留改動 |
| `--hard` | ❌ | ❌ | 完全重置（危險） |

**範例**：

1️⃣ **撤銷上一次提交，保留改動**：
```bash
$ git reset --soft HEAD~1
# 上次提交的內容回到暫存區
$ git status
Changes to be committed:
  modified:   app.js
```

2️⃣ **撤銷暫存**：
```bash
$ git reset --mixed HEAD
# 或直接
$ git reset
```

3️⃣ **完全回到某個提交**：
```bash
$ git reset --hard a1b2c3d
# 所有在 a1b2c3d 之後的改動都會被丟棄
```

⚠️ **警告**：`--hard` 會永遠丟棄改動！

---

### `git revert`

**作用**：創建一個新提交來撤銷某次提交（不改寫歷史）

**基本語法**：
```bash
git revert <commit-hash>
```

**與 `git reset` 的區別**：

| 指令 | 方法 | 歷史 | 何時用 |
|------|------|------|--------|
| `git reset` | 移動 HEAD | 改寫 | 本地開發 |
| `git revert` | 創建新提交 | 保留 | 已推送的提交 |

**範例**：

1️⃣ **撤銷某次提交**：
```bash
$ git log --oneline
a1b2c3d Add user authentication
b2c3d4e Add login feature
c3d4e5f Update README

$ git revert b2c3d4e
# 會打開編輯器讓你寫 revert 訊息
# 創建新提交，內容是 b2c3d4e 的反向操作
```

2️⃣ **指定 revert 訊息**：
```bash
$ git revert b2c3d4e -m "Revert login feature"
```

✅ 原本的提交記錄保留，新增了一個撤銷提交

---

### `git show`

**作用**：查看特定提交的詳細內容

**基本語法**：
```bash
git show <commit-hash>
git show HEAD               # 查看最後一次提交
git show HEAD~1             # 查看倒數第二次提交
```

**範例**：

1️⃣ **查看最後一次提交**：
```bash
$ git show HEAD
commit a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
Author: John Doe <john@example.com>
Date:   Mon May 2 10:30:45 2026 +0800

    Add user authentication

diff --git a/auth.js b/auth.js
new file mode 100644
index 0000000..a1b2c3d
--- /dev/null
+++ b/auth.js
@@ -0,0 +1,50 @@
+// 認證相關代碼
```

2️⃣ **查看特定提交**：
```bash
$ git show b2c3d4e
```

3️⃣ **查看特定檔案在某次提交的內容**：
```bash
$ git show a1b2c3d:app.js
```

💡 **小提示**：可以看到這次提交改了什麼

---

### `git checkout <commit-hash>`

**作用**：回到特定提交的狀態（進入分離頭指針模式）

**基本語法**：
```bash
git checkout <commit-hash>
```

**範例**：
```bash
$ git checkout a1b2c3d
HEAD is now at a1b2c3d Add user authentication
```

⚠️ **注意**：這會進入「分離頭指針」（detached HEAD）狀態
- 在這個狀態下的新提交不屬於任何分支
- 通常不建議這樣做
- 要回到分支，執行 `git checkout main`

---

## 九、進階但實用的功能

### `git stash`

**作用**：臨時儲存工作目錄的改動（放進「暫存區」）

**基本語法**：
```bash
git stash                       # 儲存改動
git stash save "訊息"           # 儲存並加上說明
git stash list                  # 列出所有 stash
git stash pop                   # 取出最近的 stash（並刪除）
git stash apply                 # 取出最近的 stash（不刪除）
git stash drop                  # 刪除 stash
```

**使用情境**：

你正在 feature 分支開發，突然需要去 main 分支修緊急 bug。不想提交未完成的代碼，就可以 stash。

**範例**：

1️⃣ **儲存進行中的改動**：
```bash
$ git status
Changes not staged for commit:
  modified:   app.js
  modified:   config.json

$ git stash
Saved working directory and index state WIP on feature/login: c3d4e5f Add login feature
```

2️⃣ **列出所有 stash**：
```bash
$ git stash list
stash@{0}: WIP on feature/login: c3d4e5f Add login feature
stash@{1}: WIP on main: a1b2c3d Add user authentication
```

3️⃣ **取出最近的 stash**：
```bash
$ git stash pop
On branch feature/login
Changes not staged for commit:
  modified:   app.js
  modified:   config.json
Dropped refs/stash@{0}
```

4️⃣ **取出特定的 stash**：
```bash
$ git stash apply stash@{1}
```

5️⃣ **儲存並加上說明**：
```bash
$ git stash save "Work in progress on login feature"
$ git stash list
stash@{0}: Work in progress on login feature
```

💡 **小提示**：
- `pop` 會刪除 stash，`apply` 不會
- Stash 會保存在本地，不會推送到遠端

---

### `git commit --amend`

**作用**：修改上一次提交（內容或訊息）

**基本語法**：
```bash
git commit --amend
git commit --amend --no-edit      # 只改內容，保留訊息
```

**使用情境**：

提交後發現有小 bug，或忘記包含某些檔案，不想創建新提交。

**範例**：

1️⃣ **修改上次提交訊息**：
```bash
$ git log --oneline -1
a1b2c3d Add user authenticaton  # 打錯字

$ git commit --amend -m "Add user authentication"
[main b2c3d4e] Add user authentication
```

2️⃣ **新增遺漏的檔案**：
```bash
$ git add forgotten_file.js
$ git commit --amend --no-edit
[main b2c3d4e] Add user authentication
```

⚠️ **重要**：
- 只能修改最後一次提交
- 如果已推送到遠端，修改後需要強制推送（`git push -f`）
- 不要在共享分支上強制推送

---

### `git rebase`（簡介）

**作用**：改寫提交歷史，將一系列提交「重新貼上」到另一個基礎

**基本語法**：
```bash
git rebase <分支>
git rebase -i HEAD~3            # 互動式 rebase（編輯 3 個提交）
```

**Rebase vs Merge 的區別**：

| 操作 | 結果 | 歷史 |
|------|------|------|
| Merge | 兩個分支的提交都保留，產生合併提交 | 呈現「真實」歷史 |
| Rebase | 直線歷史，將提交「重新放上」 | 乾淨但改寫 |

**視覺化**：

Merge：
```
main:     A - B - M (合併提交)
         /        \
feature: C - D
```

Rebase：
```
main:  A - B - C' - D'
```

**範例**：

1️⃣ **基本 rebase**：
```bash
$ git checkout feature/login
$ git rebase main
First, rewinding head to replay your work on top of main...
Applying: Add login feature
```

2️⃣ **互動式 rebase（編輯提交）**：
```bash
$ git rebase -i HEAD~3
# 會打開編輯器，讓你選擇對每個提交做什麼
# pick, squash, reword 等指令
```

⚠️ **警告**：
- Rebase 改寫歷史，不要對已推送的分支使用
- 初學者建議用 merge

---

### `git blame`

**作用**：查看檔案每一行是誰在什麼時候改的

**基本語法**：
```bash
git blame <檔案>
git blame -L <開始行>,<結束行> <檔案>
```

**範例**：

```bash
$ git blame app.js
a1b2c3d (John Doe 2026-05-02 10:30:45 +0800  1) const express = require('express');
a1b2c3d (John Doe 2026-05-02 10:30:45 +0800  2) const app = express();
b2c3d4e (Jane Smith 2026-05-01 15:20:30 +0800 3)
c3d4e5f (John Doe 2026-04-30 09:15:20 +0800  4) const PORT = 3000;
```

💡 **小提示**：可以追蹤某行代碼是誰、什麼時候改的

---

### `git log -p`

**作用**：查看提交歷史，並顯示每次提交的詳細改動

**基本語法**：
```bash
git log -p
git log -p -n 3                 # 只看最近 3 次
git log -p --author="John"      # 只看某人的提交
```

**範例**：

```bash
$ git log -p -n 2
commit a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
Author: John Doe <john@example.com>
Date:   Mon May 2 10:30:45 2026 +0800

    Add user authentication

diff --git a/auth.js b/auth.js
new file mode 100644
index 0000000..a1b2c3d
--- /dev/null
+++ b/auth.js
@@ -0,0 +1,50 @@
+// 認證相關代碼
+...
```

💡 **小提示**：適合詳細審視提交的改動

---

## 十、工作流程最佳實踐

### 提交訊息慣例

**好的提交訊息應該包括**：
1. 簡短的主旨（50 字以內）
2. 空行
3. 詳細說明（選擇性）

**常見格式**：

1️⃣ **簡單提交**：
```bash
git commit -m "Add user authentication"
```

2️⃣ **詳細提交**：
```bash
git commit -m "Add user authentication

- Implemented JWT-based authentication
- Added login and logout endpoints
- Added user session management"
```

**提交訊息最佳實踐**：

| ✅ 好 | ❌ 不好 |
|------|--------|
| "Add login feature" | "fix" |
| "Fix payment button bug" | "update" |
| "Update documentation" | "asdfgh" |
| "Refactor database queries" | "random changes" |

**提交訊息模板**：

```
<類型>: <簡短描述>

<詳細說明（選擇性）>

<參考（選擇性）>
```

**類型說明**：
- `feat`: 新功能
- `fix`: 修復 bug
- `docs`: 文檔更新
- `style`: 代碼風格（不影響功能）
- `refactor`: 重構代碼
- `test`: 新增或修改測試
- `chore`: 依賴更新、構建配置等

**範例**：
```bash
git commit -m "feat: Add user authentication

Implemented JWT-based token authentication system
- Added login endpoint
- Added token validation middleware
- Added logout endpoint

Closes #123"
```

---

### 常見工作流程範例

#### Feature Branch 工作流

**流程**：

1️⃣ **從 main 創建功能分支**：
```bash
$ git checkout main
$ git pull                              # 同步最新
$ git checkout -b feature/user-profile
```

2️⃣ **在分支上開發**：
```bash
$ # 編輯檔案、測試、改進...
$ git add .
$ git commit -m "Add user profile page"
$ git add .
$ git commit -m "Add avatar upload"
```

3️⃣ **推送分支**：
```bash
$ git push -u origin feature/user-profile
```

4️⃣ **發起 Pull Request（在 GitHub）**：
- 讓他人審視代碼
- 進行測試
- 修正反饋

5️⃣ **合併回 main**：
```bash
$ git checkout main
$ git pull
$ git merge feature/user-profile
$ git push
```

6️⃣ **刪除分支**：
```bash
$ git branch -d feature/user-profile
$ git push origin --delete feature/user-profile
```

---

#### 日常開發流程

**早上開始**：
```bash
$ git checkout main
$ git pull                  # 獲取他人推送的最新代碼
$ git checkout -b feature/new-feature
```

**開發中**：
```bash
$ # 修改檔案...
$ git status               # 查看改動
$ git diff app.js          # 查看具體改動
$ git add app.js
$ git commit -m "Implement feature X"
```

**有緊急 bug 需要修復**：
```bash
$ git stash                           # 暫存未完成的工作
$ git checkout main
$ git pull
$ git checkout -b hotfix/critical-bug
$ # 修復 bug...
$ git commit -m "Fix critical bug"
$ git push origin hotfix/critical-bug
$ # 發 PR 審核後合併

$ git checkout feature/new-feature    # 回到原分支
$ git stash pop                       # 恢復暫存的工作
```

**準備推送**：
```bash
$ git fetch origin          # 檢查遠端有無新變更
$ git rebase origin/main    # 更新到最新（可選）
$ git push origin feature/new-feature
```

---

### 常見問題排查

#### 問題 1：誤刪了本地分支

**症狀**：
```bash
$ git branch -d feature/important
Deleted branch feature/important (was a1b2c3d).
```

**解決方案**：
```bash
$ git reflog                          # 查看操作歷史
$ git checkout -b feature/important a1b2c3d
# 分支恢復
```

---

#### 問題 2：提交到了錯誤的分支

**症狀**：在 main 上誤提交了開發代碼

**解決方案**：

1️⃣ **撤銷提交（保留代碼）**：
```bash
$ git reset --soft HEAD~1
# 提交被撤銷，代碼回到暫存區
```

2️⃣ **創建新分支**：
```bash
$ git checkout -b feature/correct-branch
$ git commit -m "Add feature"
$ git push -u origin feature/correct-branch
```

3️⃣ **main 恢復原狀**：
```bash
$ git checkout main
$ git reset --hard origin/main
```

---

#### 問題 3：不小心 push --force 了

**症狀**：強制推送覆蓋了他人的代碼

**解決方案**：

1️⃣ **查看被覆蓋的提交**：
```bash
$ git reflog origin/main
```

2️⃣ **恢復提交**：
```bash
$ git push origin <commit-hash>:main
```

⚠️ **預防**：使用 `git push --force-with-lease` 而不是 `--force`，這樣如果有人已推送新代碼就會拒絕

---

#### 問題 4：忘記提交前同步遠端

**症狀**：Push 時出現衝突

**解決方案**：

```bash
$ git push
To https://github.com/john/my-repo.git
 ! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to

$ git pull --rebase         # 或 git pull
# 解決衝突（如果有）
$ git push
```

---

#### 問題 5：提交訊息寫錯了

**症狀**：提交訊息有打字錯誤，且還沒推送

**解決方案**：

```bash
$ git commit --amend -m "修正後的訊息"
# 只能修改最後一次提交
```

**如果已推送**：
```bash
$ git commit --amend -m "修正後的訊息"
$ git push -f origin main
# ⚠️ 強制推送，如果多人協作要協調！
```

---

### 實用的 Git 別名設定

**設定別名以簡化命令**：

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'restore --staged'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual 'log --graph --oneline --all'
```

**使用別名**：
```bash
$ git st                    # 等同 git status
$ git co feature/login      # 等同 git checkout feature/login
$ git ci -m "Add feature"   # 等同 git commit -m "Add feature"
```

---

## 總結

恭喜！你已經掌握了 Git 的核心概念和常用指令。

**回顧重點**：

1. ✅ **日常工作流**：add → commit → push
2. ✅ **分支管理**：branch、checkout、merge
3. ✅ **協作同步**：fetch、pull、push
4. ✅ **撤銷操作**：restore、reset、revert
5. ✅ **問題排查**：log、diff、show、blame

**下一步建議**：

- 💻 在實際項目中多練習這些指令
- 📖 學習 GitHub/GitLab 的 Pull Request 工作流
- 🔧 探索更進階的功能（rebase、cherry-pick）
- 📚 建立好的提交習慣

**有用的資源**：
- 官方文檔：https://git-scm.com/doc
- 互動學習：https://learngitbranching.js.org/
- 視覺化工具：使用 VS Code 的 Git Graph 擴充功能

---

**祝你的 Git 之旅順利！🚀**
