import sqlite3

conn = sqlite3.connect('instance/learnlink.db')
c = conn.cursor()

# Check timelines columns
c.execute('PRAGMA table_info(timelines)')
cols = c.fetchall()
print('timelines columns:')
for col in cols:
    print(f'  {col[1]}: {col[2]}')

# Check all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print('\nAll tables:')
for t in tables:
    print(f'  {t[0]}')

# Check task_users table
print('\ntask_users schema:')
try:
    c.execute('PRAGMA table_info(task_users)')
    for col in c.fetchall():
        print(f'  {col[1]}: {col[2]}')
except Exception as e:
    print(f'  Error: {e}')

# Check timeline_users table
print('\ntimeline_users schema:')
try:
    c.execute('PRAGMA table_info(timeline_users)')
    for col in c.fetchall():
        print(f'  {col[1]}: {col[2]}')
except Exception as e:
    print(f'  Error: {e}')

# Check task_comments table
print('\ntask_comments schema:')
try:
    c.execute('PRAGMA table_info(task_comments)')
    for col in c.fetchall():
        print(f'  {col[1]}: {col[2]}')
except Exception as e:
    print(f'  Error: {e}')

conn.close()
