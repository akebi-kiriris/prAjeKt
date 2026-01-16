<template>
  <div class="header">
      <img src="D:\gra\htdocs\graduation\graduation-frontend\src\Learnlink-home.png" alt="Home" onclick="location.href='Project.html'">
    <div>
      <img src="D:\gra\htdocs\graduation\graduation-frontend\src\notification_icon.png" alt="Notifications" onclick="alert('Notifications')">
      <img src="D:\gra\htdocs\graduation\graduation-frontend\src\profile_icon.png" alt="Profile" onclick="logout()">
    </div>
  </div>
  <div class="container" style="height:67vw;">
  <div class="sidebar">
    <button onclick="window.location.href='http://127.0.0.1/Learnlink/畢業專題網頁/Project.html'">主頁</button>
    <button onclick="location.href='search.html'">搜尋</button>
    <button onclick="location.href='Manage.html'">選修課程</button>
    <button class="active" >專案</button>
    <button onclick="location.href='to_do_list.html'">待辦事項</button>
    <button onclick="location.href='message.html'">訊息</button>
  </div>
  <div class="content">
    <h3 style="font-size: 28px; font-weight: bold; ">專案</h3>

    <button @click="openAddTimelinePanel" style="height: 15px;">新增專案</button>
    <!-- 專案面板 (查看專案) -->
    <div class="timeline-list">
      <div 
        v-for="timeline in timelines" 
        :key="timeline.id" 
        class="timeline-item" 
        @click="selectTimeline(timeline)"
      >
        <div class="timeline-label">
          {{ timeline.name }}
        </div>
        
        <div class="timeline-bar-container">
          <div 
            class="timeline-bar" 
            :style="{ width: timeline.progress + '%', background: timeline.color }"
          ></div>
        </div>

        <div class="timeline-details">
          📅 {{ timeline.startDate }} ~ {{ timeline.endDate }}
        </div>
        
      </div>
      <!--將要到期任務面板-->
      <div class="deadline_task-box" v-show="deadline_task_check">
        <!-- 面板頭部 -->
        <div class="task-header">
          <h3>將要到期的任務</h3>
          <button class="close-btn" @click="deadline_task_check = false">×</button>
        </div>
        
        <!-- 内容區域 -->
        <div class="task-content">
          <!-- 加載狀態 -->
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <p>加載任務資料中...</p>
          </div>
          
          <!-- 正常顯示 -->
          <template v-else-if="currentTask">
            <div class="task-field">
              <span class="field-label">任務名稱:</span>
              <span class="field-value">{{ currentTask.name }}</span>
            </div>
            
            <div class="task-field">
              <span class="field-label">完成狀態:</span>
              <span class="field-value">{{ currentTask.completed ? '✅' : '❌' }}</span>
            </div>
            
            <template>
              <div class="task-field">
                <span class="field-label">👤 負責人ID:</span>
                <span class="field-value">{{ currentTask.assignee_id || '无' }}</span>
              </div>
              <div class="task-field">
                <span class="field-label">👤 負責人:</span>
                <span class="field-value">{{ currentTask.assignee }}</span>
              </div>
            </template>
            
            <div class="task-field">
              <span class="field-label">專案ID:</span>
              <span class="field-value">{{ currentTask.timeline_id }}</span>
            </div>
            
            <div class="task-field">
              <span class="field-label">📅 開始時間:</span>
              <span class="field-value">{{ formatDate(currentTask.start_date) }}</span>
            </div>
            
            <div class="task-field">
              <span class="field-label">📅 截止時間:</span>
              <span class="field-value">{{ formatDate(currentTask.end_date) }}</span>
            </div>
            
            <div class="task-field">
              <span class="field-label">備註:</span>
              <span class="field-value">{{ currentTask.task_remark || '無' }}</span>
            </div>
            
            <div class="task-field">
              <span class="field-label">類型:</span>
              <span class="field-value">{{ currentTask.isWork ? '🛠️ 工作' : '📌 任務' }}</span>
            </div>
            
            <div class="comments-section" v-if="currentTask.comments && currentTask.comments.length">
              <h4>留言區 (共 {{ currentTask.comments.length }} 條)</h4>
              <div v-for="(comment, index) in currentTask.comments" :key="comment.comment_id || index" class="comment">
                <div class="comment-field" v-if="comment.comment_id">
                  <span class="field-label">ID:</span>
                  <span class="field-value">{{ comment.comment_id }}</span>
                </div>
                <div class="comment-field">
                  <span class="field-label">用戶:</span>
                  <span class="field-value">{{ comment.user_id || '匿名用戶' }}</span>
                </div>
                <div class="comment-field">
                  <span class="field-label">內容:</span>
                  <span class="field-value">{{ comment.task_message }}</span>
                </div>
                <hr v-if="index < currentTask.comments.length - 1">
              </div>
            </div>
            <div v-else class="no-comments">
              <p>此任務暫無留言</p>
            </div>
          </template>
          
          <!-- 空狀態 -->
          <div v-else class="empty-state">
            <span class="empty-icon">📭</span>
            <p>未找到任務數據</p>
            <button @click="deadline_task_check = false">關閉面板</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 彈出面板 (新增專案) -->
    <transition name="slide">
      <div v-if="isAddingTimeline" class="detail-panel">
        <div class="detail-header">
        <h3 style="font-size: 28px; font-weight: bold;">新增專案</h3>
        </div>

        <label>名稱：</label>
        <input v-model="newTimeline.name" type="text" />
        <br>
        <label>備註：</label>
        <input v-model="newTimeline.remark" type="text" />
        <br>
        <label>開始時間：</label>
        <input v-model="newTimeline.startDate" type="date" />
        <br>
        <label>結束時間：</label>
        <input v-model="newTimeline.endDate" type="date" />
        <br>
        <div>
        <button @click="addTimeline">確認新增</button>
        <button class="button" @click="closeAddTimelinePanel">✖</button>
        </div>
      </div>
    </transition>

    <!-- 彈出面板 (查看專案詳細) -->
    <transition name="slide">
      <div v-if="selectedTimeline"  class="detail-panel" ref="draggablePanel"> 
        <div class="detail-header">
          <h3 style="font-size: 28px; font-weight: bold; text-align: center;">{{ selectedTimeline.name }}</h3>
        </div>
        <div style="display: flex; justify-content: center; gap: 8px; margin: 10px 0;">
          <button @click="openSharePanel">🔗 邀請人員</button>
          <button @click="deleteTimeline">🗑️ 刪除專案</button>
          <button @click="isRemarkVisible = !isRemarkVisible">📌 備註</button>
        </div>
        <!-- 邀請面板 -->
        <div v-if="isSharePanelOpen" class="share-panel">
          <div class="share-header">
            <h3>輸入學生學號</h3>
          </div>

          <div class="input-group">
            <input
              v-model="inputStudentId"
              placeholder="請輸入 student_id"
              class="student-input"
            />
            <button @click="searchStudent">查詢</button>
          </div>

          <div v-if="searchResult" class="result-box">
            <p>👤 查詢結果：</p>
            <p><strong>ID：</strong>{{ searchResult.id }}</p>
            <p><strong>姓名：</strong>{{ searchResult.name }}</p>
          </div>

          <div v-if="searchError" class="error-msg">
            {{ searchError }}
          </div>

          <button @click="confirmShare">確定邀請</button>
          <button class="close-btn" @click="isSharePanelOpen = false">✖</button>
        </div>

        <div v-if="isRemarkVisible" class="detail-panel-remark">
          <h3>備註:</h3>

          <div v-if="isEditingRemark">
            <input
              v-model="newRemark"
              @keyup.enter="editRemark"
              @blur="editRemark"
              type="text"
              placeholder="輸入新的備註..."
              autofocus
            />
          </div>

          <div v-else>
            <p>{{ selectedTimeline?.remark || "無備註" }}</p>
            <button @click="startEditingRemark">修改備註</button>
          </div>
        </div>
        <!-- 列出該專案的所有任務 -->
        <div class="task-container">
          <template v-if="selectedTimeline.tasks && selectedTimeline.tasks.length">
          <!--<h3>📌 任務/工作列表</h3>-->
          <div v-for="(task, index) in selectedTimeline.tasks" :key="task.task_id" class="task-box">
            
            <!-- 如果該任務被選中，顯示詳情 -->
            <div v-if="selectedTask && selectedTask.task_id === task.task_id" class="task-info" >
              <h3>{{ selectedTask.name }} (ID: {{ task.task_id }})</h3>
              <button @click="updateTaskStatus">
                狀態：<span :class="{ completed: selectedTask.completed }">
                  {{ selectedTask.completed ? '✅ 完成' : '❌ 未完成' }}
                </span>
              </button>
              <p>👤 負責人：{{ selectedTask.assignee }}</p>
              <p v-if="selectedTask.assistant">
                👤 相關人員：
                {{ typeof selectedTask.assistant === "string" ? selectedTask.assistant : selectedTask.assistant.join('、') }}
              </p>
              <p>📅 開始日期：{{ task.start_date }}</p>
              <p v-if="task.end_date">📅 截止日期：{{ task.end_date }}</p>

              <!-- 留言區域 -->
              <div class="comments-section" v-if="selectedTask">
                <h4>留言區</h4>

                <!-- 顯示留言 -->
                <div v-if="selectedTask.comments && selectedTask.comments.length">
                  <div v-for="(comment, commentIndex) in selectedTask.comments" :key="commentIndex" class="comment">
                    <p><strong>用戶 ID {{ comment.user_id }}:</strong> {{ comment.task_message }}</p>
                  </div>
                </div>
                <div v-else>
                  <p>此任務尚無留言。</p>
                </div>
                <input v-model="newComment" type="text" placeholder="寫下你的留言..." />
                <!-- 留言按鈕 -->
                <button @click="addComment(selectedTask)">留言</button>

                <!-- 檔案上傳區 -->
                <div>
                  <input 
                    v-if="selectedTask"
                    type="file"
                    :ref="(el) => {
                      if (selectedTask && el) {
                        setFileInputRef(el, selectedTask.task_id);
                      }
                    }"
                    @change="(e) => handleFileChange(e, selectedTask.task_id)"
                    style="display: none"
                    :key="'file-input-' + selectedTask.task_id"
                  />
                  <button @click="() => triggerFileInput(selectedTask.task_id)">
                    上傳檔案
                  </button>

                  <!-- 上傳狀態顯示 -->
                  <div v-if="uploadStatus[selectedTask.task_id]" class="upload-status">
                    <p :class="uploadStatus[selectedTask.task_id].class">
                      {{ uploadStatus[selectedTask.task_id].message }}
                    </p>
                    <progress 
                      v-if="uploadStatus[selectedTask.task_id].progress > 0"
                      :value="uploadStatus[selectedTask.task_id].progress"
                      max="100"
                    ></progress>
                  </div>
                </div>

                <!-- 檔案列表顯示 -->
                <div v-if="selectedTask.files && selectedTask.files.length" class="file-list">
                  <h4>已上傳檔案：</h4>
                  <ul>
                    <li v-for="file in selectedTask.files" :key="file.file_id">
                      <a :href="`http://localhost:5000${file.download_url}`" target="_blank" :download="file.original_filename">
                        {{ file.original_filename }} ({{ formatFileSize(file.file_size) }})
                      </a>
                    </li>
                  </ul>
                </div>
                <div v-else>
                  <p>尚未上傳任何檔案</p>
                </div>
              </div>


              <!-- 返回列表按鈕 -->
              <button @click="clearSelectedTask">🔙 返回列表</button>

            </div>

            <div v-else style="display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px; width: 100%">
              <h3>{{ task.isWork ? '🛠️ 工作' : '📌 任務' }} : {{ task.name }}</h3>
              <p>備註 : {{ task.remark }}</p>
              <p>👤 負責人：{{ task.assignee }}</p>
              <p v-if="task.assistant && task.assistant.length">👤 相關人員：{{ task.assistant.join('、') }}</p>
              <!--<p>👤 相關人員：{{ task.assistant.join('、') }}</p>-->
              <p>📅 開始日期：{{ task.start_date }}</p>
              <p v-if="task.end_date">📅 截止日期：{{ task.end_date }}</p>
              
              <!-- 新增的按钮容器 -->
              <div style="display: flex; gap: 8px; justify-content: center;">
                <button @click="handleClick(task)">查看詳情</button>
                <button class="delete-btn" @click="deleteTask(task.task_id)">刪除</button>
              </div>
            </div>

          </div>
          </template>
            <!-- 如果没有任务，显示提示信息 -->
          <div v-else class="no-tasks-message">
            <p>📭 目前沒有任務</p>
          </div>
        </div>
        <div style="display: flex; justify-content: center; gap: 8px; margin: 10px 0;">
          <button @click="openAddTaskPanel">新增任務/工作</button>
          <button @click="closeDetailPanel">✖</button>
        </div>

      </div>
    </transition>


    <!-- 彈出面板 (新增任務) -->
    <transition name="slide">
      <div v-if="isAddingTask" class="detail-panel">
        <div class="detail-header">
          <h3 style="font-size: 28px; font-weight: bold; ">新增任務/工作</h3>
        </div>

        <label>名稱：</label>
        <input v-model="newTask.name" type="text" />
        <br>

        <label>負責人：</label>
        <input v-model="newTask.assignee" type="text" />
        <br>

        <!-- 相關人員輸入 -->
        <label>相關人員：</label>
        <input v-model="assistantInput" type="text" placeholder="輸入學號以搜尋姓名" />

        <!-- 即時建議 -->
        <ul v-if="assistantSuggestions.length > 0" class="suggestions">
          <li v-for="user in assistantSuggestions" :key="user.id" @click="addAssistant(user.student_id)">
            {{ user.student_id }} - {{ user.name }}
          </li>
        </ul>

        <!-- 已選擇的相關人員清單 -->
        <div class="selected-assistants">
          <span v-for="sid in assistantIds" :key="sid" class="selected-chip">
            {{ sid }}
            <button @click="removeAssistant(sid)">✖</button>
          </span>
        </div>
        <br>

        <label>備註：</label>
        <input v-model="newTask.remark" type="text" />
        <br>

        <!-- 是否為工作任務選擇 -->
        <label>
          <input type="checkbox" v-model="newTask.isWork"/>
          這是一個工作
        </label>
        <br>

        <label>開始日期：</label>
        <input v-model="newTask.startDate" type="datetime-local" />
        <br>

        <!-- 當 isWork 為 false 才顯示截止日期 -->
        <template v-if="!newTask.isWork">
          <label>截止日期：</label>
          <input v-model="newTask.endDate" type="datetime-local" />
          <br>
        </template>
        <div>
          <button @click="addTask">確認新增</button>
          <button class="button" @click="closeAddTaskPanel">✖</button>
        </div>
      </div>
    </transition>
  </div>
  </div>

