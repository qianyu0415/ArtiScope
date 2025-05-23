<template>
  <div class="chat-container">
    <!-- 聊天消息区域 -->
    <div class="messages-container" ref="messagesContainer">
      <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
        <div :class="['message', message.role === 'user' ? 'message-user' : 'message-assistant']">
          <div class="message-avatar">
            <el-avatar :size="36" :icon="message.role === 'user' ? 'User' : 'ChatRound'" />
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.content)"></div>
            <!-- 显示附件信息 -->
            <div v-if="message.files && message.files.length > 0" class="message-files">
              <div 
                v-for="(file, fileIndex) in message.files" 
                :key="fileIndex" 
                class="file-item"
                @click="downloadFile(file)"
              >
                <el-tag size="small" type="info" class="file-tag">
                  <el-icon class="file-icon"><Document /></el-icon>
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                  <el-icon class="download-icon"><Download /></el-icon>
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="isTyping" class="message-wrapper">
        <div class="message message-assistant">
          <div class="message-avatar">
            <el-avatar :size="36" :icon="'ChatRound'" />
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="fixed-bottom-container" :style="{'--sidebar-width': sidebar.collapse ? '65px' : '250px'}">
      <div class="input-container">
        <el-input v-model="inputText">
          <template #prepend>
            <el-button type="primary" plain @click="triggerFileInput">
              {{ selectedFiles.length > 0 ? `已选择 ${selectedFiles.length} 个文件` : '引用附件' }}
              <input 
                ref="fileInput"
                type="file" 
                style="display: none;" 
                @change="handleFileUpload"
                multiple
              >
            </el-button>
          </template>
          <template #default>
            <el-input
              type="textarea"
              ref="textareaRef"
              :autosize="{ minRows: 1, maxRows: 8 }"
              placeholder="请描述想要生成的图片或与大模型对话"
              @input="adjustTextareaHeight"
              @keydown.enter.ctrl="handleSend"
            />
          </template>
          <template #append>
            <el-button 
              type="primary" 
              icon="ChatRound" 
              style="height: 100%;"
              @click="handleSend"
            ></el-button>
          </template>
        </el-input>
        <!-- 文件预览区域 -->
        <div v-if="selectedFiles.length > 0" class="files-preview">
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-preview-item">
            <el-icon><Document /></el-icon>
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ formatFileSize(file.size) }}</span>
            <el-icon @click="removeFile(index)" class="remove-icon"><Close /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="text-to-image">
import { ref, nextTick, onMounted } from 'vue';
import { Close, Document, User, Download } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSidebarStore } from '../../store/sidebar';

const fileInput = ref(null);
const inputText = ref('');
const selectedFiles = ref([]);
const textareaRef = ref(null);
const messagesContainer = ref(null);
const isTyping = ref(false);
const sidebar = useSidebarStore();

// 聊天消息数组
const messages = ref([
  {
    role: 'assistant',
    content: '你好！我是AI助手，很高兴为你提供帮助，请你描述想生成的图片或与我对话。'
  }
]);

// 预设的AI回复
const aiResponses = [
  "我已收到你的消息，正在思考如何回答...",
  "这是个很好的问题！根据我的理解，这个问题可以从几个方面来看...",
  "谢谢你的提问。让我为你详细解答这个问题。",
  "很高兴收到你的消息。基于你提供的信息，我认为...",
  "我理解你的需求。让我给你提供一些相关的建议和解决方案。",
  "这是一个复杂的问题，让我尝试从不同角度为你解析。"
];

