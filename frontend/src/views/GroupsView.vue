<template>
  <div class="h-full w-full bg-linear-to-br from-purple-50 to-pink-100 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-8 pb-4 px-4 animate-slideDown">
      <span class="text-6xl mb-4 block animate-pulse-custom">💬</span>
      <h1 class="text-4xl font-bold mb-2 text-gray-800">群組訊息</h1>
      <p class="text-lg text-gray-600">與團隊即時交流互動</p>
    </div>
    
    <!-- Action Bar -->
    <div class="flex justify-center gap-4 px-4 mb-6">
      <button 
        @click="showCreateGroup = true"
        class="px-6 py-3 bg-linear-to-r from-primary to-primary-light text-white font-semibold rounded-full shadow-lg hover:-translate-y-0.5 hover:shadow-xl transition-all flex items-center gap-2"
      >
        <span>➕</span>
        <span>建立群組</span>
      </button>
      <button 
        @click="showJoinGroup = true"
        class="px-6 py-3 bg-green-500 text-white font-semibold rounded-full shadow-lg hover:-translate-y-0.5 hover:shadow-xl transition-all flex items-center gap-2"
      >
        <span>🔗</span>
        <span>加入群組</span>
      </button>
    </div>
    
    <!-- Create Group Modal -->
    <div v-if="showCreateGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showCreateGroup = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-slideUp">
        <h3 class="text-xl font-semibold text-primary mb-6">建立新群組</h3>
        <div class="relative mb-6">
          <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">💬</span>
          <input 
            v-model="newGroupName"
            type="text" 
            placeholder="請輸入群組名稱"
            class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
          />
        </div>
        <div class="flex gap-3">
          <button 
            @click="showCreateGroup = false"
            class="flex-1 px-4 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all"
          >
            取消
          </button>
          <button 
            @click="handleCreateGroup"
            class="flex-1 px-4 py-3 font-bold text-lg rounded-xl border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center justify-center gap-2"
            style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
          >
            <span>✓</span>
            建立
          </button>
        </div>
      </div>
    </div>
    
    <!-- Join Group Modal -->
    <div v-if="showJoinGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showJoinGroup = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-slideUp">
        <h3 class="text-xl font-semibold text-primary mb-6">加入群組</h3>
        <div class="relative mb-6">
          <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔑</span>
          <input 
            v-model="inviteCode"
            type="text" 
            placeholder="請輸入六位數邀請碼"
            maxlength="6"
            class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
          />
        </div>
        <div class="flex gap-3">
          <button 
            @click="showJoinGroup = false"
            class="flex-1 px-4 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all"
          >
            取消
          </button>
          <button 
            @click="handleJoinGroup"
            class="flex-1 px-4 py-3 font-bold text-lg rounded-xl border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center justify-center gap-2"
            style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
          >
            <span>✓</span>
            加入
          </button>
        </div>
      </div>
    </div>
    
    <!-- Group List -->
    <div class="pb-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="group in groups" 
          :key="group.group_id" 
          class="bg-white rounded-xl shadow-md hover:-translate-y-1 hover:shadow-xl transition-all animate-fadeIn"
        >
          <div class="p-6">
            <h3 class="text-xl font-semibold text-primary flex items-center gap-2 mb-4">
              <span>💬</span>
              {{ group.group_name }}
            </h3>
            
            <div class="space-y-3 text-gray-600 text-sm">
              <p class="flex items-center gap-2">
                <span>🔑</span>
                <strong>邀請碼：</strong>
                <span class="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full font-mono font-semibold">
                  {{ group.invite_code }}
                </span>
              </p>
              <p class="flex items-center gap-2 text-gray-400">
                <span>⏰</span>
                建立於 {{ formatDate(group.created_at) }}
              </p>
            </div>
            
            <div class="mt-4 pt-4 border-t flex gap-2">
              <button 
                @click="openChat(group)"
                class="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center gap-2"
              >
                <span>💬</span>
                開啟聊天
              </button>
              <button 
                @click="leaveGroup(group.group_id)"
                class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
              >
                <span>✕</span>
                離開
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="groups.length === 0" class="text-center py-16">
        <span class="text-6xl block mb-4">💬</span>
        <p class="text-xl text-gray-600">目前尚未加入任何群組</p>
      </div>
    </div>
    
    <!-- Chat Modal -->
    <div v-if="currentGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="currentGroup = null">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl h-[80vh] flex flex-col animate-slideUp">
        <div class="p-4 border-b flex justify-between items-center">
          <h3 class="text-xl font-semibold text-primary">{{ currentGroup?.group_name }}</h3>
          <button @click="currentGroup = null" class="text-gray-400 hover:text-gray-600 text-2xl">✕</button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-4 bg-gray-50" ref="messagesContainer">
          <div v-for="msg in messages" :key="msg.message_id" class="mb-4 p-3 bg-white rounded-lg border-l-4 border-primary">
            <div class="flex items-center gap-2 text-primary font-semibold text-sm mb-1">
              <span>👤</span>
              {{ msg.sender_name }}
            </div>
            <p class="text-gray-800 mb-1">{{ msg.content }}</p>
            <div class="text-xs text-gray-400 flex items-center gap-1">
              <span>⏰</span>
              {{ formatTime(msg.created_at) }}
            </div>
          </div>
          
          <div v-if="messages.length === 0" class="text-center py-8 text-gray-400">
            <span class="text-4xl block mb-2">💬</span>
            <p>目前沒有訊息</p>
          </div>
        </div>
        
        <div class="p-4 border-t">
          <div class="flex gap-2">
            <input 
              v-model="newMessage"
              type="text" 
              placeholder="輸入訊息..."
              @keyup.enter="sendMessage"
              class="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            />
            <button 
              @click="sendMessage"
              class="px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary-dark transition-colors"
            >
              📤
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import api from '../services/api';