</template>

<script setup>
import { ref, onMounted ,watch,computed} from "vue";
import { useRouter } from 'vue-router'
import axios from "axios";
import VueCookies from "vue-cookies";



const isWork = ref(false);
const timelines = ref([]);
const selectedTimeline = ref(null);
const selectedTask = ref(null);
const isAddingTimeline = ref(false);
const isAddingTask = ref(false);
const isTask= ref(false)
const isSharePanelOpen = ref(false);  // 控制分享面板的顯示
const selectedGroups = ref([]);       // 存放使用者選擇的分享對象
const newComment = ref(''); 
const isEditingRemark = ref(false);
const newRemark = ref(""); // 存放新的備註內容
const isPasted = ref(true);
const deadline_task_check = ref(true);

const taskInCookie = ref(false); // 用来存储 task 是否为 true
//const taskIdFromCookie = computed(() => getCookie("task_id"));
const urlParams = new URLSearchParams(window.location.search);
const taskIdFromCookie = computed(() => urlParams.get('task_id'));

//監聽時間軸
watch(selectedTimeline, (newTimeline) => {
  if (newTimeline && newTimeline.id) {
    console.log("Selected Timeline ID is:", newTimeline.id);
  }
});

const newTimeline = ref({
  name: '',
  startDate: '', // 設定當前日期 + 時間（時:分）
  endDate: '',
  remark: ''
});

