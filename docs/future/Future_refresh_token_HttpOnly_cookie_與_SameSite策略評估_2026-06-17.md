# Future：refresh token 改為 HttpOnly cookie 與 SameSite 策略評估

> 日期：2026-06-17  
> 狀態：future backlog  
> 背景：Phase 10.3 收尾時，已先補 backend cookie / session policy 與 auth response `no-store`，但目前登入主線仍是 `localStorage + Authorization Bearer`，尚未正式改成 cookie-based refresh flow。

---

## 1. 目前狀態

目前 Learnlink 的登入流程是：

1. `/api/auth/login` 回傳 `access_token` 與 `refresh_token`
2. frontend 存進 `localStorage`
3. request 透過 `Authorization: Bearer <access_token>` 呼叫
4. 401 時由 `frontend/src/services/api.ts` 使用 `refresh_token` 打 `/api/auth/refresh`

這代表：

1. 現在主要風險不在 cookie 遺失 `SameSite`
2. 而是在 token 仍可被前端 JS 直接讀取
3. 所以單純補 backend cookie policy，還不等於完成登入安全升級

---

## 2. 為什麼這件事值得做

若 `refresh_token` 仍長期放在 `localStorage`：

1. 一旦前端遭遇 XSS，refresh token 也可能被讀走
2. refresh token 壽命通常比 access token 長，風險更大
3. 即使 access token 很短命，refresh token 洩漏仍能持續換發新 token

比較合理的下一步通常是：

1. access token 保持短效
2. refresh token 改為 `HttpOnly cookie`
3. refresh endpoint 改成讀 cookie，不再讓前端手持 refresh token

---

## 3. 預期目標

若之後啟動這項重構，目標應該是：

1. `refresh_token` 不再暴露給前端 JS
2. `/auth/refresh` 改走 cookie-based refresh
3. 明確決定部署情境下的 `SameSite` 策略
4. 保持現有前端使用 `Authorization` header 的主線盡量少破壞

---

## 4. 建議重構方向

### 4.1 第一階段

1. login 成功後：
   - body 只回 `access_token` 與必要 user payload
   - `refresh_token` 改用 `HttpOnly` cookie 下發
2. refresh 時：
   - frontend 不再從 `localStorage` 取 refresh token
   - backend 從 cookie 讀 refresh token
3. logout 時：
   - backend 主動清除 refresh cookie

### 4.2 第二階段

1. 評估 access token 是否保留在 `localStorage`
2. 或改為只放 memory，由重整時走 `/auth/refresh` 取新 access token
3. 視 DX 與安全需求決定是否進一步縮短 access token 壽命

---

## 5. SameSite 策略要特別確認的事

這塊不能只憑直覺直接寫 `Strict`，要先看實際部署型態。

### 5.1 若 frontend / backend 為同 site

例如：

1. 同主網域
2. 反向代理後看起來同站

那麼 `SameSite=Strict` 或 `Lax` 通常較有機會可行。

### 5.2 若 frontend / backend 為跨 site

例如目前常見情境：

1. frontend 在 Firebase Hosting
2. backend 在 Railway / 其他 API domain

這種情況若真的屬 cross-site，則：

1. `SameSite=Strict` 可能直接讓 refresh cookie 不會被帶上
2. `SameSite=Lax` 也未必足夠
3. 很可能必須用 `SameSite=None; Secure`

所以這件事要先以實際部署網域關係驗證，而不是只用「Strict 比較安全」直接拍板。

---

## 6. 實作前要確認的問題

1. 正式環境 frontend 與 backend 是否屬同 site？
2. `/auth/refresh` 是否接受只靠 cookie，不再接受 `Authorization: Bearer refresh_token`？
3. CORS 與 `withCredentials` 是否已完整對齊？
4. logout 是否要由 backend 主動清 cookie？
5. 測試是否要補：
   - login set-cookie
   - refresh read-cookie
   - logout clear-cookie
   - cross-origin credential flow

---

## 7. 建議落點

這項工作比較像：

1. auth 安全收斂
2. session / token 策略調整
3. 前後端登入流程重構

它不適合混在 10.3 這種契約收斂尾聲直接硬做，比較適合另開一個 auth security / session strategy 小 phase。

---

## 8. 一句話版

目前只是先補了 cookie policy 與 auth response 不快取；  
真正更有感的下一步，是把 `refresh_token` 從 `localStorage` 移到 `HttpOnly cookie`，並依實際部署型態重新決定 `SameSite=Strict / Lax / None`。
