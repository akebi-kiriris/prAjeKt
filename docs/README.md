# Docs 索引與目錄規範

`docs/` 用於集中管理 Learnlink 的專案文件，包含階段規劃、架構說明、操作手冊、參考資料與學習筆記。本文件作為 `docs/` 的入口索引與放置規範，目的在於維持文件結構清楚、查找一致、主題分層明確。

## 目錄結構

```text
docs/
├── README.md
├── 重構計畫.md
├── 進度追蹤.md
├── phases/
├── architecture/
├── runbooks/
├── reference/
├── guides/
├── workflows/
├── future/
├── changelog/
├── learning/
├── assets/
└── .obsidian/
```

## 根層文件

`docs/` 根層僅保留跨目錄入口或持續維護中的主文件：

1. `README.md`
   - `docs/` 的總索引與放置規範。
2. `重構計畫.md`
   - 專案整體重構計畫與階段性細節。
3. `進度追蹤.md`
   - 當前進度、完成狀態與下一步追蹤。

若文件已明確屬於某個主題，原則上應放入對應子目錄，而不是留在 `docs/` 根層。

## 子目錄用途

### `docs/phases/`

存放 Phase 規劃、階段詳解、階段收斂紀錄與同一階段下的補測或修復計畫。

### `docs/architecture/`

存放系統設計、模組責任、分層邊界、資料流與長期有效的技術設計說明。

### `docs/runbooks/`

存放部署、遷移、啟動、排障與其他可執行操作手冊。

### `docs/reference/`

存放高頻查表型文件，例如 API 端點、錯誤碼、payload 契約、環境設定對照。

### `docs/guides/`

存放開發流程、協作規範、Git/CI/CD 流程與文件維護規範。

### `docs/workflows/`

存放 AI workflow、tool workflow、流程範例與操作編排說明。

### `docs/future/`

存放尚未進入主線排程的改進提案、重構草稿與後續待驗證方向。

### `docs/changelog/`

存放具時間序的變更紀錄、整理紀錄或歷史更新摘要。

### `docs/learning/`

存放個人學習筆記、技術整理、面試準備與非正式專案文檔。

### `docs/assets/`

存放圖片、附件、示意圖與其他非 Markdown 資源。

### `docs/.obsidian/`

保留 Obsidian 本地設定，不作為正式文檔內容的一部分。

## 新文件放置規則

新增文件時，請依內容性質選擇放置位置：

1. Phase 規劃、階段總結、階段修復計畫：放 `docs/phases/`
2. 架構說明、設計紀錄、責任邊界：放 `docs/architecture/`
3. 部署、遷移、啟動、排障手冊：放 `docs/runbooks/`
4. API、錯誤碼、契約、環境對照：放 `docs/reference/`
5. 開發流程、Git/CI/CD、文件規範：放 `docs/guides/`
6. AI 或工具流程範例：放 `docs/workflows/`
7. 未來提案、待驗證構想、暫緩項目：放 `docs/future/`
8. 歷史變更紀錄：放 `docs/changelog/`
9. 學習筆記、面試整理、個人技術摘要：放 `docs/learning/`
10. 圖片、附件與其他素材：放 `docs/assets/`

## 維護原則

1. 同一份資訊應盡量維持單一主檔，避免多處重複後內容漂移。
2. `重構計畫.md` 保留較完整的規劃內容，`進度追蹤.md` 保留精簡的狀態摘要。
3. 若文件已具有明確分類，應優先移入對應子目錄，不持續累積在 `docs/` 根層。
4. 學習性質或個人整理內容，應與正式專案文檔分開維護。
