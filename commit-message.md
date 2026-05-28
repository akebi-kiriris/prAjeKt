Phase 9.1：後端 Type Hints 基線收斂與 Any 邊界第一波精準化

- 完成 Phase 9.1 型別註解基線：覆蓋 repositories、services、validation、transactions 主要邊界
- 補齊 task/timeline/group/message/knowledge/rag 等核心 service 對外函式型別簽名
- 補齊 repositories 層參數與回傳型別，降低 Any 擴散與 agent 串接時的型別不確定性
- 收斂 Any 邊界第一波：group query row 改為 TypedDict（GroupMemberRow / GroupMessageRow）
- group_service 同步改為明確結構讀取，並保留對 ORM object 的相容以確保既有行為
- message_service unread query 回傳型別由 Any 收斂為 Query
- 同步更新重構計畫與進度追蹤（root + docs mirror），反映 9.1 完成與 Any 邊界第一波收斂

驗證：
- python -m compileall services repositories blueprints
- pytest（services + blueprints 關聯範圍）131 passed
- pytest（group/message 關聯範圍）29 passed

備註：
- 保持既有 API 契約與行為不變，本次以型別與可維護性收斂為主
- 仍保留部分動態 payload / 外部互動邊界為 Any，後續可在 9.2/9.3 逐步收斂