const newTask = ref({
  name: '',
  assignee: '',
  assistant: '',
  start_date: null,  
  end_date: null,    
  task_remark: '',   
  completed: 0,      
  timeline_id: null,
  isWork:'' 
});

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}


const userId = $cookies.get('user_id'); // 確保 Cookie 名稱正確
console.log('User ID from Cookie:', userId);


//獲取專案
const fetchTimelines = async () => {
  try {
    const response = await axios.get(`http://127.0.0.1:5000/timelines`, {
          withCredentials: true, // 確保發送 Cookie
        });

    // 确保返回的数据是有效的并且是一个数组
    if (!response.data || !Array.isArray(response.data)) {
      console.error("获取时间轴时发生错误: 无效的数据格式", response.data);
      return;
    }

    // 对每个时间轴的数据进行映射和处理
    timelines.value = response.data.map(timeline => {
      const startDate = new Date(timeline.startDate);
      const endDate = new Date(timeline.endDate);
      const startTime = startDate.getTime();
      const endTime = endDate.getTime();

      // 检查日期是否有效，避免 NaN
      if (isNaN(startTime) || isNaN(endTime)) {
        console.warn(`时间轴 "${timeline.name}" 日期格式错误`, timeline);
        return null;  // 如果日期无效，则跳过该时间轴
      }

      return {
        id: timeline.id, 
        name: timeline.name,
        startDate: timeline.startDate, 
        endDate: timeline.endDate,
        progress: timeline.progress ?? 0,  // 如果进度为 null，则设为 0
        remark: timeline.remark ?? "", // 如果 remark 为 null，则设为空字符串
        tasks: Array.isArray(timeline.tasks) ? timeline.tasks : [], // 确保 tasks 为数组
        color: getColor(startTime, endTime)
      };
    }).filter(timeline => timeline !== null); // 过滤掉无效的时间轴

    console.log("成功获取时间轴:", timelines.value);
  } catch (error) {
    console.error("获取时间轴时发生错误:", error);
  }
};


//獲取任務
// 確保 assistant 為陣列
const fetchTasks = async (timelineId) => {
  try {
    const response = await axios.get(`http://localhost:5000/timelines/${timelineId}/tasks`);
    const tasks = response.data.map(task => {
      task.assistant = Array.isArray(task.assistant) ? task.assistant : [];
      return task;
    });
    // 後端已確保 assistant 是陣列，這裡不需要再轉換
    //const tasks = response.data.map(task => ({
    //  ...task,
    //  // 確保日期欄位處理
    //  start_date: task.start_date ? new Date(task.start_date) : null,
    //  end_date: task.end_date ? new Date(task.end_date) : null,
    //  created_at: new Date(task.created_at)
    //}));

    // 更新對應專案的任務列表
    const timeline = timelines.value.find(t => t.id === timelineId);
    if (timeline) {
      timeline.tasks = tasks;
    }

    // 如果當前選中的專案是這個專案，更新 selectedTimeline
    if (selectedTimeline.value && selectedTimeline.value.id === timelineId) {
      selectedTimeline.value.tasks = tasks;
    }
  } catch (error) {
    console.error("取得任務時發生錯誤:", error);
  }
};


