# Phase 10.3 protected fields 與 frontend 不可自送欄位說明

> 日期：2026-06-17  
> 目的：把 Phase 10.2 已釐清、但原本還停留在討論與慣例層的 `protected fields` / `route-owned identifiers`，整理成可直接查閱的正式說明。  
> 定位：這份文件不是新的 schema 真相來源；它是幫助 frontend、blueprint、service review 快速判斷「哪些欄位不該由 client 自送」的閱讀版規則。

---

## 1. 一句話先記住

不是所有欄位都應該由 frontend 放進 request body。

有些欄位：

1. 應由 auth context 決定
2. 應由 route / path 決定
3. 應由後端查詢、guard 或 service 流程推導後確認

這些欄位即使格式正確，也不代表 client 有權提供。

---

## 2. 三種欄位分類

### 2.1 client-owned fields

這類欄位可以由 frontend 送進來，再交給 schema 驗證格式與基本限制。

常見例子：

1. `name`
2. `description`
3. `remark`
4. `priority`
5. `start_date`
6. `end_date`
7. `status`
8. `content`

判斷方式：

1. 這是使用者真的可以自由輸入或修改的內容
2. route / auth context 無法自然推導出來
3. 只靠 server 自己也不該擅自決定

### 2.2 server-owned / protected fields

這類欄位不應由 frontend 自送，應由後端 context、guard 或 service 決定。

常見例子：

1. `user_id`
2. `actor_user_id`
3. `created_by`
4. `owner_id`
5. `request_id`
6. `execution_id`
7. `plan_id` 以外的核准後寫入欄位
8. agent / tool payload 中由 server 注入的 scope 欄位

判斷方式：

1. 欄位代表的是「誰正在操作」而不是「想操作什麼」
2. 欄位牽涉權限、審計、追蹤或系統內部流程
3. 若讓 client 自送，會出現冒名、越權或污染 trace 的風險

### 2.3 route-owned identifiers

這類欄位的主來源應是 URL path / route 參數，不應在 request body 再重複承諾一次。

常見例子：

1. `task_id`
2. `timeline_id`
3. `group_id`
4. `comment_id`
5. `message_id`
6. `document_id`
7. `notification_id`

判斷方式：

1. 路由已經明確指出操作目標
2. body 再送一次同欄位只會增加衝突與混亂
3. 若 path 與 body 不一致，後端還得額外處理「到底該信哪個」

---

## 3. 為什麼不能只靠 schema 驗證

schema 可以驗證：

1. 欄位有沒有缺
2. 型別對不對
3. 字串長度、列舉值、日期格式等基本限制

但 schema 不能單靠自己回答：

1. 這個 `user_id` 是不是應該從 JWT 來？
2. 這個 `timeline_id` 為什麼同時出現在 path 和 body？
3. 這個使用者到底是不是這個 group / timeline 的 member？
4. 這筆資料是不是屬於目前正在操作的資源？

所以完整判斷一定是：

1. schema 驗證格式
2. route 決定目標資源
3. auth context 決定操作者
4. service / repository / guard 驗證業務合法性

---

## 4. frontend 端應遵守的規則

### 4.1 不要把以下欄位放進 request body

1. `user_id`
2. `actor_user_id`
3. `created_by`
4. `owner_id`
5. 已由 path 承諾的 `task_id` / `timeline_id` / `group_id` / `comment_id`
6. 後端內部追蹤欄位，例如 `request_id`、`trace_id`、`execution_id`

### 4.2 frontend type 不要把這些欄位混進 create / update payload

例如：

1. `CreateTaskPayload` 不應長出 `user_id`
2. `UpdateTimelinePayload` 不應長出 `owner_id`
3. `AddGroupMessagePayload` 不應長出 `group_id` 若 route 已經是 `/groups/{group_id}/messages`
4. `CreateSubtaskPayload` 不應自行承諾 `task_id` 若 route 已經是 `/tasks/{task_id}/subtasks`

### 4.3 若畫面上需要這些值，也不代表它們該被送回後端

常見情況：

1. 畫面需要顯示 `user_id`、`owner_id`
2. URL 上已經有 `timeline_id`
3. store 裡拿得到 `group_id`

這些值可以用來顯示、比對、導頁，但不等於要重新塞回 payload。

---

## 5. backend 端應遵守的規則

### 5.1 blueprint

1. 不要讓 path 與 body 同時承諾同一個資源 id
2. 若操作者可由 JWT 取得，就不要從 body 接 `user_id`
3. schema 只驗 client-owned fields
4. route-owned identifier 由 path 讀取後再組 service payload

### 5.2 service

1. 將 `actor_user_id`、`operator_user_id`、scope id 視為 server 注入資料
2. 若某欄位應靠查詢確認，就不要只因 schema 通過就直接信任
3. 需要權限判定時，以 guard / context / 查詢結果為準

### 5.3 tool / agent

1. planner / tool payload 不應讓模型自由產出 protected keys
2. nested payload 也要做 sanitize
3. 真正執行前仍要由 server 補 scope 欄位與權限資訊

---

## 6. 在 Learnlink 目前最常見的例子

### 6.1 task / timeline

不該由 frontend 自送：

1. `user_id`
2. `actor_user_id`
3. `task_id` 若 route 已是 `/tasks/{task_id}`
4. `timeline_id` 若 route 已是 `/timelines/{timeline_id}`

應由 frontend 自送：

1. `name`
2. `description`
3. `priority`
4. `start_date`
5. `end_date`
6. `status`
7. `depends_on_task_ids` 或其他真正屬於使用者編輯內容的欄位

### 6.2 group / message / notification

不該由 frontend 自送：

1. `group_id` 若 route 已是 `/groups/{group_id}/...`
2. `user_id`
3. `sender_id`
4. `notification_id` 若 route 已經承諾

應由 frontend 自送：

1. `content`
2. `invite_code`
3. 其他真的是使用者輸入的搜尋或操作欄位

### 6.3 copilot / agent

不該由 frontend 或模型自送：

1. `actor_user_id`
2. scope 類欄位若應由 route / context 決定
3. 由後端注入的 protected keys

可由 frontend 自送：

1. `message`
2. 已明確允許的 `context`
3. 已明確允許的 `tool_payloads` 內容

但即使可送，後端仍要再 sanitize 與補 server context。

---

## 7. review 時的快速檢查清單

看到一個 request payload 時，至少問自己：

1. 這個欄位真的是 client 可以自由決定的嗎？
2. 它是不是其實應由 auth context 決定？
3. 它是不是其實已經由 route / path 承諾？
4. 它是不是即使格式合法，仍要靠 DB / guard / service 才能成立？
5. frontend type 是否偷偷把不該送的欄位也混進去了？

如果答案偏向第 2、3、4 類，就不應只把它當成普通 request schema 欄位。

---

## 8. 和 Phase 10.3 的關係

這份文件補上的，不是新的實作機制，而是把已在 10.2 / 10.3 形成的判斷邏輯正式文件化：

1. request / response contract 不只看型別，也要看欄位擁有權
2. frontend type 不應長出其實不能送的欄位
3. backend schema 收斂之後，欄位責任邊界也要能被穩定重複判斷

一句話版：

`schema` 驗格式，`context / route / service` 驗欄位擁有權與業務合法性。
