#!/usr/bin/env python
"""測試資料庫連接"""

import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:,U7a3A%NxfH7+-3@db.ojtdiktwjscfmagqepcg.supabase.co:5432/postgres'

from app import create_app
from models import db

app = create_app()

with app.app_context():
    try:
        # 測試資料庫連接
        result = db.session.execute(db.text('SELECT 1'))
        print("✅ PostgreSQL 連接成功！")
        
        # 顯示資原始 URI（隱藏密碼）
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        safe_uri = uri.replace(uri.split('@')[0].split('://')[1], '***:***')
        print(f"📊 資料庫 URI: {safe_uri}")
        
        # 計算表格數量
        inspector_query = """
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        result = db.session.execute(db.text(inspector_query))
        table_count = result.scalar()
        print(f"📋 已建立 {table_count} 個表格")
        
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
