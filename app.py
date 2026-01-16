from flask import Flask, request, jsonify , make_response,session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime
from datetime import timedelta
import mysql.connector
import json
import os
import bcrypt
import uuid
from flask import current_app
import re
import base64




app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
# CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5173"])
# CORS(app, supports_credentials=True, origins=["http://127.0.0.1"])
CORS(
    app,
    supports_credentials=True,
    origins=["http://127.0.0.1:5173", "http://127.0.0.1"]  # 同時允許開發和生產環境
)

# 配置上傳資料夾和允許的檔案類型
UPLOAD_FOLDER = 'task_files_uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx','PNG'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上傳大小為16MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 連接 MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="learnlink"
)
cursor = db.cursor(dictionary=True, buffered=True)


#獲取任務
@app.route('/timelines/<int:timeline_id>/tasks', methods=['GET'])
def get_tasks(timeline_id):
    try:
        # 首先獲取該時間軸的所有任務
        cursor.execute("""
            SELECT 
                task_id, name, 
                start_date, end_date, completed, 
                timeline_id, created_at, task_remark, isWork
            FROM tasks 
            WHERE timeline_id = %s
        """, (timeline_id,))
        tasks = cursor.fetchall()

        tasks_response = []
        for task in tasks:
            task_id = task["task_id"]
            
            # 獲取此任務的負責人（role = 0）
            cursor.execute("""
                SELECT u.name, u.id
                FROM task_users tu
                JOIN users u ON tu.user_id = u.id
                WHERE tu.task_id = %s AND tu.role = 0
                LIMIT 1  # 假設每個任務只有一個負責人
            """, (task_id,))
            assignee = cursor.fetchone()
            # assignee_info = {
            #     "id": assignee["id"] if assignee else None,
            #     "name": assignee["name"] if assignee else None
            # }
            assignee_info = assignee["name"]
            
            # 獲取此任務的所有助理（role = 1）
            cursor.execute("""
                SELECT u.id, u.name 
                FROM task_users tu
                JOIN users u ON tu.user_id = u.id
                WHERE tu.task_id = %s AND tu.role = 1
            """, (task_id,))
            assistants = cursor.fetchall()
            assistant_list = [a["name"] for a in assistants]

            tasks_response.append({
                "task_id": task_id,
                "name": task["name"],
                "assignee": assignee_info,  # 包含id和name的物件
                "assistant": assistant_list,  # 包含id和name的物件陣列
                "start_date": task["start_date"].strftime("%Y-%m-%d %H:%M:%S") if task["start_date"] else None,
                "end_date": task["end_date"].strftime("%Y-%m-%d %H:%M:%S") if task["end_date"] else None,
                "completed": bool(task["completed"]),
                "timeline_id": task["timeline_id"],
                "created_at": task["created_at"].strftime("%Y-%m-%d %H:%M:%S") if task["created_at"] else None,
                "remark": task["task_remark"],
                "isWork": bool(task["isWork"])
            })

        return jsonify(tasks_response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# 獲取單個任務詳情
@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task_details(task_id):
    db_conn = None
    cursor = None
    try:
        task_id = int(task_id)
        print(f"Fetching details for task ID: {task_id}")
        
        # 建立新的數據庫連接
        db_conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="learnlink",
            ssl_disabled=True
        )
        cursor = db_conn.cursor(dictionary=True, buffered=True)

        # 查询任务基本信息
        task_sql = """
            SELECT task_id, name, assignee, assistant, start_date, end_date, 
                   completed, timeline_id, created_at, task_remark, isWork
            FROM tasks 
            WHERE task_id = %s
        """
        cursor.execute(task_sql, (task_id,))
        task = cursor.fetchone()
        
        if not task:
            print(f"No task found with ID: {task_id}")
            return jsonify({"error": "Task not found"}), 404

        # 查询关联的留言
        comments_sql = """
            SELECT comment_id, user_id, task_message
            FROM task_comments
            WHERE task_id = %s
        """
        cursor.execute(comments_sql, (task_id,))
        comments = cursor.fetchall()

        # 格式化日期字段
        def format_date(dt):
            return dt.strftime('%Y/%m/%d %H:%M:%S') if isinstance(dt, datetime) else None

        # 处理 assistant 字段
        assistant = task["assistant"] or ""  # 處理 None 情況
        assistant_list = []
        try:
            if assistant.startswith("[") and assistant.endswith("]"):
                assistant_list = json.loads(assistant)
            else:
                assistant_list = [a.strip() for a in assistant.split(",") if a.strip()]
        except (json.JSONDecodeError, AttributeError):
            assistant_list = [assistant] if assistant else []

        # 构建响应数据
        response = {
            "task_id": task["task_id"],
            "name": task["name"],
            "assignee": task["assignee"],
            "assistant": assistant_list,
            "start_date": format_date(task["start_date"]),
            "end_date": format_date(task["end_date"]),
            "completed": bool(task["completed"]),
            "timeline_id": task["timeline_id"],
            "remark": task["task_remark"],
            "isWork": bool(task["isWork"]),
            "comments": [{
                "comment_id": c["comment_id"],
                "user_id": c["user_id"],
                "task_message": c["task_message"],
            } for c in comments]
        }

        print(f"Successfully fetched task details for ID: {task_id}")
        return jsonify(response)

    except mysql.connector.Error as e:
        print(f"MySQL error: {e}")
        return jsonify({"error": "Database error"}), 500
        
    except Exception as e:
        print(f"Error fetching task details: {e}")
        return jsonify({"error": "Internal server error"}), 500
        
    finally:
        # 確保關閉連接
        if cursor:
            cursor.close()
        if db_conn:
            db_conn.close()
    
    