//獲取單個任務詳情
const loading = ref(false)
const error = ref(null)
const currentTask = ref(null)  // 取代原本的 selectedTask
const fetchTaskDetails = async (taskIdFromCookie) => {
  console.log("從url获取的task_id:", taskIdFromCookie)
  try {
    loading.value = true
    const response = await axios.get(`http://localhost:5000/tasks/${taskIdFromCookie}`)
    currentTask.value = response.data  // 將資料存入 currentTask
    console.log("獲取的任務資料:", currentTask.value)  // 確認資料是否正確載入
  } catch (err) {
    error.value = err.response?.data?.error || '獲取任務詳情失敗'
    console.error('獲取任務錯誤:', err)
  } finally {
    loading.value = false
  }
}

//更新任務完成狀態
const updateTaskStatus = async () => {
  // 確保 selectedTask 已經定義
  if (!selectedTask.value) {
    console.error('selectedTask is undefined');
    return; // 防止繼續執行
  }

  // 切換完成狀態
  selectedTask.value.completed = !selectedTask.value.completed;

  try {
    const response = await fetch('http://localhost:5000/update-task-status', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        task_id: selectedTask.value.task_id,   // 確保發送了 task_id
        completed: selectedTask.value.completed // 確保發送了完成狀態
      })
    });

    if (response.ok) {
      console.log('Task status updated successfully');
    } else {
      const errorData = await response.json(); // 獲取錯誤訊息
      console.error('Failed to update task status:', errorData.error);
    }
  } catch (error) {
    console.error('Error updating task status:', error);
  }
};

// 设置 Cookie 函数
const setCookie = (name, value, days) => {
  const d = new Date();
  d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000)); // 设置过期时间
  const expires = "expires=" + d.toUTCString();
  document.cookie = name + "=" + value + ";" + expires + ";path=/"; // 设置 Cookie
};

onMounted(async () => {
    fetchTimelines(); // 當組件掛載時取得時間軸
    if (selectedTask.value) {
        fetchComments(selectedTask.value);  // 如果有选中的任务，获取其留言
    }
    // 检查 task_id 是否存在并设置 task 到 Cookie
    if (getCookie("task_id")) {
      setCookie("task", "true", 30); // 设置 task = true 到 Cookie，有效期为30天
      console.log("task 已设置为 true");
    } else {
      console.log("没有找到 task_id");
    }
    // 直接使用taskIdFromCookie（现在从URL获取）
    if (taskIdFromCookie.value) {
      console.log("自动加载URL指定的任务:", taskIdFromCookie.value);
      await fetchTaskDetails(taskIdFromCookie.value);
      deadline_task_check.value = true;
    }
    //const taskIdFromCookie = getCookie("task_id");
    console.log("isPasted:",isPasted.value);
    //if (taskIdFromCookie && isPasted.value==true) {
    //  await fetchTaskDetails(taskIdFromCookie)
    //}
    getTaskIdFromURL();
});

const share_timeline = ref([
  "網頁設計-第七組",
  "畢業專題-第六組"
]);

// 打開分享面板
const openSharePanel = () => {
  isSharePanelOpen.value = true;
};


const getColor = (startDate, endDate) => {
  const now = new Date().getTime();
  const start = new Date(startDate).getTime(); // 確保轉換為時間戳記
  const end = new Date(endDate).getTime();
  
  if (isNaN(start) || isNaN(end) || start >= end) return "#D50000"; // 防止錯誤

  const remainingTime = end - now;
  const duration = end - start;
  const remainingRatio = Math.max(remainingTime / duration, 0);
  return getProgressColor(remainingRatio);
};

const getProgressColor = (remainingRatio) => {
  remainingRatio = Math.min(Math.max(remainingRatio, 0), 1); // 限制範圍在 0 ~ 1
  const red = Math.round(255 * (1 - remainingRatio));
  const green = Math.round(200 * remainingRatio);
  return `rgb(${red}, ${green}, 0)`;
};


const calculateProgress = (startDate, endDate) => {
  const start = new Date(startDate).getTime();
  const end = new Date(endDate).getTime();
  const now = new Date().getTime();
  const totalDuration = end - start;
  const elapsedTime = now - start;
  const progress = (elapsedTime / totalDuration) * 100;
  return Math.min(Math.max(progress, 0), 100).toFixed(2);
};

const openAddTimelinePanel = () => { 
  newTimeline.value = { name: "", endDate: "", remark: "" }; // 清空輸入框
  isAddingTimeline.value = true; 
};
const closeAddTimelinePanel = () => { isAddingTimeline.value = false; };

//新增專案
const addTimeline = async () => {
  if (!newTimeline.value.name || !newTimeline.value.startDate || !newTimeline.value.endDate) {
    alert("請輸入完整資訊（名稱、開始時間和結束時間）");
    return;
  }

  try {
    const userId = $cookies.get('user_id'); // 从cookie获取用户ID
    
    const newTimelineData = {
      name: newTimeline.value.name,
      startDate: newTimeline.value.startDate,
      endDate: newTimeline.value.endDate,
      progress: calculateProgress(newTimeline.value.startDate, newTimeline.value.endDate),
      color: getColor(
        new Date(newTimeline.value.startDate).getTime(),
        new Date(newTimeline.value.endDate).getTime()
      ),
      tasks: [],
      remark: newTimeline.value.remark,
      user_id: userId // 新增：明确传递user_id
    };

    const response = await axios.post(
      "http://localhost:5000/timelines", 
      newTimelineData,
      {
        withCredentials: true // 仍然保持cookie传递
      }
    );

    if (response.status === 201) {
      timelines.value.push(response.data);
      closeAddTimelinePanel();
    } else {
      alert("新增專案失敗，請稍後再試");
    }
  } catch (error) {
    console.error("新增專案時發生錯誤:", error);
    alert(`新增失敗: ${error.response?.data?.error || "伺服器錯誤"}`);
  }
};



const selectTimeline = (timeline) => {
  selectedTimeline.value = timeline;
  fetchTasks(timeline.id);  // 根據選擇的專案 ID 獲取任務
  selectedTask.value = null;

  // 打印選擇的時間軸的欄位
  console.log("Selected Timeline:", selectedTimeline.value);
  console.log("ID:", selectedTimeline.value.id);
  console.log("Name:", selectedTimeline.value.name);
  console.log("Start Date:", selectedTimeline.value.startDate);
  console.log("End Date:", selectedTimeline.value.endDate);
  console.log("Progress:", selectedTimeline.value.progress);
  console.log("Color:", selectedTimeline.value.color);
  console.log("Tasks:", selectedTimeline.value.tasks);
  console.log("Remark:", selectedTimeline.value.remark);
};


const closeDetailPanel = () => {
  selectedTimeline.value = null;
  selectedTask.value = null;
};

const openAddTaskPanel = () => { 
  isAddingTimeline.value = false;
  isAddingTask.value = true; };