const groups = ref([]);
const currentGroup = ref(null);
const messages = ref([]);
const newMessage = ref('');
const newGroupName = ref('');
const inviteCode = ref('');
const showCreateGroup = ref(false);
const showJoinGroup = ref(false);
const messagesContainer = ref(null);

const fetchGroups = async () => {
  try {
    const response = await api.get('/groups');
    groups.value = response.data;
  } catch (error) {
    console.error('取得群組失敗:', error);
  }
};

const handleCreateGroup = async () => {
  if (!newGroupName.value.trim()) {
    alert('請輸入群組名稱');
    return;
  }
  
  try {
    const response = await api.post('/groups', { group_name: newGroupName.value });
    alert(`群組建立成功！邀請碼: ${response.data.invite_code}`);
    await fetchGroups();
    showCreateGroup.value = false;
    newGroupName.value = '';
  } catch (error) {
    alert(error.response?.data?.error || '建立群組失敗');
  }
};

const handleJoinGroup = async () => {
  if (!inviteCode.value.trim()) {
    alert('請輸入邀請碼');
    return;
  }
  
  try {
    await api.post('/groups/join', { invite_code: inviteCode.value });
    alert('成功加入群組');
    await fetchGroups();
    showJoinGroup.value = false;
    inviteCode.value = '';
  } catch (error) {
    alert(error.response?.data?.error || '加入群組失敗');
  }
};

const openChat = async (group) => {
  currentGroup.value = group;
  await fetchMessages(group.group_id);
};

const fetchMessages = async (groupId) => {
  try {
    const response = await api.get(`/groups/${groupId}/messages`);
    messages.value = response.data;
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error('取得訊息失敗:', error);
  }
};

const sendMessage = async () => {
  if (!newMessage.value.trim()) return;
  
  try {
    await api.post(`/groups/${currentGroup.value.group_id}/messages`, {
      content: newMessage.value
    });
    newMessage.value = '';
    await fetchMessages(currentGroup.value.group_id);
  } catch (error) {
    alert(error.response?.data?.error || '發送訊息失敗');
  }
};

const leaveGroup = async (groupId) => {
  if (!confirm('確定要離開此群組？')) return;
  
  try {
    await api.post(`/groups/${groupId}/leave`);
    alert('已離開群組');
    await fetchGroups();
    if (currentGroup.value?.group_id === groupId) {
      currentGroup.value = null;
    }
  } catch (error) {
    alert(error.response?.data?.error || '離開群組失敗');
  }
};

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

const formatTime = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString('zh-TW');
};

onMounted(() => {
  fetchGroups();
});
</script>
