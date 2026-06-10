# frontend/src/services

這層負責前端對後端 API / socket 的呼叫封裝，讓 view、component、store 不需要直接散落 `fetch` 或 axios 細節。

## 常見檔案

- `api.ts`: 共用 API client 與基礎請求設定
- `copilotService.ts`: Copilot / Agent 相關 API 呼叫
- `taskService.ts`, `timelineService.ts`, `groupService.ts`: 各 domain API 封裝
- `profileService.ts`, `notificationService.ts`, `todoService.ts`, `trashService.ts`: 其餘 domain API 封裝
- `socketService.ts`: 即時連線相關封裝

## 這層應該負責什麼

- 呼叫後端 API
- 統一 request / response 基礎處理
- 必要的前端資料轉接
- 把同一個 domain 的 API 呼叫集中，避免頁面自己散打

## 不應該放什麼

- Vue component 顯示邏輯
- 頁面互動流程控制
- 複雜商業規則判斷
- 大量前端格式化細節

## 與其他前端目錄的分界

### `services/` 負責

- 打 API
- 組 query / body / headers
- 處理共用 request 失敗邏輯
- 必要的 response 轉接

### `types/` 負責

- 定義 API model / UI model 的型別
- 讓 service 與 component 共享穩定型別

### `utils/` 負責

- 純資料轉換
- 格式化
- 與 Vue 無關的 helper

### `components/` / `views/` 負責

- 顯示畫面
- 使用者互動
- 畫面層狀態協調

一句話版本：

- `services/` 解決「怎麼跟後端講話」
- `types/` 解決「資料應該長什麼樣」
- `components/` / `views/` 解決「畫面怎麼呈現」

## 修改判斷

- 如果是「前端怎麼打這支 API」或「response 先做一層轉接」，改這裡
- 如果是按鈕點擊後怎麼更新畫面、怎麼顯示錯誤，通常應回到 component / view / store
- Copilot plan / confirm / execute 的前端對接，優先看 `copilotService.ts`

## 建議原則

- 一個 service 盡量對應一個 domain
- 這層回傳的資料要盡量穩定，避免 component 到處自己猜 API shape
- 若 response 需要小幅轉接，可在這層或 `utils/` 做；若已是大型 UI 映射，通常不該放這裡

## 契約邊界原則

### 前端 service 的「契約」是什麼

在前端這邊，service 的契約通常不是 Pydantic，而是：

- request 參數 shape
- 回傳資料 shape
- 錯誤物件或例外的外型

因此這層要盡量做到：

- 同一支 function 的入參固定
- 回傳型別固定
- component 不需要知道底層 API 的零碎差異

### 什麼情況該在 service 做 mapping

- 後端欄位名稱不夠直觀，前端要做一層輕量轉接
- 多支 API 共用某個錯誤格式，需要先統一
- response 需要補成較穩定的前端 model

### 什麼情況不該在 service 做 mapping

- 單純是顯示格式，例如日期顯示、顏色、文案
- 大量畫面專屬的衍生欄位
- 只在單一 component 內成立的暫時狀態

## 測試上怎麼看這層

這層若要補測，通常優先驗證：

- request 參數是否正確送出
- response 是否被正確轉接
- 錯誤是否被統一處理

如果你在測的是：

- 點按鈕後畫面有沒有變
- loading / error UI 有沒有顯示

那通常應回到 component test，而不是 service test。
