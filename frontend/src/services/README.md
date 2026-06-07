# frontend/src/services

這層負責前端對後端 API / socket 的呼叫封裝，讓 view、component、store 不需要直接散落 `fetch` 或 axios 細節。

## 常見檔案

- `api.ts`: 共用 API client 與基礎請求設定
- `copilotService.ts`: Copilot / Agent 相關 API 呼叫
- `taskService.ts`, `timelineService.ts`, `groupService.ts`: 各 domain API 封裝
- `socketService.ts`: 即時連線相關封裝

## 這層應該負責什麼

- 呼叫後端 API
- 統一 request / response 基礎處理
- 必要的前端資料轉接

## 不應該放什麼

- Vue component 顯示邏輯
- 頁面互動流程控制
- 複雜商業規則判斷

## 修改判斷

- 如果是「前端怎麼打這支 API」或「response 先做一層轉接」，改這裡
- 如果是按鈕點擊後怎麼更新畫面、怎麼顯示錯誤，通常應回到 component / view / store
- Copilot plan / confirm / execute 的前端對接，優先看 `copilotService.ts`
