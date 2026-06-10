# frontend/src/composables

這層放可重用的 Composition API 邏輯，讓 component 不必重複寫同一套互動流程。

## 目前檔案

- `useConfirm.ts`: 確認操作相關邏輯

## 這層應該負責什麼

- 可被多個 component 重用的互動邏輯
- 與 Vue reactivity 高度相關，但不綁定單一畫面結構的程式

## 不應該放什麼

- 純字串 / 陣列工具函式：放 `utils/`
- API 封裝：放 `services/`
- 只服務單一大型元件且脫離該元件就不成立的零碎邏輯
