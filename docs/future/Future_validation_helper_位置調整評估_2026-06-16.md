# Future：validation helper 位置調整評估

> 日期：2026-06-16  
> 狀態：future backlog  
> 來源：Phase 10.2 後續確認清單第 2 點

---

## 1. 背景

目前 `backend/blueprints/validation.py` 已不只是單一 blueprint 私有檔案，而是跨 blueprint 共用的 HTTP 驗證與錯誤映射 helper。

目前主要內容包含：

- `validate_payload_or_400`
- `error_response`
- `error_from_exception`

語意上它比較接近 backend 共用的 HTTP validation infrastructure，而不是 blueprint 專屬 schema 或業務邏輯。

---

## 2. 目前結論

現階段先不搬。

原因：

1. 目前沒有明確維護痛點
2. 搬遷收益主要是目錄語意優化，不是 10.2 的核心阻塞點
3. 目前更重要的是持續完成 contract source / response contract 的主線收斂

---

## 3. 後續什麼情況下再回來看

若出現以下情況，可再重新評估是否搬遷：

1. `validation.py` 開始持續被非 blueprint 邊界直接依賴
2. backend 開始明確整理共用 HTTP / API 基礎設施
3. `blueprints/` 目錄責任變得太混，影響閱讀與維護
4. 後續 backend 共用基礎設施持續往 `backend/contracts/`、`backend/http/`、`backend/api/` 等更中性位置收斂

---

## 4. 若未來要搬，較合理的方向

目前較合理的候選位置：

1. `backend/http/validation.py`
2. `backend/api/validation.py`
3. `backend/common/http_validation.py`

不建議搬到：

1. `backend/contracts/`

原因是它不是 schema 本身，而是 HTTP 驗證與錯誤映射 helper。

---

## 5. 備註

這份文件不是要求立即重構，而是保留一個明確結論：

`validation.py` 目前留在 `blueprints/` 可接受，但不視為理論上的最終位置。
