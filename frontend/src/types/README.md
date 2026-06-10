# frontend/src/types

這層放前端共用型別，目的是讓 API 回傳、前端狀態、UI 使用資料之間有穩定且可追蹤的型別邊界。

可以把它理解成：

- `services/` 在跟後端交換資料
- `types/` 在描述資料長什麼樣
- `components/` / `views/` 在使用這些資料做畫面

## 常見檔案

- `timeline.ts`, `task.ts`, `group.ts`, `todo.ts`
  - 各 domain 主要型別
- `copilot.ts`
  - Copilot / Agent 相關型別
- `common.ts`, `ui.ts`
  - 共用型別與 UI 層型別
- `index.ts`
  - 匯出入口，維持既有 import 路徑穩定

## 這層應該負責什麼

- API model 型別
- 前端 domain model 型別
- UI 會共用的資料結構型別
- enum-like union type
- 跨多個檔案共用的 payload / response type

## 這層不應該負責什麼

- API 呼叫邏輯
- 畫面顯示邏輯
- 純資料轉換函式
- 欄位驗證函式本體

## 與其他前端目錄的分界

### `types/` 負責

- 描述資料結構
- 統一欄位名稱與型別語意
- 讓多個 service / component 使用同一份型別

### `services/` 負責

- 實際打 API
- 取得資料後回傳對應型別

### `utils/` 負責

- 把某種資料從 A 轉成 B
- 格式化與 mapping

### `components/` / `views/` 負責

- 使用型別後渲染畫面與處理互動

一句話版本：

- `types/` 解決「資料是什麼」
- `utils/` 解決「資料怎麼轉」
- `services/` 解決「資料怎麼拿」

## API model 與 UI model 的分界

這是前端最容易慢慢混掉的地方。

### API model

指的是後端回來的原始資料 shape，通常應盡量貼近後端契約。

適合特徵：

- 欄位名跟後端一致
- 方便 service 對接
- 不先混入畫面專屬衍生欄位

### UI model

指的是前端畫面真正要用的 shape，可能是 API model 經過輕量轉接後的結果。

適合特徵：

- 欄位名更貼近前端語意
- 可帶有少量前端專用欄位
- 但不要混進純顯示字串結果

## 什麼時候該新增型別

- 同一組欄位在多處重複出現
- 多個 service 或 component 都會用到同一種資料
- 某個 payload / response 已經不是一眼看得懂的 inline type
- 你開始需要靠註解解釋欄位意義，通常代表該抽型別了

## 什麼時候不一定要抽到這層

- 單檔內部使用、作用範圍很小的臨時型別
- 與單一 component 強耦合、離開該檔案就沒有意義的局部型別

## 命名原則

- domain 主型別用清楚名詞，例如 `Task`, `Timeline`, `CopilotPlan`
- payload 型別可用 `CreateXxxPayload`, `UpdateXxxPayload`
- API response 型別可用 `XxxResponse`, `XxxApiItem`
- UI 衍生型別可視需要用 `XxxViewModel` 或明確命名，不要都叫 `Data`

## 撰寫原則

- 共用型別優先集中，不要在 component 內反覆手寫 inline type
- 能對應後端契約時，名稱與欄位盡量一致
- 前端衍生型別要清楚區分 API model 與 UI model
- union type 比寬鬆的 `string` 更能保住邊界時，優先用 union type

## `index.ts` 的角色

[frontend/src/types/index.ts](C:/Users/USER/Desktop/0611/0611/Learnlink/frontend/src/types/index.ts:1) 是目前全站型別匯出入口。

這表示：

- 新增常用共用型別時，通常也要考慮是否補到 `index.ts`
- 若某型別是 repo 廣泛使用的共用型別，集中從這裡 export 會比較穩
- 若只是很局部的型別，不一定要進總入口

## 與測試的關係

型別本身通常不是直接拿來「測」的，但它會影響：

- service test 的入參 / 回傳假資料 shape
- component test 的 mock props / mock response

所以如果你發現：

- mock data 到處欄位不一致
- 同一個 entity 在不同測試長得不一樣

往往代表 `types/` 邊界還不夠穩。

## 修改判斷速查

- 同一組欄位重複出現：先看這裡
- service 回傳型別不穩：先看這裡，再看 service mapping
- component props 型別越來越混：先看這裡
- 若只是單檔案內部臨時型別，不一定要抽到這層
