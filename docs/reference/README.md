# Reference 目錄說明

`docs/reference/` 存放高頻查閱、需要與實作保持接近的參考資料，例如 API 契約、錯誤碼、OpenAPI、環境變數、payload 規格與階段收斂後的查表型整理。

## 責任範圍

1. API、request / response、錯誤碼與 payload 契約。
2. OpenAPI 靜態輸出與維護說明。
3. 後端 contract、frontend type、service consumer 的對照索引。
4. Phase 完成後仍會被後續維護反覆查閱的整理文件。

## 相鄰目錄邊界

1. 階段規劃與階段驗收放 `docs/phases/`。
2. 架構設計與責任邊界放 `docs/architecture/`。
3. 操作步驟與排障流程放 `docs/runbooks/`。
4. Git、CI/CD、文件流程規範放 `docs/guides/`。

## 維護原則

1. reference 文件應描述目前實作狀態，不手動創造尚未存在的規格。
2. 若內容與程式碼不同步，先回到真相來源修正，例如 `backend/contracts/`、route / service、OpenAPI builder 或 tests。
3. 契約相關文件應標清楚 `stable`、`partial`、`dynamic`、`binary` 或 `legacy-flexible` 等狀態，避免把彈性區誤認為漏做。
4. 主要 API 變更時，應同步檢查相關 reference 文件是否需要更新。
