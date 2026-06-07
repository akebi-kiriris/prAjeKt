# Quickstart（最短可複製流程）

以下為最少步驟，讓開發環境可在本機跑通。更多細節請參閱 [本地開發測試部署_Runbook.md](./本地開發測試部署_Runbook.md)。

Windows（建議已安裝 Docker）

```bat
REM 於專案根目錄執行一次：
scripts\dev\bootstrap_pg_local.bat

REM 或（若已初始化）啟動：
scripts\dev\start_all.bat
```

手動（如需逐步操作）

```bat
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
docker compose up -d postgres
venv\Scripts\python.exe safe_migrate.py
venv\Scripts\python.exe migrate_sqlite_to_postgres.py --sqlite-path instance/prajekt.db --pg-dsn postgresql://postgres:postgres@localhost:5433/prajekt --skip-if-not-empty
venv\Scripts\python.exe app.py

cd ..\frontend
npm install
npm run dev
```

Unix / macOS

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker compose up -d postgres
python safe_migrate.py
python migrate_sqlite_to_postgres.py --sqlite-path instance/prajekt.db --pg-dsn postgresql://postgres:postgres@localhost:5433/prajekt --skip-if-not-empty
python app.py

cd ../frontend
npm install
npm run dev
```

預期服務

- 後端: http://localhost:5000
- 前端: http://localhost:5173
