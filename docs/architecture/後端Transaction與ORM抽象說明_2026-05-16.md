# 後端 Transaction 與 ORM 抽象說明_2026-05-16

## 這次重構到底在做什麼

這次重構的主軸不是「把程式碼搬來搬去」，而是逐步降低 service 層對資料庫細節的依賴。

可以先抓住一句話：

> Service 應該描述 use case 流程；資料庫交易、ORM entity 建構、session 操作，應該盡量被集中到更低層的 helper / repository。

這不代表 service 完全不能碰資料庫相關概念，而是要避免 service 同時知道太多細節，例如：

- 什麼時候 `commit()`。
- 失敗時哪裡要 `rollback()`。
- SQLAlchemy entity 怎麼建。
- 什麼時候需要 `flush()` 才拿得到 id。
- 每種 entity 要怎麼 `db.session.add()`。

我們目前的重構就是把這些細節一層一層往外抽。

## 重構前的樣子

重構前，service 常常像這樣：

```python
def create_task_for_user(user_id, data):
    # 驗證 request payload
    # 正規化資料

    new_task = Task(...)
    db.session.add(new_task)
    db.session.flush()

    db.session.add(TaskUser(...))
    db.session.add(Notification(...))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise TaskOperationError(...)
```

這種寫法短期可以運作，但 service 同時扮演了很多角色：

- Use case coordinator：建立任務這個流程要做哪些事。
- Domain rule checker：檢查狀態、日期、權限、成員。
- ORM factory：知道 `Task(...)`、`TaskUser(...)`、`Notification(...)` 怎麼建。
- Persistence layer：知道 `db.session.add()`、`flush()`、`commit()`、`rollback()`。
- Error translator：把底層例外轉成 API 可理解的錯誤。

問題不在於它「錯」，而是這些責任混在一起後，後續維護會變難。

## 第一階段：收斂 transaction 邊界

第一階段處理的是 `commit()` / `rollback()`。

我們新增了：

```text
backend/services/transactions.py
```

核心概念是：

```python
with transaction(TaskOperationError, '任務新增失敗，請稍後再試'):
    ...
```

這代表 service 不再自己寫：

```python
try:
    db.session.commit()
except Exception:
    db.session.rollback()
```

而是把交易規則集中到 `transaction()`。

### 這一步解決什麼

它解決的是 transaction boundary 分散的問題。

也就是：

- 哪一段流程成功後要提交。
- 哪一段流程失敗後要回滾。
- 已知的 operation error 要不要保留原本 status code。
- 未預期錯誤要怎麼包成統一錯誤。

這些規則不再散在每個 service function 裡。

### 這一步還沒有解決什麼

這一步還沒有完全讓 service 脫離 ORM。

因為 service 裡仍可能有：

```python
new_task = Task(...)
db.session.add(new_task)
db.session.flush()
```

所以第一階段只是先把「交易控制」抽出，不是把所有 DB 操作都抽完。

## 第二階段：抽出 ORM entity 建構

第二階段處理的是 `Task(...)`、`Timeline(...)`、`TaskUser(...)`、`Notification(...)` 這類 ORM entity 建構。

我們新增或調整了 repository helper，例如：

```text
backend/repositories/task_repository.py
backend/repositories/timeline_repository.py
backend/repositories/session_repository.py
```

現在 service 會更像這樣：

```python
new_task = build_task_entity(...)
add_entity(new_task)
flush_session()
add_entity(build_task_member_entity(...))
```

### 這一步解決什麼

它降低了 service 對 SQLAlchemy model 結構的直接依賴。

以前 service 需要知道：

```python
Task(
    user_id=user_id,
    name=data['name'],
    completed=False,
    completed_at=None,
    timeline_id=timeline_id,
    ...
)
```

現在 service 只需要知道：

```python
build_task_entity(...)
```

這樣做的好處是：

- 建立 entity 的預設值更集中。
- ORM 欄位變動時，不一定要到處改 service。
- service 主流程比較容易閱讀。
- 未來如果要把 ORM model 和 domain model 分開，會比較有位置可以接。

### 為什麼還有 `add_entity()`、`flush_session()`、`delete_entity()`

因為目前 Learnlink 還是 SQLAlchemy ORM 架構。

我們沒有一次導入完整 Unit of Work，所以仍需要地方負責：

- 把 entity 掛進 session。
- 在需要新 id 時呼叫 `flush()`。

只是現在這些操作被集中到：

```text
backend/repositories/session_repository.py
```

這代表 session 操作不再散在各個 repository 裡，也不再每個 service 自己直接呼叫 `db.session.add()` / `db.session.flush()`。
目前也包含 `db.session.delete()` 的共用入口。

## 重構後的責任邊界

目前比較理想的閱讀方式是：

