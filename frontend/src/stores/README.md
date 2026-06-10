# frontend/src/stores

這層放 Pinia store，負責前端跨頁或跨區塊共享的狀態。

## 目前 store 主題

- `auth.ts`: 登入與使用者驗證狀態
- `groups.ts`, `tasks.ts`, `timelines.ts`, `todos.ts`, `profile.ts`: 各 domain 狀態
- `notifications.ts`: 通知狀態

## 這層應該負責什麼

- 跨元件共享狀態
- 前端狀態快取
- 明確的前端 state transition

## 不應該放什麼

- 太細碎、只在單一元件使用的區域狀態
- 大量 DOM / UI 細節操作
- 後端 payload 格式驗證規則

## 修改判斷

- 若狀態需要被多個 view / component 共同讀寫，考慮放 store
- 若只是單頁局部狀態，先留在 view 或 component
