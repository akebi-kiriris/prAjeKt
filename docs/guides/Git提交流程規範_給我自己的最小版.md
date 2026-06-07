# Git 提交流程規範（給我自己的最小版）

> 適用：Learnlink 專案日常開發  
> 目標：固定流程、降低失誤、可回滾

---

## 1. 一般流程（固定照做）

1. 先確認目前分支與變更
2. 從 `main` 切出功能分支
3. 本地測試通過
4. `git add` + `git commit`（使用檔案式 commit message）
5. `git push -u origin <branch>`
6. 開 PR 到 `main`
7. 等 CI 全綠後 merge

---

## 2. 建議指令模板

```powershell
# 0) 檢查狀態
git status --short
git branch --show-current

# 1) 開分支（例）
git checkout -b feature/phase8-6-ci-hardening

# 2) 本地驗證（依改動選擇）
cd backend
venv\Scripts\python.exe -m pytest
cd ..\frontend
npm run guardrails:payload
npm run build
cd ..

# 3) 提交（建議使用 -F）
git add .
git commit -F docs/guides/commit-message.md

# 4) 推送
git push -u origin feature/phase8-6-ci-hardening
```

---

## 3. Commit Message 規範

1. 第一行：一句話摘要（祈使句）
2. 內文分段：`背景`、`本次變更`、`驗證`
3. 盡量列出「改了哪些檔案/模組」與「測試結果」
4. 不要把無關改動混在同一個 commit

---

## 4. 禁止事項（避免踩雷）

1. 不直接在 `main` 做日常開發與提交
2. 不用 `git reset --hard` 清工作區（除非明確要回滾）
3. 不用 `git push --force` 覆蓋共享分支（除非確認只有自己在用）
4. 不跳過測試直接開 PR

---

## 5. 出問題時怎麼做

1. commit 前發現多加檔案：`git restore --staged <file>`
2. commit 訊息寫錯但未 push：`git commit --amend -F docs/guides/commit-message.md`
3. push 後發現問題：再開修復 commit，不要改歷史
4. 需要回滾：優先用新 commit revert，不做破壞性清除