```text
Blueprint
  負責 HTTP request / response、JWT、參數取得

Service
  負責 use case 流程、業務驗證、權限判斷、錯誤語意

Transaction helper
  負責 commit / rollback 規則

Repository helper
  負責查詢、建立 ORM entity、封裝資料存取細節

Session repository
  負責 add / flush / delete 這類 session 操作

SQLAlchemy models
  負責 ORM mapping
```

換成流程圖會像這樣：

```text
HTTP request
  ↓
Blueprint
  ↓
Service: create_task_for_user()
  ↓
Service helper: _build_task_create_payload()
  ↓
Repository helper: build_task_entity()
  ↓
Session helper: add_entity(), flush_session(), delete_entity()
  ↓
Transaction helper: commit or rollback
  ↓
Database
```

## Service 現在仍然知道什麼

目前 service 還是知道一些 persistence 概念，例如：

- 它知道某段流程需要 transaction。
- 它知道建立 task 後需要 `flush_session()` 才能拿到 `task_id`。
- 它知道要呼叫 repository helper 建 entity。
- 它仍會操作 ORM entity 上的 domain-like method，例如 `task.change_status(...)`。

這是目前可接受的過渡狀態。

因為我們現在的目標不是一步到位變成完整 DDD，而是先把最混亂、最容易出錯的 DB 細節集中起來。

## 我們還沒做到什麼

目前還沒有做到完全的 ORM 解耦。

例如：

- Service 拿到的仍然是 SQLAlchemy model。
- Repository helper 回傳的仍然是 ORM entity。
- 測試 service 時，多數情況仍需要資料庫 session。
- 還沒有完整 Unit of Work 物件。
- 還沒有獨立的 domain model 層。

所以比較精準的說法是：

> 我們不是把 ORM 從 service 世界完全移除，而是先把 ORM 細節集中、命名、隔離，讓 service 不再直接散落 transaction 與 entity 建構細節。

## 下一步：何時要做 repository 語意化

目前 `session_repository` 的 `add_entity()` / `flush_session()` / `delete_entity()` 是通用層能力，適合快速收斂與一致化。  
下一步是否要再往上抽「語意化 helper」，建議用以下判準：

- 同一段流程同時操作 2~3 個以上 entity，且有先後依賴（例如 member + notification）。
- 同一組 persistence 規則在多個 service 函式重複出現。
- 流程的業務語意比 ORM 細節更重要，service 可讀性開始下降。

適合語意化的例子：

- `add_timeline_member_with_invite_notification(...)`
- `transfer_task_owner_and_demote_previous(...)`
- `create_group_with_owner_member(...)`

不急著語意化的例子：

- 單筆 CRUD（單一 entity、無跨表規則）
- 只在一個地方出現且邏輯簡單的流程

一句話：先用通用 helper 把 session 細節收斂，再對高複雜流程補語意化入口，避免一開始就過度抽象。

## 為什麼不一口氣做到完全抽象

因為 Learnlink 目前已經有不少功能，直接導入完整 Unit of Work / domain model 會有幾個風險：

- 改動範圍太大。
- 很多測試會一起壞。
- 原本能運作的流程可能被抽象改壞。
- 會為了「架構看起來漂亮」而付出太多遷移成本。

所以這次採取的是漸進式重構。

也就是：

1. 先把 `commit()` / `rollback()` 收斂。
2. 再把建立 entity 的細節抽出。
3. 再統一 `add()` / `flush()` 的入口。
4. 等 service 仍然痛、測試仍然難寫，再評估 Unit of Work。

## 這跟 Architecture Patterns with Python 的關係

《Architecture Patterns with Python》裡強調的不是「一定要照抄某個資料夾結構」，而是：

- 讓高層業務流程不要依賴低層技術細節。
- 讓資料庫、ORM、外部服務成為可替換的 adapter。
- 讓 domain / service 的測試不需要每次都碰真實基礎設施。

我們目前做的是往這個方向靠近，但還沒有完全到書中的最終型態。

目前比較像：

```text
Before:
Service -> SQLAlchemy session / ORM details everywhere

Now:
Service -> transaction helper + repository helper + session helper -> SQLAlchemy

Future:
Service -> Unit of Work / repository interface -> SQLAlchemy adapter
```

## 判斷自己有沒有理解的檢查點

可以用這幾個問題檢查：

- 我是否分得出 `transaction()` 解決的是 commit/rollback，而不是 entity 建構？
- 我是否知道 `build_task_entity()` 解決的是 ORM 建構細節集中化？
- 我是否知道 `add_entity()` / `flush_session()` 仍然是 session 操作，只是被集中到一個入口？
- 我是否知道目前還沒有完全脫離 SQLAlchemy？
- 我是否知道 service 現在主要應該讀成 use case orchestration？

如果以上都能回答，那這次重構的核心概念就已經抓到了。

## 一句話總結

這次重構的目的，是把 service 從「什麼都自己做」推向「負責流程編排，細節交給 transaction / repository / session helper」。

它不是終點，但它是一個很穩的中繼站。
