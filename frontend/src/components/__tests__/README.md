# frontend/src/components/__tests__

這層放前端 component 測試，重點是驗證元件互動、顯示結果與使用者看得到的行為。

## 目前檔案

- `CopilotDock.test.ts`

## 這層應該測什麼

- props 改變後畫面是否正確更新
- 事件觸發後是否有正確 emit 或互動結果
- loading / error / empty state 是否正確顯示
- 關鍵使用者流程是否可通過

## 這層不主要測什麼

- API 參數是否組得正確
- service 裡的 mapping 細節
- 純工具函式的每個分支

這些通常更適合落在：

- `frontend/src/services/`
- `frontend/src/utils/`
- 或對應的低層單元測試

## 與 service 測試的分界

### component test 比較像在驗證

- 使用者看到了什麼
- 點下去之後發生了什麼
- 某個狀態下畫面有沒有正確反應

### service test 比較像在驗證

- API 是不是被正確呼叫
- response 有沒有被正確轉接
- 錯誤有沒有被統一處理

一句話版本：

- component test 測「行為與畫面」
- service test 測「資料與呼叫邊界」

## 不應該過度測什麼

- 純工具函式內部細節
- 第三方函式庫自己的行為
- 與畫面無關的低層實作細節

## 測試判斷

- 如果你在乎的是「使用者會看到什麼、點下去會發生什麼」，優先寫這層測試
- 如果你在乎的是「資料怎麼轉換」，可能更適合測 `utils/` 或 `services/`

## 建議的 component test 檢查表

- 是否有 render 出關鍵文字或按鈕
- props 改變後是否顯示對應狀態
- 使用者操作後是否 emit 正確事件
- loading / error / empty state 是否有覆蓋
- 關鍵流程是否不依賴實際後端也能穩定驗證
