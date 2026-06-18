# Guides 目錄說明

`docs/guides/` 存放開發流程、協作規範、Git / CI / CD、文件更新流程與其他「如何做事」的穩定指引。

## 責任範圍

1. Git commit、branch、PR 與發布流程。
2. CI/CD 操作與檢查流程。
3. 文件更新、同步與分類規範。
4. 可跨多個 Phase 重複使用的工作方法。

## 相鄰目錄邊界

1. 具體部署或排障步驟放 `docs/runbooks/`。
2. 階段計畫放 `docs/phases/`。
3. API 或契約查表放 `docs/reference/`。
4. 個人學習與筆記放 `docs/learning/`。

## 維護原則

1. guide 應保持穩定，不記錄一次性進度。
2. 若某流程已不再使用，應明確標註過時或移除。
3. 新增 guide 時應回答「什麼時候用」、「照什麼順序做」、「完成後如何確認」。
4. commit message 範例應與 repo 實際歷史風格一致。
