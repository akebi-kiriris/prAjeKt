#!/usr/bin/env python3
import os
from collections import defaultdict

EXTS = {'.py', '.ts', '.js', '.vue', '.html', '.css', '.scss', '.jsx', '.tsx'}
EXCLUDE_DIRS = {'.git', 'node_modules', 'frontend/dist', 'backend/venv', 'venv', '__pycache__', 'coverage', 'uploads', 'Image', 'frontend/coverage', 'dist'}

stats = defaultdict(lambda: {'files':0,'lines':0})

def should_exclude_dir(d):
    # exact match or prefix match for paths like frontend/dist
    for ex in EXCLUDE_DIRS:
        if d == ex:
            return True
    return False

for root, dirs, files in os.walk('.'):
    # normalize root to remove leading ./
    # prune excluded dirs in-place
    dirs[:] = [d for d in dirs if not should_exclude_dir(os.path.join(root, d).lstrip('./').replace('\\','/')) and d not in EXCLUDE_DIRS]
    for fname in files:
        path = os.path.join(root, fname)
        _, ext = os.path.splitext(fname)
        ext = ext.lower()
        if ext in EXTS:
            try:
                with open(path, 'rb') as f:
                    data = f.read()
            except Exception:
                continue
            lines = data.count(b'\n')
            if data and not data.endswith(b'\n'):
                lines += 1
            stats[ext]['files'] += 1
            stats[ext]['lines'] += lines

# print table
all_lines = sum(v['lines'] for v in stats.values())
print('Lines of Code by extension:')
for ext, v in sorted(stats.items(), key=lambda kv: kv[1]['lines'], reverse=True):
    print(f"{ext:>5}  files: {v['files']:4d}  lines: {v['lines']:7d}")
print('')
print(f'TOTAL_LINES: {all_lines}')
