# Phase 7.3 PostgreSQL Collation Mismatch 修復 Runbook

最後更新：2026-04-24

## 1. 先做根因定位（RCA）

在 PostgreSQL（建議先在 staging）執行：

```sql
SELECT version();

SELECT datname, datcollate, datctype, datlocprovider
FROM pg_database
ORDER BY datname;

SELECT collname, collprovider, collversion
FROM pg_collation
WHERE collname IN ('C', 'C.UTF-8', 'en_US.utf8', 'en_US.UTF-8')
ORDER BY collname;
```

若有警告類似：
`database "xxx" has a collation version mismatch`
代表 DB 建立時的 collation 版本與目前 OS/libc 提供版本不同（常見於 PostgreSQL 映像升級或宿主 OS 更新）。

## 2. 低風險修復（建議路徑）

1. 先備份（必做）：

```bash
pg_dump -Fc -h <host> -U <user> -d <db> -f backup_before_collation_fix.dump
```

2. 刷新資料庫 collation 版本：

```sql
ALTER DATABASE <db_name> REFRESH COLLATION VERSION;
```

3. 對可能受影響 index 重建（建議優先文字欄位索引）：

```sql
REINDEX DATABASE <db_name>;
```

> 若線上負載高，改為逐表 `REINDEX TABLE ...` 以降低鎖定衝擊。

## 3. 保險路徑（若低風險路徑失敗）

1. 建立新 DB（同 PostgreSQL 主版本、同 locale/provider）。
2. 將備份還原到新 DB。
3. 以應用程式 smoke test 驗證。
4. 切換連線字串到新 DB。

## 4. 驗證清單

- `SELECT * FROM alembic_version;` 應包含 7.3 migration head。
- 主要 API 可正常查詢：
  - `/api/timelines/{id}/risk-analysis`
  - `/api/timelines/ai-suggest-plan`
  - `/api/knowledge/documents`
- 關鍵查詢無 collation mismatch 警告。

## 5. 回滾計畫

若修復後出現異常：

1. 立即切回修復前 DB 或還原備份。
2. 關閉 7.3 相關 feature flag（若有）。
3. 保留錯誤 SQL 與 PostgreSQL log，重新執行 RCA。