const closeAddTaskPanel = () => { isAddingTask.value = false; };

//新增任務
const addTask = async () => {
  console.log("addTask method triggered");

  if (!newTask.value.name || !newTask.value.assignee || (!newTask.value.isWork && !newTask.value.endDate)) {
    alert("請填寫完整資訊");
    return;
  }

  if (!selectedTimeline.value) {
    console.error("selectedTimeline is undefined or null");
    return;
  }

  if (!selectedTimeline.value.id) {
    alert("时间轴ID未选择");
    return;
  }
    // 确保 tasks 数组已初始化
  if (!selectedTimeline.value.tasks) {
    console.warn("selectedTimeline.tasks is undefined, initializing...");
    selectedTimeline.value.tasks = [];
  }

  try {
    const userId = $cookies.get('user_id'); // 从cookie获取用户ID
    //const assistantStudentIds = assistantIds.value; // 直接使用你原本的學號數組
    const assistantStudentIds = Array.isArray(assistantIds.value) 
      ? assistantIds.value 
      : (assistantIds.value || '').toString().trim().split(/\s+/).filter(Boolean);
    const requestData = {
      name: newTask.value.name,
      completed: false,
      timeline_id: selectedTimeline.value.id,
      start_date: newTask.value.startDate,
      end_date: newTask.value.isWork ? null : newTask.value.endDate,
      task_remark: newTask.value.remark,
      isWork: newTask.value.isWork ? 1 : 0,
      user_id :userId,
      student_ids: assistantStudentIds // 傳遞學號數組到後端
    };
    console.log("Sending request with data:", requestData);

    const response = await axios.post("http://localhost:5000/tasks", requestData);
    const newTaskId = response.data.task_id;
    //await inviteAssistantsToTask(newTaskId);
    //const newTaskFromServer = {
    //  ...response.data,
    //  assistant: typeof response.data.assistant === 'string' 
    //    ? response.data.assistant.split(/\s+/) 
    //    : response.data.assistant
    //};
    const newTaskFromServer = response.data;
    
    selectedTimeline.value.tasks.push(newTaskFromServer);
    
    // 重置表单和状态
    newTask.value = {
      name: '',
      assignee: '',
      assistant: '',
      remark: '',
      startDate: '',
      endDate: '',
      isWork: false
    };
    
    isTask.value = true; // 关闭任务创建界面
    //isTaskDetail.value = true; 
    //selectedTask.value = newTaskFromServer;
    closeAddTaskPanel();
  } catch (error) {
    console.error("新增任务失败", error);
  }
};






const isRemarkVisible = ref(false);

// 進入編輯模式
const startEditingRemark = () => {
  if (!selectedTimeline.value) return alert("請先選擇時間軸");
  newRemark.value = selectedTimeline.value.remark || ""; // 預設為目前的備註
  isEditingRemark.value = true;
};

const isSaving = ref(false);
// 送出修改
const editRemark = async () => {
  if (!selectedTimeline.value) {
    alert("請先選擇時間軸");
    return;
  }

  console.log("選擇的時間軸：", selectedTimeline.value);  // 檢查 timeline_id 是否為 undefined
  if (!selectedTimeline.value.id) {
    alert("時間軸 ID 無效");
    return;
  }

  try {
    const timeline_id = selectedTimeline.value.id;  // 直接取得 ID
    const response = await axios.put(`http://localhost:5000/timelines/${timeline_id}/remark`, {
      remark: newRemark.value,
    });

    // 如果後端回傳成功，更新前端狀態並提示成功
    if (response.status === 200) {
      selectedTimeline.value.remark = newRemark.value;
      alert("備註修改成功！");

      // 修改成功後關閉編輯模式
      isEditingRemark.value = false;

      // 清空備註輸入框
      newRemark.value = "";
    }
  } catch (error) {
  }
};




// 監聽 Enter 鍵
const handleKeyPress = (event) => {
  if (event.key === "Enter") {
    editRemark();
  }
};


// 刪除專案
const deleteTimeline = async () => {
  if (!selectedTimeline.value) return;

  try {
    // 获取当前用户ID
    const user_id = $cookies.get('user_id'); 
    
    // 发送 DELETE 请求（携带 user_id）
    await axios.delete(
      `http://localhost:5000/timelines/${selectedTimeline.value.id}`,
      {
        data: { user_id },  // 通过请求体传递
        withCredentials: true  // 仍然保留cookie传递
      }
    );

    // 更新前端状态
    const index = timelines.value.findIndex(t => t.id === selectedTimeline.value.id);
    if (index !== -1) {
      timelines.value.splice(index, 1);
      selectedTimeline.value = null;
      selectedTask.value = null;
    }

    console.log("時間軸刪除成功");
  } catch (error) {
    console.error("刪除失敗:", {
      error: error.message,
      response: error.response?.data
    });
    alert(error.response?.data?.error || "刪除失敗");
  }
};

//新增留言
const addComment = async (task) => {
  console.log('留言内容：', newComment.value); // 调试输出留言内容

  // 确保每个任务都有一个 comments 数组
  if (!task.comments) {
    task.comments = []; // 如果没有 comments 数组，初始化为空数组
  }

  if (newComment.value.trim() !== '') {
    // 添加评论到本地评论数组
    task.comments.push({
      author: '當前用戶', // 假设当前用户为 '當前用戶'
      task_message: newComment.value,
    });

    // 向后端发送请求，存储评论到数据库
    try {
      const response = await fetch('http://localhost:5000/add-comment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_id: task.task_id,
          user_id: userId,
          task_message: newComment.value,
        }),
      });

      if (response.ok) {
        console.log('评论添加成功');
        newComment.value = ''; // 留言后清空输入框
      } else {
        console.error('评论添加失败');
      }
    } catch (error) {
      console.error('发送评论时发生错误:', error);
    }
  } else {
    alert('留言内容不能为空');
  }
};

//獲取留言
const fetchComments = async (task) => {
  if (!task || !task.task_id) {
    console.error('Invalid task or task_id');
    return;
  }
  
  console.log('Fetching comments for task_id:', task.task_id);

  // 先初始化 comments 避免異常時 Vue 無法反應
  task.comments = [];

  try {
    const response = await fetch(`http://localhost:5000/tasks/${task.task_id}/comments`);

    if (!response.ok) {
      console.warn(`HTTP error! Status: ${response.status}`);
      return;
    }

    const comments = await response.json();
    console.log('Fetched comments from backend:', comments);

    if (Array.isArray(comments)) {
      // 如果 task 來自 selectedTask.value，要確保 Vue 監測到變化
      task.comments = [...comments];  
    } else {
      console.warn('Received data is not an array, initializing empty comments.');
    }
  } catch (error) {
    console.error('Error fetching comments:', error);
  }
};

