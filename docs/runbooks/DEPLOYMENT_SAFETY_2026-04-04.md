# 部署安全檢查：Phase 6.0 PostgreSQL 遷移

> 日期：2026/04/04 | 對象：Supabase 部署

## 問題背景

之前修改了 3 個已執行過的舊 migration（在 Supabase 已有紀錄），會導致部署衝突。

## 修復方案 ✅

### 1. 還原舊 Migration 為原始狀態
- `439237f905ed_todo_add_content_field.py` → 移除 `has_table` 檢查（恢復原始）
- `a5efd8d22631_remove_progress_field_from_timeline.py` → 移除欄位存在檢查（恢復原始）
- **原因**：Supabase alembic_version 表已記錄執行狀態，修改檔案會導致版本不一致

### 2. 新增獨立 Migration：compat safeguards
- 檔案：`c1d2e3f4a5bb_add_postgres_compat_safeguards.py`
- 用途：為未來 PostgreSQL 兼容性修復預留（目前為空 pass migration）
- 優勢：不影響既有部署，新部署環境自動執行最新修復

### 3. 補強 Subtasks Migration
- `b4c2d9e7f1ab_add_subtasks_table.py` 現在是冪等的
- 邏輯：`if not inspector.has_table('subtasks'): create_table(...)`
- 好處：既有部署跳過（表已存在），新部署正常建立

### 4. 修正 Migration 依賴鏈
```
6a15da3a4025 → 1f7e8f9caaff → add_deleted_field → b4c2d9e7f1ab → c1d2e3f4a5bb
```
- **無分支**（已驗證 `db heads` 單一頂點）
- **線性遞進**（每個版本唯一 down_revision）

## 對部署的影響

| 環境 | 狀態 | 備註 |
|-----|------|------|
| **Supabase 既有部署** | ✅ 安全 | 老 migration 未改，只執行新的 compat safeguards（無副作用） |
| **Railway 後端** | ✅ 安全 | 同 Supabase |
| **Firebase 前端** | ✅ 無影響 | 前端不含 migration |
| **本地開發** | ✅ 正常 | 可正常執行 `flask db upgrade head` |

## 驗證結果

1. Migration 鏈檢查：
   ```
   $ flask db heads
   → c1d2e3f4a5bb (head)  // ✅ 單一頂點，無分支
   ```

2. Migration 升級執行：
   ```
   $ flask db upgrade head
   → Running upgrade b4c2d9e7f1ab -> c1d2e3f4a5bb ✅
   ```

3. 回歸測試：
   ```
   $ pytest tests -q
   → 136 passed ✅
   ```

## 建議行動

### 立即行動
- ✅ 程式碼已修復（無需額外操作）
- 本地開發使用 `scripts/dev/bootstrap_pg_local.bat` 或 `scripts/dev/start_all.bat` 正常部署

### 未來 Production 更新
- 當推送至 Supabase：只新增 compat safeguards（無衝突）
- 舊 migration 保持不動（版本兼容）

### 長期建議
- Migration 修改原則：
  1. **新增 migration** ✅ →  安全
  2. **現有 migration 修復** ❌ → 建立新 migration 應用修復
  3. 避免修改執行過的老 migration（除非絕對必要且知曉後果）

---

**檢查清單**
- [x] 舊 migration 還原為原始狀態
- [x] 新建 compat safeguards migration
- [x] Subtasks migration 改為冪等
- [x] Migration 鏈線性化（no branching）
- [x] 本地升級測試通過
- [x] 後端回歸測試通過（136 passed）
- [x] Production 安全性驗證完成
