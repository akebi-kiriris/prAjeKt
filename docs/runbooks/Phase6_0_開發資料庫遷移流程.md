# Phase 6.0 開發資料庫遷移流程（SQLite -> PostgreSQL）

> 版本：v1.1
> 最後更新：2026-04-04
> 目標：將本地開發主線從 SQLite 遷移為 PostgreSQL，讓本地、測試、部署環境一致。

---

## 1. 範圍與原則

- 範圍：本地開發環境、測試環境、初始化流程、文件流程。
- 非範圍：生產資料庫（Supabase）已在 Phase 5 完成，不在本文件重做。
- 原則：
  - 先完成「可啟動 + 可測試」，再處理舊資料轉移。
  - 保留 SQLite 作為 fallback，不再作為主線。
  - 每一步都要可驗證、可回滾。

---

## 2. 完成定義（DoD）

- 本地 `backend` 預設使用 PostgreSQL 啟動成功。
- `pytest tests -q` 在 PostgreSQL 環境可通過。
- `GET /api/health` 可明確回傳目前 DB 類型為 PostgreSQL。
- 新同學可依文件在 30 分鐘內完成本地啟動。

---

## 3. 前置需求

- Docker Desktop（或可執行 PostgreSQL 的本機服務）。
- Python 3.10+、pip、venv。
- 現有後端依賴可安裝：`psycopg2-binary`。
- 已備份 SQLite 檔案（若要保留舊資料）。

---

## 4. 執行步驟

### Step 1. 建立本地 PostgreSQL 服務

新增或更新 `docker-compose.yml`（範例）：

```yaml
services:
  postgres:
    image: postgres:16
    container_name: prajekt-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: prajekt
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d prajekt"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

啟動：

```bash
docker compose up -d postgres
docker compose ps
```

### Step 2. 統一環境變數

將 `backend/.env.local` 的 `DATABASE_URL` 改為：

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/prajekt
```

檢查點：
- 不再以 SQLite 連線字串作為預設值。
- README 與啟動文件中的範例值一致。

### Step 3. Schema 初始化策略

二選一，整個團隊統一使用同一條路徑：

- 路徑 A（推薦）：`flask db upgrade`
- 路徑 B（現有流程）：`python init_db.py`

驗證：

```bash
cd backend
flask db upgrade
python check_tables.py
```

### Step 4. 舊資料遷移

若要帶入本地 SQLite 歷史資料，建議流程：

- 先做全新 schema 初始化。
- 寫一次性遷移腳本（目前已提供：`backend/migrate_sqlite_to_postgres.py`）：
  - 先搬主表：`users`, `timelines`, `tasks`, `groups`
  - 再搬關聯表：`timeline_users`, `task_users`, `subtasks`, `task_comments`, `task_files`, `messages`, `notifications`
- 以主鍵或唯一鍵做去重，避免重跑重複插入。

最低驗證：
- 使用者數量一致。
- 任務與子任務數量一致。
- 抽樣檢查 3 筆跨表資料關聯正確。

本專案本次執行指令：

```bash
cd backend
venv\Scripts\python.exe migrate_sqlite_to_postgres.py --sqlite-path instance/prajekt.db --pg-dsn postgresql://postgres:postgres@localhost:5433/prajekt
```

### Step 5. 啟動與健康檢查

啟動後端：

```bash
cd backend
python app.py
```

驗證 API：

```bash
curl http://localhost:5000/api/health
```

預期：
- status 為 healthy。
- db driver 或 db name 顯示 PostgreSQL。

### Step 6. 測試與回歸

```bash
cd backend
venv\Scripts\python.exe -m pytest tests -q
```

若測試依賴資料庫特性（例如 transaction / datetime / constraint），需補上 PostgreSQL 專屬測試樣本。

### Step 7. 文件與啟動腳本同步

必做同步：
- `README.md`：DATABASE_URL、啟動流程。
- `重構計畫.md`：6.0 進度與驗收狀態。
- `進度追蹤.md`：里程碑與實際完成日期。
- `scripts/dev/start_all.bat` / `start.sh`：提示資訊與前置檢查說明。

---

## 5. 驗收清單（可直接勾）

- [x] `docker compose up -d postgres` 正常。
- [x] `backend/.env.local` 已切到 PostgreSQL URL。
- [x] schema 初始化成功（`flask db upgrade`）。
- [x] `/api/health` 顯示 PostgreSQL。
- [x] `venv\Scripts\python.exe -m pytest tests -q` 通過（`136 passed`）。
- [x] SQLite 資料已遷移至 PostgreSQL（含 `subtasks`，筆數對帳一致）。
- [x] README / 重構計畫 / 進度追蹤 已同步更新（本輪已更新重構計畫，README/進度追蹤可依版本節奏補記）。

---

## 6. 回滾策略

若遷移期間阻塞開發，臨時回滾：

- 還原 `DATABASE_URL` 到 SQLite（僅短期）。
- 保留 PostgreSQL 容器與遷移腳本，不刪除。
- 開 issue 記錄阻塞點與重啟條件。

回滾原則：
- 回滾是為了不中斷開發，不是取消 Phase 6.0。
- 下一輪需先解掉阻塞點再重新切回 PostgreSQL。

---

## 7. 常見風險與對策

- 風險：本地與 CI 用不同 DB。
  - 對策：CI 增加 PostgreSQL service container。
- 風險：datetime/timezone 在 PG 與 SQLite 行為不同。
  - 對策：統一 UTC 儲存，API 回傳 ISO 8601（含時區）。
- 風險：唯一鍵與外鍵約束在 PG 更嚴格，導致舊資料插入失敗。
  - 對策：遷移腳本加入資料清理與錯誤報告。

---

## 8. 建議時程（Week 1-2）

- Day 1-2：PostgreSQL 本地服務 + env 切換 + schema 初始化。
- Day 3-4：測試修補與 `/api/health` 驗證。
- Day 5-7：舊資料遷移腳本（可選）與文件同步。
- Day 8-10：CI 一致化與收斂驗收。