// 清除 selectedTask 並刪除 Cookie
const clearSelectedTask = () => {
  selectedTask.value = null;
  document.cookie = "task_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/";
};


const selectTask = async (task) => {
  console.log('选中的任务:', task);  // 确保选中的任务正确
  selectedTask.value = task;  // 设置当前选中的任务

  // 确保每个任务都有一个 comments 数组
  if (!selectedTask.value.comments) {
    selectedTask.value.comments = []; // 如果没有评论，初始化为空数组
  }

  // 获取该任务的评论
  console.log('开始获取留言...');
  await fetchComments(selectedTask.value);  // 取得留言
};

// 處理查看詳情按鈕點擊

const handleClick = (task) => {
  selectedTask.value = task; // 設定選中的任務
  
  selectTask(task); // 載入留言

  // 存入 Cookie
  document.cookie = `task_id=${task.task_id}; path=/; max-age=3600`;

  // 重置上傳狀態
  uploadStatus.value = {};

  // 載入該任務上傳的檔案
  fetchTaskFiles(task.task_id);
};


//從php獲取cookie
//fetch("http://127.0.0.1/get_user.php")
//  .then(response => response.json())
//  .then(data => {
//    if (data.user_id) {
//      document.cookie = `user_id=${data.user_id}; path=/;`;
//    }
//  });


// 删除任務
const deleteTask = async (taskId) => {
  const isConfirmed = window.confirm('確定要刪除這個任務嗎？');
  if (!isConfirmed) return;

  try {
    // 发送 DELETE 请求到后端
    await axios.delete(`http://localhost:5000/tasks/${taskId}`);
    
    // 从当前时间轴的任务列表中移除
    if (selectedTimeline.value?.tasks) {
      selectedTimeline.value.tasks = selectedTimeline.value.tasks.filter(
        task => task.task_id !== taskId
      );
    }
    
    // 关闭当前显示的任务详情画面
    selectedTask.value = null;
    
    alert('任務刪除成功');
  } catch (error) {
    console.error('刪除任務失敗:', error);
    alert('刪除任務失敗');
  }
};

//調整body
const toggleBodyClass = () => {
  if (document.body.classList.contains('dark-mode')) {
    document.body.classList.remove('dark-mode');
  } else {
    document.body.classList.add('dark-mode');
  }
};

//格式化時間
const formatDate = (dateString) => {
  if (!dateString) {
    return "";
  }
  const date = new Date(dateString);
  return date.toLocaleString("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
};

//從URL獲取task_id
const getTaskIdFromURL = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const taskId = urlParams.get('task_id');
  
  if (taskId) {
    console.log("从URL获取到任务ID:", taskId);
    return taskId;
  }
  console.log("URL中没有task_id参数");
  return null;
};

// 上傳檔案功能
const ALLOWED_EXTENSIONS = new Set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx']);
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// 上傳狀態追蹤
const uploadStatus = ref({});
const fileInputs = ref({});

const setFileInputRef = (el, taskId) => {
  if (el) {
    fileInputs.value[taskId] = el;
  } else if (fileInputs.value[taskId]) {
    delete fileInputs.value[taskId];
  }
};

const triggerFileInput = (taskId) => {
  const input = fileInputs.value[taskId];
  if (input?.click) {
    // 重置上傳狀態
    uploadStatus.value[taskId] = {
      progress: 0,
      message: '',
      class: ''
    };
    input.click();
  }
};

const handleFileChange = async (event, taskId) => {
  const file = event.target.files[0];
  if (!file) return;

  // 檢查檔案類型
  const fileExt = file.name.split('.').pop().toLowerCase();
  if (!ALLOWED_EXTENSIONS.has(fileExt)) {
    uploadStatus.value[taskId] = {
      progress: 0,
      message: `不支援的檔案類型: .${fileExt}`,
      class: 'error'
    };
    event.target.value = '';
    return;
  }

  // 檢查檔案大小
  if (file.size > MAX_FILE_SIZE) {
    uploadStatus.value[taskId] = {
      progress: 0,
      message: `檔案大小超過限制 (最大 ${MAX_FILE_SIZE / 1024 / 1024}MB)`,
      class: 'error'
    };
    event.target.value = '';
    return;
  }

  uploadStatus.value[taskId] = {
    progress: 0,
    message: '正在上傳...',
    class: 'uploading'
  };
  const userId = $cookies.get('user_id'); // 確保 Cookie 名稱正確
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('taskId', taskId);
    formData.append('userId', userId);

    const response = await fetch('http://localhost:5000/upload', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || '上傳失敗');
    }

    const result = await response.json();

    uploadStatus.value[taskId] = {
      progress: 100,
      message: '上傳成功',
      class: 'success',
      file: result  // 儲存上傳成功的檔案資訊
    };

    // 更新任務的檔案列表
    if (selectedTask.value && selectedTask.value.task_id === taskId) {
      if (!selectedTask.value.files) selectedTask.value.files = [];
      selectedTask.value.files.push(result);
    }

    // 3秒後清除進度
    setTimeout(() => {
      if (uploadStatus.value[taskId]?.progress === 100) {
        delete uploadStatus.value[taskId];
      }
    }, 3000);

  } catch (error) {
    console.error('上傳失敗:', error);
    uploadStatus.value[taskId] = {
      progress: 0,
      message: `上傳失敗: ${error.message}`,
      class: 'error'
    };
  } finally {
    event.target.value = '';
  }
};

// 格式化檔案大小顯示
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

//獲取檔案
const fetchTaskFiles = async (taskId) => {
  try {
    const response = await axios.get(`http://localhost:5000/tasks/${taskId}/files`);
    const files = response.data.files;

    // 找到該任務並塞入 files 資料
    const task = selectedTimeline.value.tasks.find(t => t.task_id === taskId);
    if (task) {
      task.files = files;
    }

    // 如果這是目前選中的任務，也一併更新
    if (selectedTask.value && selectedTask.value.task_id === taskId) {
      selectedTask.value.files = files;
    }

    console.log("獲取檔案成功", files);
  } catch (error) {
    console.error("獲取檔案失敗:", error);
  }
};

