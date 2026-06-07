# CI/CD 最小流程（Learnlink）

> 最後更新：2026-05-27  
> 目的：用最小成本確保「改動可測、可審、可回滾」

---

## 1. 適用範圍

1. 本專案所有進入 `main` 的程式碼變更
2. 前端與後端 workflow 驗證
3. PR 合併與部署觸發行為

---

## 2. 標準流程（固定執行）

1. 從 `main` 開新分支（`feature/*`、`fix/*`）
2. 本地先跑必要測試
3. push 分支並建立 PR 到 `main`
4. 等 GitHub Actions checks 全綠
5. 完成 code review 後 merge
6. merge 到 `main` 後才觸發部署（或手動觸發 deploy workflow）

---

## 3. 本地最小驗證指令

## Backend

```powershell
cd backend
venv\Scripts\python.exe -m pytest
```

## Frontend

```powershell
cd frontend
npm ci
npm run test:coverage
npm run build
```

---

## 4. PR 必要條件（Merge Gate）

`main` 分支建議啟用以下 Branch Protection：

1. Require a pull request before merging
2. Require status checks to pass before merging
3. Required checks 至少包含：
 - `Backend Tests`
 - `Frontend Tests`（或 `Frontend CI`）
4. Restrict direct push to `main`

---

## 5. Workflow 原則

1. CI workflow（測試）與 Deploy workflow（上線）分離
2. PR 階段只跑測試，不直接部署
3. Deploy 僅在 `push main` 或 `workflow_dispatch` 觸發

---

## 6. 失敗處理（最小回應）

1. Check fail：先修復再重跑，不以 `re-run` 取代修正
2. Merge 後問題：優先用小修復 PR；必要時快速回滾到前一穩定 commit
3. 部署失敗：保留最近一次可用版本，避免直接在 `main` 熱修未測代碼

---

## 7. PR 描述最小模板（建議）

1. 變更摘要：這次改了什麼、為什麼改
2. 風險：可能影響的區域
3. 測試證據：本地與 CI 結果
4. 回滾方式：若上線異常如何退回

