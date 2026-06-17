refactor: 收尾 Phase 10.3 並補強 auth 安全設定

這次提交主要把 Phase 10.3 真正收尾，同時順手補上登入相關的安全基線。主軸一樣是契約收斂與文件對齊，但另外把 auth 目前仍採 `localStorage + Bearer token` 的現況重新檢查一遍，補上 cookie / session policy 與 auth response 的 cache control，避免看起來像有做安全收斂，實際上登入主線還留著明顯空白。

---

一、Phase 10.3 收尾與文件同步

- 新增：
  - `docs/reference/Phase10_3_protected_fields_與_frontend_不可自送欄位說明_2026-06-17.md`

- 調整：
  - `docs/重構計畫.md`
  - `docs/進度追蹤.md`
  - `docs/phases/Phase10_契約收斂與前後端對齊規劃_2026-06-12.md`
  - `docs/reference/Phase10_3_後端回應契約收斂實作整理_2026-06-17.md`

- 本輪收斂重點：
  - 將 10.3 原本尚未勾掉的兩個尾項正式補完：
    - `protected fields / frontend 不可自送欄位說明`
    - `frontend consumer` 主線範圍內剩餘對齊項
  - 將 `client-owned fields`、`server-owned / protected fields`、`route-owned identifiers` 的差異整理成正式說明文件
  - 明確把剩餘 `copilot / agent` 內層動態 payload、測試 mock cast、DOM event typing 等項目降級為後續維護，不再算作 10.3 阻塞
  - 將 `重構計畫`、`進度追蹤`、總 Phase 10 規劃與 10.3 實作整理同步回寫，讓狀態與實作一致

---

二、auth / login 安全設定補強

- 調整：
  - `backend/app.py`
  - `backend/blueprints/auth.py`
  - `backend/tests/blueprints/test_auth.py`

- 本輪安全收斂重點：
  - 明確固定目前 JWT 使用位置為 `headers`，避免未來混入 cookie token 路徑時責任不清
  - 補上 cookie / session 安全基線：
    - `SESSION_COOKIE_HTTPONLY = True`
    - `SESSION_COOKIE_SAMESITE = Strict`（可由 `COOKIE_SAMESITE` 覆寫）
    - `SESSION_COOKIE_SECURE = production only`
    - `JWT_COOKIE_SAMESITE = Strict`
    - `JWT_COOKIE_SECURE = production only`
    - `JWT_COOKIE_CSRF_PROTECT = True`
  - 新增 `COOKIE_SAMESITE` 解析與合法值限制，只允許 `Strict / Lax / None`
  - `auth` 相關 response（register / login / logout / me / refresh）統一補上：
    - `Cache-Control: no-store`
    - `Pragma: no-cache`
  - 原因是目前 token 仍由 `/auth/login` 與 `/auth/refresh` 直接回在 JSON body，既然還沒改成 HttpOnly refresh cookie，就至少先避免被瀏覽器或中介快取

- 補充判定：
  - 這次沒有把登入流程直接改成 cookie-based auth
  - 目前前端仍是 `localStorage + Authorization Bearer`
  - 所以 `SameSite=Strict` 這次補的是 backend cookie / session policy 基線，而不是把現有 token 流改成吃 cookie
  - 若後續要進一步升級登入安全，下一步應該是評估：
    - `refresh token` 改存 `HttpOnly cookie`
    - access token 是否維持記憶體 / header 模式
    - cross-origin 前後端下 `Strict` / `Lax` / `None` 的實際部署相容性

---

三、驗證

- `python -m py_compile backend\\app.py backend\\blueprints\\auth.py`
  - PASS
- `venv\\Scripts\\python.exe -m pytest tests/blueprints/test_auth.py -q`
  - PASS
  - 補驗證：
    - login response token payload 仍正常
    - login / refresh response 已補 `no-store` / `no-cache` header

---

四、補充

- 這次提交雖然看起來同時碰了 Phase 10 文件與 auth 安全，但主題其實一致：把原本「已經形成慣例、但還沒被正式落成規則」的部分收成可維護狀態
- 10.3 這邊收的是契約與文件閉環；auth 這邊收的是登入安全基線，不直接改壞目前前後端 header token 流
