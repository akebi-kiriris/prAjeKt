# Backend Service Contracts 目錄說明

`backend/services/contracts/` 用於定義後端 service 與 agent tool 的資料契約。此目錄的核心目標是讓輸入輸出 schema、欄位限制與錯誤外型保持明確，而不是在流程各處任意傳遞模糊 `dict`。

## 內容範圍

本目錄適合存放以下內容：

1. Domain request/response schema
2. agent tool input/output model
3. success / error envelope 定義
4. 純資料層級的正規化與驗證規則

## 責任邊界

本目錄應負責：

1. 欄位型別與結構定義
2. 必填、選填與格式限制
3. 純契約層級的 validator 與正規化
4. 穩定的 tool I/O 外型

以下內容不應放在本目錄：

1. 商業流程判斷
2. repository / database 查詢
3. HTTP route 控制
4. LangGraph 節點流程與執行順序

## 相鄰目錄邊界

1. `services/` 負責合法資料進來後要如何執行。
2. `tools/` 負責將已驗證契約接到 agent 工具入口。
3. `blueprints/` 負責 API request 來源與 HTTP 邊界。
4. 若驗證需要查 DB、看權限或依賴流程狀態，通常應回到 service 層。

## 撰寫原則

1. 優先使用明確 schema 定義欄位與限制。
2. 純欄位驗證與正規化可留在本層。
3. 契約名稱、欄位語意與錯誤外型應保持穩定。
4. 對外契約變更時，應同步檢查 consumer、tool handler 與測試。
