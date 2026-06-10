# frontend/src/utils

這層放純函式工具與資料轉接 helper，原則上不依賴 Vue component、Pinia store 或畫面生命週期。

可以把它理解成：

- `types/` 描述資料長什麼樣
- `utils/` 負責把資料整理、轉換、驗證、格式化
- `components/` / `views/` 再拿整理好的結果去顯示

## 目前常見用途

- `apiError.ts`
  - API 錯誤整理
- `formatters.ts`
  - 顯示格式化
- `payloadMappers.ts`
  - payload 映射
- `validators.ts`
  - 前端欄位驗證
- `timelineDetailUtils.ts`, `taskDetails.ts`, `ganttPopup.ts`
  - 特定 domain 的輔助邏輯

## 這層應該負責什麼

- 純資料轉換
- 格式化
- payload mapping
- 前端欄位驗證 helper
- 不依賴畫面生命週期的 domain 輔助函式

## 這層不應該放什麼

- API 請求
- Pinia state 管理
- 大量 template 專屬互動流程
- 依賴 Vue reactivity 的狀態操作

## 與其他前端目錄的分界

### `utils/` 負責

- 純函式
- 相同輸入得到可預期輸出
- 不需要 component instance 就能執行

### `composables/` 負責

- 與 reactive state 密切相關的重用邏輯
- 使用 `ref`、`computed`、生命週期或互動流程的程式

### `services/` 負責

- 呼叫 API
- 回傳資料邊界封裝

### `types/` 負責

- 型別本身
- 不負責函式行為

一句話版本：

- `utils/` 是不靠 Vue 也能跑的工具箱

## validator / formatter / mapper 的分界

這三種很常越寫越混，建議這樣看：

### validator

回答的是：

- 這個值合不合法
- 不合法時錯在哪

例如 [frontend/src/utils/validators.ts](C:/Users/USER/Desktop/0611/0611/Learnlink/frontend/src/utils/validators.ts:1)：

- `validateRequired`
- `validateEmail`
- `validatePassword`
- `validateDateRange`

適合特徵：

- 回傳錯誤訊息或通過結果
- 只檢查值，不負責畫面

### formatter

回答的是：

- 這個值要怎麼顯示比較好

例如：

- 日期顯示
- 數字顯示
- 文案標籤轉換

### mapper

回答的是：

- 資料要怎麼從一種 shape 轉成另一種 shape

例如：

- 後端 payload 轉前端 model
- 前端表單資料轉 API request body

## 什麼情況該放 utils

- 函式輸入輸出清楚
- 不需要 component instance
- 不依賴 router / store / lifecycle
- 在多個地方都有機會重用

## 什麼情況不該放 utils

- 函式已經要讀寫 reactive state
- 函式本身跟單一 component 結構高度綁定
- 函式開始牽涉 API 呼叫或 UI 流程控制

如果一個 helper 開始需要：

- `ref`
- `computed`
- `watch`
- `onMounted`

那通常就更像 composable，不像 utils。

## 測試上怎麼看這層

這層很適合做低層單元測試，因為：

- 輸入輸出明確
- 不需要 mount component
- 容易覆蓋邊界條件

特別適合測：

- validator 的各種錯誤分支
- mapper 的欄位轉換
- formatter 的特殊輸入

## 修改判斷速查

- 想驗證欄位格式：先看 `validators.ts`
- 想把資料從 A shape 轉成 B shape：先看 mapper 類 helper
- 想顯示更友善文字：先看 formatter 類 helper
- 若函式開始依賴大量 reactive state，可能更適合 composable 或 component
