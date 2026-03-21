#!/usr/bin/env python
"""初始化資料庫 - 直接建立所有表格"""

import os
import sys

# 設定 PostgreSQL 連接字串
os.environ['DATABASE_URL'] = 'postgresql://postgres:,U7a3A%NxfH7+-3@db.ojtdiktwjscfmagqepcg.supabase.co:5432/postgres'

from app import create_app
from models import db

def init_database():
    """直接建立資料庫表格"""
    app = create_app()
    with app.app_context():
        print("正在建立資料庫表格...")
        try:
            db.create_all()
            print("✅ 資料庫初始化成功！")
            return True
        except Exception as e:
            print(f"❌ 資料庫初始化失敗: {e}")
            return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
