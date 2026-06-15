# Backend Contracts 目錄說明

`backend/contracts/` 用於定義後端共用契約層，供 blueprint、service 與 agent tool 共用資料契約。此目錄的核心目標是讓輸入輸出 schema、欄位限制與錯誤外型保持明確，而不是在流程各處任意傳遞模糊 `dict`。

## 內容範圍

本目錄適合存放以下內容：

1. Domain request/response schema
2. agent tool input/output model
3. success / error envelope 定義
4. 純資料層級的正規化與驗證規則
5. 已抽出的共用 request contract（供 blueprint / service / tool 共用）

以下情況通常不需要硬抽到本目錄：

1. 只服務單一路由、沒有共用價值的 request schema
2. 純 HTTP 層細節、且不會進入 service / tool 共用邊界的 payload
3. 只為了形式一致而搬家的 route 專屬 schema

## 目前已收斂的 request contract

1. `task_contracts.py`
2. `timeline_contracts.py`
3. `knowledge_contracts.py`
4. `auth_contracts.py`
5. `profile_contracts.py`
6. `todo_contracts.py`
7. `group_contracts.py`
8. `shared_fields.py`

## 命名慣例

在仍採用「按功能聚合」的前提下，優先保持 class 命名穩定，而不是過早把檔案再細拆成多層目錄。

建議慣例：

1. `XxxRequest`
   - 給 blueprint 外部入口 payload 使用
   - 描述 request shape、必填欄位、基本格式限制
2. `XxxInput`
   - 給 service 邊界使用
   - 描述 service 真正想吃的資料型態與正規化結果
3. `XxxResponse`
   - 給回傳契約使用
   - 目前可只在高風險或已收斂主線補
4. `shared_fields.py`
   - 只放真正跨 domain 共用的純欄位規則
   - 例如 enum、日期格式、priority、member role、正整數 list 正規化

目前不建議為了形式完整就先拆成 `requests/`、`inputs/`、`responses/` 子資料夾；以目前專案大小，維持 `task_contracts.py`、`timeline_contracts.py` 這種按功能聚合的方式較容易維護。

## 責任邊界

本目錄應負責：

1. 欄位型別與結構定義
2. 必填、選填與格式限制
3. 純契約層級的 validator 與正規化
4. 穩定的 tool I/O 外型
5. 已確認可跨 blueprint / service / tool 共用的 schema

以下內容不應放在本目錄：

1. 商業流程判斷
2. repository / database 查詢
3. HTTP route 控制
4. LangGraph 節點流程與執行順序
5. 需要查 DB、看權限、看資源存在性後才成立的驗證

## 相鄰目錄邊界

1. `services/` 負責合法資料進來後要如何執行。
2. `services/tools/` 負責將已驗證契約接到 agent 工具入口。
3. `blueprints/` 負責 API request 來源與 HTTP 邊界。
4. 若 route request schema 已被抽到 `contracts/`，blueprint 仍只負責呼叫與錯誤映射，不擁有業務規則。
5. 若驗證需要查 DB、看權限或依賴流程狀態，通常應回到 service 層。
6. `blueprints/validation.py` 屬於 HTTP 驗證與錯誤映射基礎設施，不是 schema 倉庫。

## 撰寫原則

1. 優先使用明確 schema 定義欄位與限制。
2. 純欄位驗證與正規化可留在本層。
3. 契約名稱、欄位語意與錯誤外型應保持穩定。
4. 對外契約變更時，應同步檢查 consumer、tool handler 與測試。
5. 優先抽「真的共用」的欄位規則，不為了形式一致把純 route 細節硬塞進共用層。
6. 若同一份欄位規則同時出現在 blueprint、service、tool，應優先收斂成單一契約來源。
7. 若單一 domain contract 檔案變得過胖，再考慮拆成子檔；不要在專案尚小時過早細分目錄。