// 模拟AI可能返回的附件
const mockAiFiles = [
  { name: '分析报告.pdf', size: 1024000, type: 'application/pdf' },
  { name: '数据统计.xlsx', size: 512000, type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' },
  { name: '示例代码.txt', size: 8192, type: 'text/plain' },
  { name: '设计图.png', size: 2048000, type: 'image/png' },
  { name: '参考文档.docx', size: 756000, type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' }
];

const triggerFileInput = () => {
  fileInput.value.click();
};

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files);
  const newFiles = files.map(file => ({
    name: file.name,
    size: file.size,
    type: file.type,
    file: file // 保存原始文件对象用于下载
  }));
  selectedFiles.value.push(...newFiles);
};

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1);
  if (selectedFiles.value.length === 0) {
    fileInput.value.value = '';
  }
};

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 下载文件函数
const downloadFile = (fileInfo) => {
  try {
    let blob;
    let url;
    
    if (fileInfo.file) {
      // 用户上传的文件，直接使用原始文件
      blob = fileInfo.file;
      url = URL.createObjectURL(blob);
    } else {
      // AI返回的模拟文件，创建一个示例文件
      const content = generateMockFileContent(fileInfo);
      blob = new Blob([content], { type: fileInfo.type || 'application/octet-stream' });
      url = URL.createObjectURL(blob);
    }
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = url;
    link.download = fileInfo.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // 清理URL对象
    URL.revokeObjectURL(url);
    
    ElMessage.success(`文件 "${fileInfo.name}" 下载成功！`);
  } catch (error) {
    console.error('文件下载失败:', error);
    ElMessage.error('文件下载失败，请重试！');
  }
};

// 生成模拟文件内容
const generateMockFileContent = (fileInfo) => {
  const fileName = fileInfo.name.toLowerCase();
  
  if (fileName.includes('.txt') || fileName.includes('.md')) {
    return `这是AI生成的文本文件：${fileInfo.name}\n\n内容示例:\n- 这是第一行内容\n- 这是第二行内容\n- 文件大小: ${formatFileSize(fileInfo.size)}\n- 生成时间: ${new Date().toLocaleString()}`;
  } else if (fileName.includes('.json')) {
    return JSON.stringify({
      fileName: fileInfo.name,
      generatedBy: 'AI Assistant',
      timestamp: new Date().toISOString(),
      data: {
        message: '这是AI生成的JSON文件',
        size: fileInfo.size
      }
    }, null, 2);
  } else if (fileName.includes('.csv')) {
    return `文件名,大小,类型,生成时间\n${fileInfo.name},${fileInfo.size},${fileInfo.type},${new Date().toLocaleString()}\n示例数据1,100,文本,2024-01-01\n示例数据2,200,图片,2024-01-02`;
  } else {
    return `AI生成的文件: ${fileInfo.name}\n大小: ${formatFileSize(fileInfo.size)}\n类型: ${fileInfo.type}\n生成时间: ${new Date().toLocaleString()}`;
  }
};

const handleSend = () => {
  if (inputText.value.trim() || selectedFiles.value.length > 0) {
    // 添加用户消息
    const userMessage = {
      role: 'user',
      content: inputText.value.trim(),
      files: selectedFiles.value.length > 0 ? [...selectedFiles.value] : null
    };
    messages.value.push(userMessage);
    
    // 保存用户消息内容用于AI回复逻辑
    const userMessageText = inputText.value;
    const hasUserFiles = selectedFiles.value.length > 0;
    
    // 清空输入框
    inputText.value = '';
    selectedFiles.value = [];
    if (fileInput.value) fileInput.value.value = '';
    
    // 重置输入框高度
    nextTick(() => {
      adjustTextareaHeight();
      scrollToBottom();
    });

    // 模拟AI正在输入
    isTyping.value = true;
    
    // 模拟AI回复延迟
    setTimeout(() => {
      isTyping.value = false;
      
      // 生成AI回复
      let aiReply = aiResponses[Math.floor(Math.random() * aiResponses.length)];
      let aiFiles = null;
      
      // 根据用户消息内容决定是否返回附件
      if (hasUserFiles) {
        aiReply += " 我已收到您的附件，经过分析后，为您生成了相关的报告文件。";
        // 随机返回1-2个附件
        const fileCount = Math.floor(Math.random() * 2) + 1;
        aiFiles = mockAiFiles.slice(0, fileCount).map(file => ({
          ...file,
          // 添加时间戳使文件名唯一
          name: file.name.replace('.', `_${Date.now()}.`)
        }));
      } else if (userMessageText.includes('文件') || userMessageText.includes('附件') || userMessageText.includes('下载')) {
        aiReply += " 根据您的需求，我为您准备了相关的文档和资料。";
        aiFiles = [mockAiFiles[Math.floor(Math.random() * mockAiFiles.length)]];
        aiFiles[0].name = aiFiles[0].name.replace('.', `_${Date.now()}.`);
      } else if (Math.random() < 0.3) {
        // 30%的概率随机返回附件
        aiReply += " 另外，我还为您准备了一份相关资料供参考。";
        aiFiles = [mockAiFiles[Math.floor(Math.random() * mockAiFiles.length)]];
        aiFiles[0].name = aiFiles[0].name.replace('.', `_${Date.now()}.`);
      }
      
      messages.value.push({
        role: 'assistant',
        content: aiReply,
        files: aiFiles
      });
      
      nextTick(() => {
        scrollToBottom();
      });
    }, 1500);
  }
};