#修改任務完成狀態
@app.route('/update-task-status', methods=['POST'])
def update_task_status():
    try:
        data = request.get_json()
        task_id = data['task_id']
        completed = data['completed']

        # 確保資料庫連接已經建立
        if cursor is None:
            return jsonify({"error": "Database connection is not available"}), 500

        # 更新任務的完成狀態
        sql = """
            UPDATE tasks
            SET completed = %s
            WHERE task_id = %s
        """
        cursor.execute(sql, (completed, task_id))

        # 提交更改
        db.commit()

        return jsonify({"message": "Task status updated successfully"}), 200

    except mysql.connector.Error as e:
        print(f"MySQL error: {e}")
        return jsonify({"error": "Database error"}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# 新增任務
@app.route('/tasks', methods=['POST'])
def add_Task():
    try:
        data = request.json  # 获取请求的 JSON 数据
        
        # 检查是否包含必要的字段
        required_fields = ["name", "completed", "timeline_id", "task_remark", "assignee"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # 处理日期，如果没有日期则为 None
        start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%dT%H:%M") if data.get("start_date") else None
        end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%dT%H:%M") if data.get("end_date") else None

        # SQL 插入任务数据
        sql = """
            INSERT INTO tasks (name, completed, timeline_id, start_date, end_date, task_remark, assignee, isWork)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data["name"],
            data["completed"],
            data["timeline_id"],
            start_date,
            end_date,
            data["task_remark"],
            data["assignee"],
            data["isWork"]   
        )
        
        cursor.execute(sql, values)
        new_task_id = cursor.lastrowid  # 获取新任务的 ID
        
        # 添加任務創建者到 task_users 表 (role=0)
        user_id = data.get('user_id')
        if user_id:
            task_user_sql = """
                INSERT INTO task_users (task_id, user_id, role)
                VALUES (%s, %s, 0)
            """
            cursor.execute(task_user_sql, (new_task_id, user_id))
        
        # 處理協助者 - 先根據學號查詢user_id
        student_ids = data.get('student_ids', [])  # 獲取學號列表
        assistant_user_ids = []  # 儲存找到的user_id
        
        if student_ids:
            # 構建IN查詢，一次查詢所有學號對應的user_id
            format_strings = ','.join(['%s'] * len(student_ids))
            sql = f"""
                SELECT id FROM users 
                WHERE student_id IN ({format_strings})
            """
            cursor.execute(sql, tuple(student_ids))
            results = cursor.fetchall()
            assistant_user_ids = [result['id'] for result in results]
            
            # 檢查是否有學號沒找到對應使用者
            if len(assistant_user_ids) != len(student_ids):
                found_student_ids = set(assistant_user_ids)
                missing_student_ids = [sid for sid in student_ids if sid not in found_student_ids]
                return jsonify({
                    "error": "Some student IDs not found",
                    "missing_student_ids": missing_student_ids
                }), 400
        
        # 添加協助者到 task_users 表 (role=1)
        for assistant_id in assistant_user_ids:
            assistant_sql = """
                INSERT INTO task_users (task_id, user_id, role)
                VALUES (%s, %s, 1)
            """
            cursor.execute(assistant_sql, (new_task_id, assistant_id))
        
        db.commit()  # 提交事务
        
        # 返回新任务数据
        task_data = {
            "task_id": new_task_id,
            "name": data["name"],
            "completed": data["completed"],
            "timeline_id": data["timeline_id"],
            "start_date": start_date.strftime('%Y-%m-%dT%H:%M') if start_date else None,
            "end_date": end_date.strftime('%Y-%m-%dT%H:%M') if end_date else None,
            "task_remark": data["task_remark"],
            "assignee": data["assignee"],
            "isWork": data["isWork"],
            "assistant_user_ids": assistant_user_ids  # 返回實際添加的user_id列表
        }

        return jsonify(task_data), 201

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while adding the task", "details": str(e)}), 500


# 刪除任務
@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        print(f"Deleting task with ID: {task_id}")  # 打印 task_id

        # 检查任务是否存在
        sql_check = "SELECT 1 FROM task_users WHERE task_id = %s"
        cursor.execute(sql_check, (task_id,))
        if cursor.fetchone() is None:
            print(f"No task found with ID: {task_id}")
            return jsonify({"error": "Task not found"}), 404

        # 执行删除操作
        sql = "DELETE FROM task_users WHERE task_id = %s"
        cursor.execute(sql, (task_id,))
        db.commit()

        # 确保有行被删除
        if cursor.rowcount == 0:
            print(f"No task deleted, task_id {task_id} might not exist")
            return jsonify({"error": "Task not found"}), 404

        print(f"Task with ID {task_id} deleted successfully")
        return jsonify({"message": f"Task {task_id} deleted successfully"}), 200  # 返回200成功状态

    except Exception as e:
        db.rollback()  # 遇到错误时回滚
        print(f"Error deleting task: {e}")
        return jsonify({"error": "Failed to delete task", "message": str(e)}), 500  # 返回500错误


# 新增專案
@app.route('/timelines', methods=['POST'])
def add_timeline():
    try:
        data = request.json
        # 保持与 GET 方法完全一致的 Cookie 获取方式
        user_id = data.get('user_id') or request.cookies.get('user_id')
        print(f"获取到的 user_id: {user_id}")  # 调试日志
        
        if not user_id:
            return jsonify({"error": "user_id 缺失"}), 401

        # 其余逻辑保持不变...
        sql = """
            INSERT INTO timelines (name, remark, start_date, end_date, progress, created_at) 
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        values = (
            data["name"],
            data.get("remark", ""),
            data["startDate"],
            data["endDate"],
            data.get("progress", 0)
        )
        cursor.execute(sql, values)
        db.commit()

        new_timeline_id = cursor.lastrowid
        
        # 关联 timeline_users 表
        cursor.execute(
            "INSERT INTO timeline_users   (timeline_id, id, role) VALUES (%s, %s, %s)",
            (new_timeline_id, user_id, 0)  # 直接使用获取到的 id
        )
        db.commit()

        return jsonify({
            "id": new_timeline_id,
            **data,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 201

    except Exception as e:
        db.rollback()
        print(f"新增專案失敗: {str(e)}")
        return jsonify({"error": "伺服器內部錯誤"}), 500


#獲取專案
# @app.route('/timelines', methods=['GET'])
# def get_timelines():
#     try:
#         #取得user_id
#         id = request.cookies.get('user_id') # 確保 Cookie 名稱正確
#         print(f"hello: {id}")  # 印出收到的 user_id

#         if not id:
#             return jsonify({"error": "user_id is required or not logged in"}), 401 # 401 代表未授權
        
#         # 查询所有的时间轴数据
#         sql = """
#         SELECT t.*
#         FROM timelines t
#         JOIN timeline_users tu ON t.timeline_id = tu.timeline_id
#         WHERE tu.id = %s;
#         """
#         cursor.execute(sql, (id,))
#         timelines = cursor.fetchall()  # 获取所有记录

#         # 确保处理 remark 字段
#         for timeline in timelines:
#             timeline["id"] = timeline["timeline_id"]  # 将 timeline_id 改为 id
#             del timeline["timeline_id"]  # 删除原始的 timeline_id 字段
#             timeline["startDate"] = str(timeline["start_date"])  # 转换字段名
#             timeline["endDate"] = str(timeline["end_date"])      # 转换字段名
#             del timeline["start_date"]  # 删除原始字段
#             del timeline["end_date"]    # 删除原始字段
#             timeline["remark"] = timeline.get("remark", "")  # 确保处理 remark 字段

#         return jsonify(timelines), 200
#     except Exception as e:
#         print("查询时间轴时发生错误:", e)
#         return jsonify({"error": "无法获取时间轴数据"}), 500

#獲取專案
@app.route('/timelines', methods=['GET'])
def get_timelines():
    try:
        # 取得 user_id
        user_id = request.cookies.get('user_id')
        print(f"hello: {user_id}")

        if not user_id:
            return jsonify({"error": "user_id is required or not logged in"}), 401

        # 查詢使用者參與的時間軸
        sql = """
        SELECT t.*
        FROM timelines t
        JOIN timeline_users tu ON t.timeline_id = tu.timeline_id
        WHERE tu.id = %s;
        """
        cursor.execute(sql, (user_id,))
        timelines = cursor.fetchall()

        result = []

        for timeline in timelines:
            timeline_id = timeline["timeline_id"]

            # 查 timeline_users + users 拿到該專案所有成員的 id、name、role
            member_sql = """
            SELECT tu.id, u.name, tu.role
            FROM timeline_users tu
            JOIN users u ON tu.id = u.id
            WHERE tu.timeline_id = %s;
            """
            cursor.execute(member_sql, (timeline_id,))
            members = cursor.fetchall()
            my_role = next((m["role"] for m in members if str(m["id"]) == str(user_id)), "member")

            # 整理 timeline 資料（保留所有欄位，只改必要欄位）
            timeline["id"] = timeline["timeline_id"]
            del timeline["timeline_id"]

            timeline["startDate"] = str(timeline["start_date"])
            timeline["endDate"] = str(timeline["end_date"])
            del timeline["start_date"]
            del timeline["end_date"]

            timeline["remark"] = timeline.get("remark", "")
            timeline["members"] = members  # 加入成員資訊
            timeline["role"] = my_role

            result.append(timeline)

        return jsonify(result), 200

    except Exception as e:
        print("查询时间轴时发生错误:", e)
        return jsonify({"error": "无法获取时间轴数据"}), 500





    
# 刪除專案
@app.route('/timelines/<int:timeline_id>', methods=['DELETE'])
def delete_timeline(timeline_id):
    try:
        data = request.json
        # 统一获取user_id的方式
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id') or request.cookies.get('user_id')
        
        if not user_id:
            return jsonify({"error": "需要用户凭证"}), 401

        with db.cursor() as cursor:
            # 简单权限检查（可根据需求调整）
            cursor.execute(
                "SELECT 1 FROM timeline_users WHERE timeline_id = %s AND id = %s",
                (timeline_id, user_id)
            )
            if not cursor.fetchone():
                return jsonify({"error": "无权操作此專案"}), 403

            # 删除操作
            cursor.execute("DELETE FROM timeline_users WHERE timeline_id = %s", (timeline_id,))
            cursor.execute("DELETE FROM timelines WHERE timeline_id = %s", (timeline_id,))
            db.commit()

            return jsonify({"message": "刪除成功"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": "刪除失敗", "detail": str(e)}), 500


#新增留言
@app.route('/add-comment', methods=['POST'])
def add_comment():
    try:
        data = request.get_json()
        task_id = data['task_id']
        user_id = data['user_id']  # 预设为 1
        task_message = data['task_message']

        # 插入评论到任务评论表
        cursor.execute("""
            INSERT INTO task_comments (task_id, user_id, task_message)
            VALUES (%s, %s, %s)
        """, (task_id, user_id, task_message))

        db.commit()

        return jsonify({"message": "Comment added successfully"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    

#獲取留言    
# @app.route('/tasks/<int:task_id>/comments', methods=['GET'])
# def get_comments(task_id):
#     try:
#         print(f"Fetching comments for task_id {task_id}")  # Debugging

#         sql = "SELECT comment_id, user_id, task_message FROM task_comments WHERE task_id = %s"
#         cursor.execute(sql, (task_id,))
#         comments = cursor.fetchall()

#         if not comments:
#             print(f"No comments found for task_id {task_id}")  # Debugging
#             return jsonify({"message": "No comments found for this task"}), 404

#         print(f"Fetched comments: {comments}")  # Debugging
#         print(f"Fetching comments for task_id {task_id}")

#         return jsonify(comments), 200

#     except Exception as e:
#         print(f"Error fetching comments: {e}, type: {type(e)}")  # Debugging
#         return jsonify({"error": "Failed to fetch comments", "message": str(e)}), 500

#獲取留言0507
@app.route('/tasks/<int:task_id>/comments', methods=['GET'])
def get_comments(task_id):
    try:
        print(f"Fetching comments for task_id {task_id}")
        
        # 使用新的數據庫連接
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="learnlink",
            ssl_disabled=True
        )
        cursor = db.cursor(dictionary=True)

        sql = """
            SELECT 
                c.comment_id,
                c.user_id,
                u.name AS user_name,
                c.task_message
            FROM task_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.task_id = %s
            ORDER BY c.comment_id ASC
        """
        cursor.execute(sql, (task_id,))
        comments = cursor.fetchall()

        # 處理可能的二進位數據
        for comment in comments:
            if isinstance(comment['task_message'], (bytes, bytearray)):
                comment['task_message'] = base64.b64encode(comment['task_message']).decode('utf-8')

        return jsonify(comments), 200

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        # 確保關閉連接
        if 'cursor' in locals(): cursor.close()
        if 'db' in locals(): db.close()



# 修改專案備註
@app.route('/timelines/<int:timeline_id>/remark', methods=['PUT'])
def update_remark(timeline_id):
    data = request.json
    new_remark = data.get("remark")

    if not new_remark:
        return jsonify({"error": "備註不能為空"}), 400

    sql = "UPDATE timelines SET remark = %s WHERE timeline_id = %s"
    cursor.execute(sql, (new_remark, timeline_id))
    db.commit()

    return jsonify({"message": "備註更新成功"}), 200

#設cookie


#透過cookie獲取使用者id

@app.route('/set_flask_session', methods=['POST'])
def set_flask_session():
    user_id = request.form.get('user_id')
    if user_id:
        session['user_id'] = user_id
        session['logged_in'] = True
        session.permanent = True
        resp = make_response('Setting a cookie!')
        resp.set_cookie('user_id',user_id)
        print(f"Received user_id in /set_flask_session: {user_id}")  # 印出收到的 user_id
        return jsonify({'message': 'Flask Session set successfully'})
    else:
        print("User ID not provided in /set_flask_session") #印出沒有收到user_id
        return jsonify({'error': 'User ID not provided'}), 400

@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    user_id = session.get('user_id')
    if user_id:
        print(f"Received user_id in /set_flask_session: {user_id}", flush=True)
        return jsonify({'user_id': user_id})
    else:
        print(f"Received user_id in /set_flask_session: {user_id}")  # 印出收到的 user_id
        return jsonify({'user_id': None})
    
@app.route('/set_user_id', methods=['POST'])
def set_user_id():
    user_id = request.form.get('user_id')
    if user_id:
        session['user_id'] = user_id
        return jsonify({'message': 'User ID set successfully'})
    else:
        return jsonify({'error': 'User ID not provided'}), 400

@app.route('/get_user_id')
def get_user_id():
    user_id = session.get('user_id')
    if user_id:
        return jsonify({'user_id': user_id})
    else:
        return jsonify({'error': 'User ID not found'}), 404

#登入
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "請求無效"}), 400

    email = data['email']
    password = data['password']

    # 直接使用已建立的資料庫連接
    cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()

    if row and bcrypt.checkpw(password.encode('utf-8'), row['password'].encode('utf-8')):
        session['user_id'] = row['id']
        return jsonify({"success": True})
    else:
        return jsonify({"error": "登入失敗"}), 401
    
@app.route('/test_cookie')
def test_cookie():
    user_id = request.cookies.get('user_id')
    return jsonify({'user_id': user_id})

#上傳檔案
# 檢查是否是允許的檔案類型
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # 基本檢查
        if 'file' not in request.files or 'taskId' not in request.form:
            return jsonify({'error': 'Missing file or taskId'}), 400

        file = request.files['file']
        task_id = request.form['taskId']
        user_id = request.form.get('userId')

        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        if file.content_length > MAX_FILE_SIZE:
            return jsonify({'error': 'File size exceeds limit'}), 400

        # 生成唯一檔名
        original_filename = clean_filename(file.filename)
        ext = os.path.splitext(original_filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        relative_path = os.path.join('uploads', unique_name)
        absolute_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)

        # 儲存檔案
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        file.save(absolute_path)

        # 資料庫操作
        try:
            cursor = db.cursor()

            cursor.execute("""
                INSERT INTO task_uploaded_files (
                    original_filename, storage_path, file_size, 
                    uploader_id, task_id, upload_time
                ) VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                original_filename,
                relative_path,  # 存相對路徑
                os.path.getsize(absolute_path),
                user_id,
                task_id
            ))
            file_id = cursor.lastrowid
            db.commit()

            return jsonify({
                'file_id': file_id,
                'original_filename': original_filename,
                'stored_filename': unique_name,
                'file_size': os.path.getsize(absolute_path),
                'download_url': f"/download/{unique_name}",
                'uploader_id': user_id,
                'task_id': task_id
            }), 200

        except Exception as e:
            current_app.logger.error(f"Database error: {e}")
            if db: db.rollback()
            # 刪除已上傳的檔案
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
            return jsonify({'error': 'Database operation failed'}), 500


    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/tasks/<int:task_id>/files', methods=['GET'])
def get_task_files(task_id):
    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                file_id,
                original_filename , 
                storage_path AS stored_filename,
                file_size,
                uploader_id,
                task_id,
                upload_time
            FROM task_uploaded_files 
            WHERE task_id = %s
            ORDER BY upload_time DESC
        """, (task_id,))
        
        files = cursor.fetchall()
        db.commit()
        
        # 添加下載URL
        for file in files:
            filename = os.path.basename(file['stored_filename'])
            file['download_url'] = f"/download/{filename}"  # 確保URL乾淨
        
        return jsonify({'files': files})

    except Exception as e:
        current_app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database operation failed'}), 500
    
@app.route('/download/<filename>')
def download_file(filename):
    try:
        # 確保是絕對路徑
        upload_folder = os.path.join(os.getcwd(), 'task_files_uploads')
        
        # 查詢資料庫以獲取 original_filename
        cursor = db.cursor(dictionary=True)
        
        # 假設資料庫中存儲的路徑為 `uploads/<filename>`
        storage_path = os.path.join('uploads', filename)
        
        cursor.execute("""
            SELECT original_filename 
            FROM task_uploaded_files 
            WHERE storage_path = %s
        """, (storage_path,))
        
        file_data = cursor.fetchone()
        
        if file_data:
            original_filename = file_data['original_filename']
        else:
            return jsonify({'error': 'File not found'}), 404
        
        # 使用 original_filename 作為下載的檔案名稱
        return send_from_directory(
            directory=upload_folder,
            path=filename,  # 真正的檔案路徑
            as_attachment=True,
            download_name=original_filename  # 下載檔案名稱是 original_filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Download error: {e}")
        return jsonify({'error': 'Download failed'}), 500

# 自行過濾可能有風險的字元（保留中文）
def clean_filename(filename):
    # 僅過濾特殊符號，例如 / \ ? % * : | " < > 等
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

#邀請人員
@app.route('/search_user_by_student_id', methods=['POST'])
def search_user_by_student_id():
    try:
        data = request.get_json()

        student_id = data.get('student_id')
        if not student_id:
            return jsonify({'error': 'student_id is required'}), 400

        sql = "SELECT id, name FROM users WHERE student_id = %s"
        cursor.execute(sql, (student_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': '找不到該使用者'}), 404

        return jsonify({
            'id': user['id'],
            'name': user['name']
        }), 200

    except Exception as e:
        print("查詢使用者時發生錯誤:", e)
        return jsonify({'error': '伺服器錯誤'}), 500

# @app.route('/invite_user_to_timeline', methods=['POST'])
# def invite_user_to_timeline():
#     try:
#         # 接收前端傳來的數據
#         data = request.get_json()
#         print("Received data:", data)  # 打印接收到的数据
#         timeline_id = data.get('timeline_id')
#         user_id = data.get('user_id')

#         if not timeline_id or not user_id:
#             return jsonify({'error': 'timeline_id and user_id are required'}), 400
        
#         # 將該使用者加入 timeline_users 表
#         sql = """
#             INSERT INTO timeline_users (timeline_id, id, role)
#             VALUES (%s, %s, 1)
#         """
#         cursor.execute(sql, (timeline_id, user_id))
#         db.commit()

#         return jsonify({'message': '邀請成功'}), 200

#     except Exception as e:
#         print("邀請使用者時發生錯誤:", e)
#         db.rollback()  # 回滾事務
#         return jsonify({'error': '伺服器錯誤'}), 500
@app.route('/invite_user_to_timeline', methods=['POST'])
def invite_user_to_timeline():
    try:
        # 接收前端传来的数据
        data = request.get_json()
        print("Received data:", data)  # 打印接收到的数据
        timeline_id = data.get('timeline_id')
        user_id = data.get('user_id')

        if not timeline_id or not user_id:
            return jsonify({'error': 'timeline_id and user_id are required'}), 400
        
        # 将该用户加入 timeline_users 表
        sql = """
            INSERT INTO timeline_users (timeline_id, id, role)
            VALUES (%s, %s, 1)  # 这里假设默认角色为 '1'（成员）
        """
        cursor.execute(sql, (timeline_id, user_id))
        db.commit()

        # 查询新加入的成员资料（从 timeline_users 表中查询）
        sql = """
            SELECT u.id, u.name, tu.role 
            FROM users u
            JOIN timeline_users tu ON u.id = tu.id
            WHERE tu.timeline_id = %s AND tu.id = %s
        """
        cursor.execute(sql, (timeline_id, user_id))
        new_member = cursor.fetchone()

        return jsonify({'message': '邀请成功', 'new_member': new_member}), 200

    except Exception as e:
        print("邀请用户时发生错误:", e)
        db.rollback()  # 回滚事务
        return jsonify({'error': '服务器错误'}), 500



#任務相關人員
@app.route('/search_user_by_student_id_task', methods=['POST'])
def search_user_by_student_id_task():
    keyword = request.get_json().get('keyword')
    if not keyword:
        return jsonify({'users': []})

    cursor.execute("""
        SELECT id, name, student_id FROM users 
        WHERE student_id LIKE %s LIMIT 5
    """, ('%' + keyword + '%',))
    users = cursor.fetchall()
    return jsonify({'users': users})  # 確保返回的格式正確

@app.route('/invite_assistants_to_task', methods=['POST'])
def invite_assistants_to_task():
    try:
        data = request.json
        task_id = data.get("task_id")
        student_ids = data.get("student_ids", [])

        for student_id in student_ids:
            # 依據學號查詢 user_id
            cursor.execute("SELECT id FROM users WHERE student_id = %s", (student_id,))
            user = cursor.fetchone()
            if user:
                user_id = user[0]
                cursor.execute(
                    "INSERT INTO task_users (task_id, user_id, role) VALUES (%s, %s, %s)",
                    (task_id, user_id, 1)  # role=1 表示被邀請的助理
                )
        
        db.commit()
        return jsonify({"message": "Assistants invited successfully."}), 200

    except Exception as e:
        db.rollback()
        print("Error inviting assistants:", e)
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=5000)