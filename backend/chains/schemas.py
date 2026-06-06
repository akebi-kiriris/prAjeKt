"""Pydantic 驗證模型層 - Phase 6.6 LangChain 整合

為 LangChain 生成的結構化輸出提供服務端驗證和類型推斷。
使用 Pydantic v2 進行驗證，並支持優雅降級到現有 JSON 提取函數。

模型列表:
- Task: 任務生成結果
- ToolSelection: 工具選擇結果  
- TaskSummary: 任務摘要結果
- GroupSnapshot: 群組快照結果

驗證策略:
1. 首選: pydantic parse_obj() - 完整型別驗證
2. 備選: 現有 _extract_first_json_*() 函數 + 手動驗證
3. 日誌: ValidationError 記錄到 logging 模塊
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Task(BaseModel):
    """任務模型 - 來自 task_generation_chain 的輸出
    
    屬性:
        name: 任務名稱 (字數限制: 1-100)
        priority: 優先級 (1-3)
        estimated_days: 預估天數 (1-365)
        task_remark: 任務描述 (字數限制: 1-500)
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "API 端點實現",
                "priority": 1,
                "estimated_days": 5,
                "task_remark": "實現 RESTful API 端點用於任務管理",
                "depends_on_task_refs": ["需求確認", "資料庫 schema 設計"]
            }
        }
    )
    
    name: str = Field(..., min_length=1, max_length=100, description="任務名稱")
    priority: int = Field(..., ge=1, le=3, description="優先級 (1=高, 2=中, 3=低)")
    estimated_days: int = Field(..., ge=1, le=365, description="預估天數")
    task_remark: str = Field(..., min_length=1, max_length=500, description="任務描述")
    depends_on_task_refs: List[str] = Field(default_factory=list, description="前置依賴任務名稱列表")
    
    @field_validator('priority', mode='before')
    @classmethod
    def validate_priority(cls, v: Any) -> int:
        """驗證優先級字段，接受數字與舊版字串值。"""
        if isinstance(v, int):
            if v in {1, 2, 3}:
                return v
            raise ValueError("優先級必須是 1、2、3")

        normalized = str(v or "").strip().upper()
        priority_map = {
            "CRITICAL": 1,
            "HIGH": 1,
            "MEDIUM": 2,
            "LOW": 3,
            "1": 1,
            "2": 2,
            "3": 3,
        }
        if normalized not in priority_map:
            raise ValueError(f"優先級格式錯誤: {v}")
        return priority_map[normalized]

    @field_validator('depends_on_task_refs')
    @classmethod
    def validate_dependency_refs(cls, values: List[str]) -> List[str]:
        """清理前置依賴名稱並移除重複項。"""
        normalized: List[str] = []
        seen = set()
        for value in values:
            if not isinstance(value, str):
                continue
            item = value.strip()
            if not item or item in seen:
                continue
            seen.add(item)
            normalized.append(item)
        return normalized


class ToolSelection(BaseModel):
    """工具選擇模型 - 來自 tool_selection_chain 的輸出
    
    屬性:
        tools: 選擇的工具列表，每個工具包含 tool_name、arguments、reasoning
        reasoning: 總體選擇理由
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "tool_name": "create_task",
                "arguments": {
                    "project_id": "proj_123",
                    "name": "API 端點實現",
                    "priority": "HIGH"
                },
                "reason": "用戶要求建立新任務用於功能開發"
            }
        }
    )
    
    tool_name: str = Field(..., min_length=1, max_length=50, description="工具名稱")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具參數")
    reason: str = Field(..., min_length=1, max_length=300, description="選擇理由")


class TaskSummary(BaseModel):
    """任務摘要模型 - 來自 summary_chain 的輸出
    
    屬性:
        decisions: 會議決議
        risks: 識別的風險
        next_actions: 後續行動項目
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "decisions": [
                    "採用 PostgreSQL 作為主數據庫",
                    "使用 LangChain 進行 LLM 整合"
                ],
                "risks": [
                    "冷啟動延遲可能影響用戶體驗",
                    "LLM 成本控制需要監控"
                ],
                "next_actions": [
                    "實現快取層以降低冷啟動",
                    "設置 LLM 成本警報"
                ]
            }
        }
    )
    
    decisions: List[str] = Field(..., description="會議決議列表")
    risks: List[str] = Field(default_factory=list, description="風險列表")
    next_actions: List[str] = Field(..., description="後續行動項目列表")
    
    @field_validator('decisions', 'next_actions')
    @classmethod
    def validate_non_empty_lists(cls, v: List[str]) -> List[str]:
        """驗證決議和後續行動不能為空"""
        if not v or len(v) == 0:
            raise ValueError("此字段不能為空列表")
        # 清理每個項目的空格
        return [item.strip() for item in v if item.strip()]


