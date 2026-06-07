# 環境變數與預設埠

重要 env keys（範例）

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
GOOGLE_API_KEY=your-google-api-key
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/prajekt
VITE_API_BASE_URL=http://localhost:5000/api
```

預設本地埠

- 後端（Flask）：`5000`
- 前端（Vite）：`5173`
- 本地 Postgres（docker compose）：`5433`（專案使用）

注意事項

- 若改變資料庫連接字串，請同步更新 `DATABASE_URL` 與 `backend/.env.local`（視專案設定）。
- `GOOGLE_API_KEY` 為 AI 功能必要，缺少時相關 API 會回傳錯誤或 fallback。
- `VITE_API_BASE_URL` 可在前端 `env` 中設定以指向遠端或本地後端。
