import sqlite3

# 連接資料庫
conn = sqlite3.connect('instance/learnlink.db')
c = conn.cursor()

# 創建 task_users 表 (任務成員表，記錄任務的負責人和協助者)
c.execute('''
CREATE TABLE IF NOT EXISTS task_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

# 創建 timeline_users 表 (時間軸成員表，記錄專案成員)
c.execute('''
CREATE TABLE IF NOT EXISTS timeline_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeline_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (timeline_id) REFERENCES timelines(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

# 創建 task_comments 表 (任務評論表)
c.execute('''
CREATE TABLE IF NOT EXISTS task_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
print("Tables created successfully!")

# 驗證表已創建
tables_to_check = ['task_users', 'timeline_users', 'task_comments']
for table_name in tables_to_check:
    c.execute(f'PRAGMA table_info({table_name})')
    cols = c.fetchall()
    print(f'\n{table_name} columns:')
    for col in cols:
        print(f'  {col[1]}: {col[2]}')

conn.close()