//邀請人員
const inputStudentId = ref('')
const searchResult = ref(null)
const searchError = ref('')
const searchStudent = async () => {
  searchResult.value = null
  searchError.value = ''

  try {
    const res = await fetch('http://127.0.0.1:5000/search_user_by_student_id', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ student_id: inputStudentId.value })
    })

    const data = await res.json()

    if (!res.ok) {
      searchError.value = data.error || '查詢失敗'
    } else {
      searchResult.value = data
    }
  } catch (err) {
    searchError.value = '請求錯誤，請稍後再試'
    console.error(err)
  }
}

const confirmShare = () => {
  if (searchResult.value) {
    // ✅ 這裡可以加進 timeline 或送出邀請
    console.log('準備邀請使用者：', searchResult.value)
  } else {
    alert('請先查詢使用者')
  }
  inviteUser(selectedTimeline.value.id, inputStudentId);

}

const inviteUser = async () => {
  const response = await fetch('http://127.0.0.1:5000/invite_user_to_timeline', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      timeline_id: selectedTimeline.value.id,  // 已選擇的時間軸 ID
      user_id: searchResult.value.id          // 被邀請的使用者 ID
    })
  });
  
  const result = await response.json();
  
  if (response.ok) {
    // 邀請成功
    alert(result.message);
  } else {
    // 顯示錯誤訊息
    alert(result.error);
  }
};

// 任務相關人員
const assistantInput = ref('')                  // 使用者輸入的字串（學號）
const assistantSuggestions = ref([])            // 從後端搜尋到的建議清單
const assistantIds = ref([])                    // 已選取的多位學號（之後送給後端用）

// 當 assistantInput 改變時，自動查詢建議姓名
watch(assistantInput, async (newVal) => {
  if (newVal.trim() === '') {
    assistantSuggestions.value = []
    return
  }
  try {
    const res = await fetch('http://127.0.0.1:5000/search_user_by_student_id_task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword: newVal })
    })
    const data = await res.json()
    assistantSuggestions.value = data.users || []
  } catch (err) {
    console.error('搜尋失敗：', err)
  }
})

// 選擇某筆建議後加到已選清單中
const addAssistant = (studentId) => {
  if (!assistantIds.value.includes(studentId)) {
    assistantIds.value.push(studentId)
  }
  assistantInput.value = ''  // 清空輸入框
  assistantSuggestions.value = []  // 關閉建議清單
}

// 刪除已選的
const removeAssistant = (id) => {
  assistantIds.value = assistantIds.value.filter(sid => sid !== id)
}

// 邀請相關人員到任務
const inviteAssistantsToTask = async (taskId) => {
  try {
    await fetch('http://127.0.0.1:5000/invite_assistants_to_task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        task_id: taskId,
        student_ids: assistantIds.value  // 使用 assistantIds 來傳送選擇的學號
      })
    })
    console.log('相關人員已成功邀請！')
  } catch (err) {
    console.error('邀請失敗：', err)
  }
}
</script>

<style>
#app {
  width:100%;
  margin: 0 auto;
}
@media (min-width: 0px) {
    #app {
      display: flow;
        max-width:100vw;
        padding: 0;
    }
}
body {
        display: flex; /* 修改 body 的 display 屬性 */
        flex-direction: column;
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
}
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #f4f4f4;
            padding: 10px 20px;
        }
        .header img {
            width: 200px;
            margin-top: 10px;
            cursor: pointer;
        }
        .header div img {
            width: 40px;
            height: 40px;
            margin-left: 10px;
        }
body.dark-mode {
  background-color: black;
  color: white;
}
.container {
  height:100%;
  display: flex;
  flex-grow: 1;
}

@media (max-width: 1028px) {
  .container {
    height:100%;
    width: 100%;  
    margin-top: 0; 
    padding-top: 20px; 
  }
}
/*
.task-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 10px;
  border: 2px solid black;
  border-radius: 5px;
  padding: 10px; 
}*/

.task-container {
  display: flex;
  min_width: 60%;
  flex-wrap: wrap;
  justify-content: center;
  align-content: flex-start;
  gap: 10px;
  margin-top: 10px;
  border: 2px solid black;
  border-radius: 5px;
  padding: 10px;
  min-height: 100px;
  /* 新增以下属性 */
  max-height: 500px; /* 设置最大高度 */
  overflow-y: auto; /* 启用垂直滚动 */
}

.task-container:empty {
  border: none;
  padding: 0;
}

.task-box {
  flex: 0 0 auto;
  min_width: 180px;
  background: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: 0.3s;
  min-height: 100px;
  box-sizing: border-box;
  /* 确保内容不会撑开盒子 */
  overflow: hidden;
  width: auto; 
  min-width: 180px;
  max-width: none;
  height: auto;
}

/* 响应式调整 
@media (max-width: 1200px) {
  .task-box {
    flex: 0 0 calc(33.333% - 10px); 
  }
}

@media (max-width: 768px) {
  .task-box {
    flex: 0 0 calc(50% - 10px); 
  }
}

@media (max-width: 480px) {
  .task-box {
    flex: 0 0 100%; 
  }
}*/
/*
.task-box {
  display:flex;
  background: #f9f9f9;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: 0.3s;
  min-height: 100px; 
  
}*/

.task-box:hover {
  transform: translateY(-2px);
}

.task-info {
  position: relative;  /* 为绝对定位子元素提供基准 */
  width: 30vw;
  max-width: 300px;
  min-width: 25 0px;    /* 设置最小宽度 */
  background: white;
  border-radius: 8px;
  padding: 5px;       /* 增加内边距 */
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.15); /* 更强的阴影 */
  margin: 10px 0;      /* 增加外边距 */
  z-index: 10;         /* 确保显示层级 */
  
  /* 可选：添加最大宽度限制 */
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

/* 彈出面板的過渡動畫 */
.detail-panel-enter-active, .detail-panel-leave-active {
  transition: transform 0.3s ease-in-out;
}

.detail-panel-enter, .detail-panel-leave-to /* .detail-panel-leave-active in <2.1.8 */ {
  transform: translateY(100%);
}

@media (max-width: 768px) {
  .detail-panel {
    /* 在小螢幕上將面板寬度調小 */
    max-width: 90%;
    margin-top: 20px;
  }
  
  .task-info, label, select, button {
    margin-bottom: 10px;
  }
}

.share-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
  width: 250px;
  text-align: center;
  z-index:999;
}

.share-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.completed {
  color: green;
}


.delete-btn {
  background: #ff4d4d;
  color: white;
  border: none;
  padding: 5px 10px;
  margin-left: 5px;
  cursor: pointer;
  border-radius: 5px;
  transition: 0.3s;
}

.delete-btn:hover {
  background: #cc0000;
}


button {
  
  padding: 8px 16px;
  margin: 10px;
  background-color: #8cd872;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  transition: 0.3s;
  white-space: nowrap;
  
}

