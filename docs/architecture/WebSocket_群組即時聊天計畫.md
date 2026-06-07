# 📖 Socket.IO 核心學習筆記



## 第一章：連線與身份識別 (Connection & Identity)
- WebSocket 是持久連線，所以「誰是誰」是在連線那一刻就決定的。
- 握手 (Handshake)：Socket.IO 預設會先用 HTTP Long Polling 嘗試連線，穩定後再自動升級（Upgrade）到 WebSocket 協議。
- 身份驗證 (Auth)：
  - 不要在每個事件都傳 Token。
  - 在建立連線時傳遞：io(url, { auth: { token: '...' } })。
- 房間 (Rooms)：這是 Socket.IO 最強大的功能。
  - join_room(room_name)：將某個連線歸類。
  - 在本專案的應用是群組房間：group_{group_id}。
  - 好處：發送訊息時只要 emit 到該 room，不會外溢到其他群。


## 第二章：通訊模式 (Communication Patterns)
理解這三種模式，就能覆蓋 99% 的功能：
|模式|指令 (Flask-SocketIO)|應用場景|
|---|---|---|
|**單一回覆**|emit('event', data)|回應發送者「我收到你的訊息了」。|
|**定向推送**|emit('event', data, to=room_id)|私訊、個人通知。|
|**全體廣播**|emit('event', data, broadcast=True)|系統公告、線上人數更新。|

**筆記重點**：emit 是「推」，on 是「聽」。

在你現在的專案中，對應如下：
- 單一回覆：group:joined、group:left（只回給自己）
- 定向推送：to=group_{id}（同群組的人）
- 全體廣播：目前沒用到，因為聊天通常不需要全站公告


## 第三章：穩定性與例外處理 (Stability)
這是手刻最難、但 Socket.IO 幫你做好的部分：
- 心跳機制 (Heartbeat)：內部會自動定時發送小封包，確認對方還活著。如果斷線，前端會自動嘗試重連（Reconnection）。
- 離線處理：WebSocket 斷線期間產生的訊息，不會自動補發。
  - 解決方案：前端重連成功後（監聽 reconnect 事件），主動打一次 API 抓取「斷線期間的歷史訊息」。
- CORS 跨域：本專案是 Vue (5173) + Flask (5000)，Socket 初始化需要對應允許來源。


## 第四章：對照本專案的初始化與接線

### 後端 app.py 在做什麼
1. 建立 `socketio = SocketIO(async_mode='threading')`
2. `socketio.init_app(app, cors_allowed_origins=[...])`
3. 註冊事件：`register_socket_events(socketio)`
4. 啟動時用 `socketio.run(app, ...)`，不是 `app.run(...)`

### 為什麼要 threading
- 開發環境簡單、穩定，先把事件與權限邏輯打通。
- 之後若要更高併發，可再評估 gevent/eventlet 或 ASGI 路線。


## 第五章：後端事件流程（你可以照這張圖去對代碼）

### 1) connect
- 從 auth 取 token
- decode token 拿 user id
- 查 user 是否存在
- 成功後把 sid -> user context 存到 CONNECTED_USERS

### 2) group:join
- 驗證 payload 的 group_id
- 驗證是否群組成員 (`is_group_member`)
- join_room(group_{id})

### 3) group:send-message
- 驗證 payload 與 membership
- 呼叫 `create_group_message` 寫入 DB
- emit `group:new-message` 到房間

### 4) group:leave / disconnect
- leave room / 清理 CONNECTED_USERS

你在讀 `backend/realtime/socket_events.py` 時，重點不是語法，而是「每一步都在防哪個錯」。


## 第六章：前端整合思路（Service + Store + View）

### socketService.ts
- 專責「連線層」：connect、disconnect、emit、on/off
- 目的：避免在 View 直接碰 socket 細節

### groups.ts (Pinia)
- 專責「聊天狀態」：
  - socketConnected、socketReady、activeRoomId、lastSocketError
  - messageIdSet 去重
  - openChat/closeChat 流程控制
- 重要設計：Socket 優先、REST fallback

### GroupsView.vue
- 專責「畫面生命週期」：
  - 開啟聊天室 -> openChat
  - 關閉聊天室 -> closeChat
  - 離開頁面 -> destroySocket

這種分層的好處是：你要改 Socket 行為時，通常改 store/service 就夠，View 不會爆炸。


## 第七章：混合模式（REST + Socket）為什麼好學又實用

你的專案採用的是業界很常見的策略：
- Socket：提供即時體驗（新訊息秒到）
- REST：提供資料一致性與補償（斷線可重抓）

這就是「即時性」與「可靠性」同時兼顧。


## 第八章：你現在可以直接觀察的事件清單

### Client -> Server
- group:join
- group:leave
- group:send-message

### Server -> Client
- socket:ready
- group:joined
- group:left
- group:new-message
- group:error

看到 group:error 時，不要只看 message，先判斷 code：
- AUTH_FAILED：多半是 token 問題
- NOT_MEMBER：權限問題
- INVALID_PAYLOAD：欄位格式問題
- SERVER_ERROR：通常看後端 log


## 第九章：讀代碼時最容易卡住的 4 個點

1. 以為 connected 就能收到訊息
- 還不夠，還要先 join 正確 room。

2. 重複收到訊息
- 可能是 listener 重複綁定，或缺少 message_id 去重。

3. 切群後還收到舊群訊息
- 多半是 leave room 或 activeRoomId 清理不完整。

4. Socket 掛了整個聊天室不能用
- 你的專案設計是可 fallback，先確認 sendMessage 是否走回 REST。


## 第十章：小結（給現在的你）

如果你只記三件事：
1. 先搞懂 room 機制，這是聊天隔離核心。
2. 先搞懂 store 的狀態流，這是前端即時行為核心。
3. 先搞懂 fallback，這是系統穩定性核心。

懂這三件事，你看後面的 typing、已讀、重連補抓會快很多。