const adjustTextareaHeight = () => {
  nextTick(() => {
    if (textareaRef.value?.$el) {
      const textarea = textareaRef.value.$el.querySelector('textarea');
      if (textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
      }
    }
  });
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

// 格式化消息文本，处理换行符
const formatMessage = (text) => {
  if (!text) return '';
  return text.replace(/\n/g, '<br>');
};

onMounted(() => {
  // 初始化时也执行一次高度调整
  adjustTextareaHeight();
  scrollToBottom();
});
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  background-color: #f5f7fa;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 35px 100px;
  margin-bottom: 80px;
}

.message-wrapper {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.message {
  display: flex;
  max-width: 80%;
  padding: 10px;
  border-radius: 8px;
}

.message-user {
  align-self: flex-end;
  background-color: #e6f7ff;
  margin-left: auto;
}

.message-assistant {
  align-self: flex-start;
  background-color: #ffffff;
  margin-right: auto;
}

.message-avatar {
  margin-right: 10px;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-text {
  word-break: break-word;
  line-height: 1.5;
}

.message-files {
  margin-top: 8px;
}

.file-item {
  margin-bottom: 4px;
  cursor: pointer;
  display: inline-block;
}

.file-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  user-select: none;
}

.file-tag:hover {
  background-color: #e6f4ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.file-icon {
  font-size: 14px;
}

.file-name {
  font-weight: 500;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12px;
  color: #666;
  margin-left: 4px;
}

.download-icon {
  font-size: 12px;
  color: #1890ff;
  margin-left: 4px;
}

.typing-indicator {
  display: flex;
  align-items: center;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  margin: 0 2px;
  background-color: #9e9ea1;
  border-radius: 50%;
  display: inline-block;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0% {
    transform: scale(1);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.5);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0.7;
  }
}

.fixed-bottom-container {
  position: fixed;
  bottom: 0;
  left: var(--sidebar-width, 250px);
  right: 0;
  padding: 15px 35px;
  background-color: #fff;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transition: left 0.48s ease;
}

.input-container {
  max-width: 100%;
  margin: 0 auto;
  position: relative;
}

.files-preview {
  margin-top: 8px;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}

.file-preview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  margin-bottom: 4px;
  background-color: #fff;
  border-radius: 4px;
  font-size: 12px;
}

.file-preview-item:last-child {
  margin-bottom: 0;
}

.file-preview-item .file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.file-preview-item .file-size {
  color: #666;
  font-size: 11px;
}

.file-preview-item .remove-icon {
  cursor: pointer;
  color: #f56c6c;
  font-size: 14px;
  padding: 2px;
  border-radius: 2px;
  transition: all 0.2s;
}

.file-preview-item .remove-icon:hover {
  background-color: #fef0f0;
  color: #f78989;
}
</style>