class GroupSnapshot(BaseModel):
    """群組快照模型 - 來自 summary_chain group_snapshot 的輸出
    
    屬性:
        health_status: 群組健康狀態 (THRIVING/STABLE/AT_RISK/BLOCKED)
        key_activities: 關鍵活動
        recommendations: 改進建議
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "health_status": "STABLE",
                "key_activities": [
                    "完成 LangChain 整合",
                    "發布 Phase 6.6 更新",
                    "進行性能測試"
                ],
                "recommendations": [
                    "增加單元測試覆蓋率",
                    "實現監控和告警",
                    "文檔更新流程自動化"
                ]
            }
        }
    )
    
    health_status: str = Field(..., description="群組健康狀態")
    key_activities: List[str] = Field(..., description="關鍵活動列表")
    recommendations: List[str] = Field(..., description="改進建議列表")
    
    @field_validator('health_status')
    @classmethod
    def validate_health_status(cls, v: str) -> str:
        """驗證健康狀態字段"""
        valid_statuses = {"THRIVING", "STABLE", "AT_RISK", "BLOCKED"}
        if v.upper() not in valid_statuses:
            raise ValueError(f"健康狀態必須是 {valid_statuses} 之一，得到: {v}")
        return v.upper()
    
    @field_validator('key_activities', 'recommendations')
    @classmethod
    def validate_activity_lists(cls, v: List[str]) -> List[str]:
        """驗證活動和建議列表"""
        if not v or len(v) == 0:
            raise ValueError("此字段不能為空列表")
        return [item.strip() for item in v if item.strip()]


class PlanSuggestedTimeline(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=120, description="建議專案名稱")
    objective: str = Field(..., min_length=1, max_length=1000, description="建議專案目標")


class PlanSuggestedTask(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=120, description="任務名稱")
    reason: str = Field(..., min_length=1, max_length=800, description="任務建議理由")
    priority: str = Field(default="MEDIUM", description="任務優先級")
    estimated_days: int = Field(default=3, ge=1, le=365, description="預估天數")
    depends_on: List[str] = Field(default_factory=list, description="依賴任務名稱列表")

    @field_validator("priority")
    @classmethod
    def validate_priority_value(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            return "MEDIUM"
        return normalized


class PlanSourceReference(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    source_type: str = Field(..., description="來源類型: timeline_task|knowledge_chunk")
    source_id: str = Field(..., min_length=1, max_length=120, description="來源 ID")
    title: str = Field(..., min_length=1, max_length=180, description="來源標題")
    snippet: str = Field(..., min_length=1, max_length=600, description="來源片段")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="來源分數")

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, value: str) -> str:
        normalized = (value or "").strip()
        if normalized not in {"timeline_task", "knowledge_chunk"}:
            raise ValueError("source_type 必須是 timeline_task 或 knowledge_chunk")
        return normalized


class PlanSuggestionOutput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    suggested_timeline: PlanSuggestedTimeline
    suggested_tasks: List[PlanSuggestedTask] = Field(default_factory=list)
    source_references: List[PlanSourceReference] = Field(default_factory=list)
    summary: str = Field(default="", max_length=1200, description="規劃摘要")