button:hover {
  background-color: #6aa84f; /* 深綠色 */
}

/* 專案 */
.timeline-list {
  width:80%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;

}

.timeline-item {
  display: flex;
  align-items: center;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
  padding: 15px;
  cursor: pointer;
  transition: 0.3s;
}

.timeline-item:hover {
  transform: translateY(-2px);
}

/* 甘特圖樣式 */
.timeline-bar-container {
  flex: 3;
  height: 15px;
  background: #ddd;
  border-radius: 8px;
  overflow: hidden;
  margin: 0 10px;
}

.timeline-bar {
  height: 100%;
  transition: width 0.5s ease-in-out;
}

@media (max-width: 380px) {
  .timeline-bar-container {
    display: none;
  }
}
/*
.detail-panel {
  position: fixed;
  right: 0;
  top: 0;
  width: 40%;
  height: 100%;
  background: white;
  box-shadow: -3px 0 10px rgba(0, 0, 0, 0.2);
  padding: 20px;
  overflow-y: auto;
}
*/

.detail-panel {
  position: fixed;
  left: 50%;
  top: 50%;
  width: 80%; /* 加宽面板（原50%） */
  max-width: 600px; /* 新增最大宽度限制 */
  min-width: 300px; /* 新增最小宽度保证可读性 */
  transform: translate(-50%, -50%);
  max-height: 80%;
  background: white;
  border: none;
  outline: 1px solid #e0e0e0;
  outline-offset: 3px;
  border-radius: 12px; 
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); 
  padding: 20px;
  overflow-y: auto;
  z-index: 1000;
  
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.detail-panel-remark {
  position: flex; 
  background: white;
  overflow-y: auto;
  border: 2px solid black;
  padding: 5px; 
  border-radius: 5px; 
  width: 100%; 
}


@media (max-width: 680px) {
  .detail-panel {
    position: fixed;
    left: 50%;
    top: 0;
    transform: translateX(-50%);
    width: 90%; 
  }
}
/*
.slide-enter-active, .slide-leave-active {
  transition: transform 0.3s ease-in-out;
}*/

.slide-enter {
  transform: translateX(100%);
}

.slide-leave-to {
  transform: translateX(80%);
}

.comments-section {
  border: 2px solid #ddd; /* 邊框 */
  border-radius: 10px; /* 圓角 */
  padding: 15px;
  background-color: #f9f9f9; /* 背景顏色 */
  max-width: 500px; /* 最大寬度 */
  margin: 20px auto; /* 置中 */
  box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1); /* 陰影 */
}

.comment {
  border-bottom: 1px solid #ccc;
  padding: 8px 0;
}

.comment:last-child {
  border-bottom: none; /* 最後一個留言不加底線 */
}

.comments-section input[type="text"] {
  width: calc(100% - 20px);
  padding: 8px;
  margin-top: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

input[type="text"] {
  width: calc(20% - 20px);
  min-width: 200px; 
  padding: 4px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

h3 {
  font-weight: bold !important;
}

.main-content { /* 新增 main-content 樣式 */
  display: flex;
  flex-grow: 1;
}
.sidebar {
  width: 150px;
  background-color: #ffffff;
  padding: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 2px solid #ddd;
}
.sidebar button {
    width: 100%;
    max-width:126px;
    margin: 5px ;
    padding: 10px;
    cursor: pointer;
    border: 2px solid #000;
    border-radius: 10px;
    background-color: #fff;
    font-size: 16px;
    font-weight: bold;
    color:black;
}
.sidebar button.active {
    background-color: #d6f5d6;
}
*,
*::before,
*::after {
  box-sizing: content-box; /* 這樣就取消了 border-box 的效果 */
}
.content {
  height:100%;
  flex-grow: 1;
  padding: 20px;
  display: flex;
  flex-wrap: wrap; /* 允許元素換行 */
  gap: 10px; /* 元素之間的間距 */
}

.no-tasks-message {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 16px;
  background: #f9f9f9;
  border-radius: 8px;
  margin: 10px 0;
}

/*將要到期任務面板*/
/* 基于您现有CSS的补充样式 */
.deadline_task-box {
  position: fixed;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  max-width: 600px;
  min-width: 300px;
  max-height: 80vh;
  background: white;
  border: 2px solid black;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  z-index: 100;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #f4f4f4;
  border-bottom: 2px solid black;
}

.task-header h3 {
  margin: 0;
  font-weight: bold;
}

.task-content {
  padding: 20px;
  overflow-y: auto;
}

.task-field {
  display: flex;
  margin-bottom: 12px;
  line-height: 1.5;
}

.field-label {
  font-weight: 600;
  color: #555;
  min-width: 90px;
  margin-right: 10px;
}

.field-value {
  color: #333;
  flex-grow: 1;
  word-break: break-word;
}

/* 状态样式 */
.loading-state, 
.error-state, 
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 0;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #8cd872;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon, .empty-icon {
  font-size: 2rem;
  margin-bottom: 15px;
}

.error-state p, 
.empty-state p {
  color: #666;
  margin-bottom: 15px;
}

.no-comments {
  text-align: center;
  color: #888;
  padding: 15px 0;
}

/* 留言区样式 - 使用您现有的comments-section样式 */
.comments-section {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #ddd;
}

.comment-field {
  display: flex;
  margin-bottom: 6px;
  font-size: 0.95rem;
}

.comment .field-label {
  min-width: 50px;
  font-size: 0.9rem;
}

.comment .field-value {
  color: #666;
}

/* 响应式调整 
@media (max-width: 680px) {
  .deadline_task-box {
    width: 90%;
    top: 20px;
    transform: translateX(-50%);
  }
  
  .task-field {
    flex-direction: column;
  }
  
  .field-label {
    margin-bottom: 4px;
  min-width: auto;
  }
}*/

.upload-status {
  margin-top: 8px;
  padding: 4px;
  border-radius: 4px;
}

.upload-status .uploading {
  color: #ff9800;
}

.upload-status .success {
  color: #4caf50;
}

.upload-status .error {
  color: #f44336;
}

progress {
  width: 100%;
  height: 6px;
  margin-top: 4px;
}

.file-list ul {
  list-style-type: none;
  padding: 0;
}

.file-list li {
  padding: 4px 0;
  border-bottom: 1px solid #eee;
}

.file-list a {
  color: #2196f3;
  text-decoration: none;
}

.file-list a:hover {
  text-decoration: underline;
}

.student-input {
  width: 100%;
  padding: 6px;
  margin-bottom: 10px;
}

.result-box {
  background: #f0f8ff;
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 10px;
}
</style>