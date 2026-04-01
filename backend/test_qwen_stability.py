#!/usr/bin/env python3
"""
Qwen3.5-9B 穩定性測試（10 次連續請求）
"""

import requests
import time
from datetime import datetime

BASE_URL = 'http://localhost:1234/v1/chat/completions'
RESULTS = []

print("\n🚀 開始 Qwen3.5-9B 10 次穩定性測試...\n")
print(f"⏰ 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

for i in range(1, 11):
    print(f"【{i}/10】開始第 {i} 次請求...", flush=True)
    
    payload = {
        'model': 'qwen',
        'messages': [
            {'role': 'user', 'content': '簡單說明 Flask 和 Django 的差別，用繁體中文回答。'}
        ],
        'max_tokens': 100,
        'temperature': 0.7
    }
    
    start = time.time()
    try:
        resp = requests.post(BASE_URL, json=payload, timeout=120)
        duration = time.time() - start
        
        data = resp.json()
        content = data['choices'][0]['message']['content']
        finish_reason = data['choices'][0]['finish_reason']
        
        print(f"  ✅ 成功（耗時 {duration:.1f}s，finish_reason: {finish_reason}）")
        print(f"  📝 {content[:60]}...\n", flush=True)
        
        RESULTS.append({
            'request': i,
            'status': 'success',
            'duration': duration,
            'finish_reason': finish_reason
        })
    except Exception as e:
        print(f"  ❌ 失敗: {str(e)}\n", flush=True)
        RESULTS.append({
            'request': i,
            'status': 'failed',
            'error': str(e)
        })
    
    if i < 10:
        time.sleep(2)

print("=" * 70)
print("📊 測試總結")
print("=" * 70)

success = sum(1 for r in RESULTS if r['status'] == 'success')
failed = sum(1 for r in RESULTS if r['status'] == 'failed')

print(f"✅ 成功: {success}/10")
print(f"❌ 失敗: {failed}/10")

if success > 0:
    avg_duration = sum(r['duration'] for r in RESULTS if r['status'] == 'success') / success
    min_duration = min(r['duration'] for r in RESULTS if r['status'] == 'success')
    max_duration = max(r['duration'] for r in RESULTS if r['status'] == 'success')
    print(f"⏱  平均耗時: {avg_duration:.1f} 秒")
    print(f"⏱  最小耗時: {min_duration:.1f} 秒")
    print(f"⏱  最大耗時: {max_duration:.1f} 秒")

print("\n詳細結果:")
for r in RESULTS:
    status_icon = "✅" if r['status'] == 'success' else "❌"
    if r['status'] == 'success':
        print(f"{status_icon} 請求 {r['request']}: {r['duration']:.1f}s ({r['finish_reason']})")
    else:
        print(f"{status_icon} 請求 {r['request']}: {r['error']}")

print("\n" + ("✅ Qwen 穩定性測試通過 - 所有 10 次請求成功！" if failed == 0 else f"⚠️  Qwen 穩定性測試有 {failed} 次失敗情況"))
print(f"⏰ 完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
