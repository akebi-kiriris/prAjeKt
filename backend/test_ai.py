#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 功能測試腳本
用於快速驗證 Google Gemini API 是否正常工作
"""

import os
from dotenv import load_dotenv

def test_environment():
    """測試環境配置"""
    print("=" * 50)
    print("1. 檢查環境配置")
    print("=" * 50)
    
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ 錯誤：GOOGLE_API_KEY 未設定")
        print("   請在 .env 檔案中添加：GOOGLE_API_KEY=你的金鑰")
        return False
    
    if not api_key.startswith('AIza'):
        print("⚠️  警告：API Key 格式可能不正確")
        print(f"   當前值：{api_key[:10]}...")
        print("   正確格式應以 'AIza' 開頭")
        return False
    
    print(f"✅ GOOGLE_API_KEY 已設定：{api_key[:10]}...{api_key[-4:]}")
    return True

def test_package():
    """測試套件是否安裝"""
    print("\n" + "=" * 50)
    print("2. 檢查套件安裝")
    print("=" * 50)
    
    try:
        import google.generativeai as genai
        print("✅ google-generativeai 已安裝")
        return True
    except ImportError:
        print("❌ 錯誤：google-generativeai 未安裝")
        print("   請執行：pip install google-generativeai")
        return False

def test_api_connection():
    """測試 API 連線"""
    print("\n" + "=" * 50)
    print("3. 測試 API 連線")
    print("=" * 50)
    
    try:
        import google.generativeai as genai
        import os
        
        api_key = os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print("⏳ 發送測試請求...")
        response = model.generate_content("請用一句話介紹你自己")
        
        print("✅ API 連線成功！")
        print(f"   回應：{response.text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ API 連線失敗：{str(e)}")
        print("\n可能的原因：")
        print("1. API Key 無效或已過期")
        print("2. 超過免費配額限制")
        print("3. 網路連線問題")
        print("4. 模型名稱錯誤")
        return False

def test_task_generation():
    """測試任務生成功能"""
    print("\n" + "=" * 50)
    print("4. 測試任務生成")
    print("=" * 50)
    
    try:
        import google.generativeai as genai
        import os
        import json
        
        api_key = os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=api_key)
        
        # 模擬專案資訊
        project_name = "測試專案"
        project_description = "使用 Python 開發一個簡單的 Web 應用"
        
        # 定義 JSON Schema
        task_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "priority": {"type": "integer", "enum": [1, 2, 3]},
                    "estimated_days": {"type": "integer", "minimum": 1, "maximum": 14},
                    "task_remark": {"type": "string"}
                },
                "required": ["name", "priority", "estimated_days", "task_remark"]
            },
            "minItems": 5,
            "maxItems": 8
        }
        
        prompt = f"""你是一個專案管理助手。根據以下專案資訊，生成 5-8 個具體可執行的任務。

專案名稱: {project_name}
專案描述: {project_description}

要求：
1. 任務要符合專案主題，具體可執行
2. 使用繁體中文
3. 優先順序要合理（1=高, 2=中, 3=低）
4. 預估天數要實際（1-14天）
5. 提供實施建議
"""
        
        print("⏳ 生成任務中...")
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=task_schema,
                temperature=0.7
            )
        )
        
        # 解析 JSON
        tasks = json.loads(response.text)
        
        print(f"✅ 成功生成 {len(tasks)} 個任務！\n")
        
        for i, task in enumerate(tasks, 1):
            priority_emoji = {1: "🔴", 2: "🟡", 3: "🟢"}.get(task['priority'], "⚪")
            print(f"{i}. {task['name']}")
            print(f"   {priority_emoji} 優先級: {task['priority']} | ⏱️ 預估: {task['estimated_days']} 天")
            print(f"   💡 備註: {task['task_remark']}")
            print()
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失敗：{str(e)}")
        return False
    except Exception as e:
        print(f"❌ 任務生成失敗：{str(e)}")
        return False

def main():
    """主函數"""
    print("\n" + "=" * 50)
    print("🤖 PrAjeKt AI 功能測試")
    print("=" * 50)
    
    # 執行測試
    results = []
    
    results.append(("環境配置", test_environment()))
    results.append(("套件安裝", test_package()))
    
    if results[0][1] and results[1][1]:
        results.append(("API 連線", test_api_connection()))
        if results[2][1]:
            results.append(("任務生成", test_task_generation()))
    
    # 顯示測試結果
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    # 總結
    all_passed = all(result for _, result in results)
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有測試通過！AI 功能已就緒！")
        print("\n下一步：")
        print("1. 啟動後端：python app.py")
        print("2. 啟動前端：npm run dev")
        print("3. 進入任意專案，點擊「✨ AI 生成任務」")
    else:
        print("⚠️  部分測試失敗，請檢查上述錯誤訊息")
        print("\n常見解決方案：")
        print("1. 安裝依賴：pip install langchain-google-genai")
        print("2. 配置 API Key：在 .env 中添加 GOOGLE_API_KEY")
        print("3. 檢查網路連線")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
