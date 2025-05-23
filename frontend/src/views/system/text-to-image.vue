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
            <!-- 显示生成的图像 -->
            <div v-if="message.imageUrl" class="message-image">
              <img :src="message.imageUrl" alt="Generated Image" />
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
          <template #default>
            <el-input
              type="textarea"
              ref="textareaRef"
              :autosize="{ minRows: 1, maxRows: 8 }"
              placeholder="请描述想要生成的图片"
              @input="adjustTextareaHeight"
            />
          </template>
          <template #append>
            <el-button 
              type="success" 
              icon="Picture"
              style="height: 100%;"
              @click="handleGenerateImage"
            >生成图像</el-button>
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="text-to-image">
import { ref, nextTick, onMounted } from 'vue';
import { User, Picture } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { useSidebarStore } from '../../store/sidebar';
import { generateImageFromText } from '@/api/image';

const inputText = ref('');
const textareaRef = ref(null);
const messagesContainer = ref(null);
const isTyping = ref(false);
const sidebar = useSidebarStore();

// 聊天消息数组
const messages = ref([
  {
    role: 'assistant',
    content: '你好！请输入描述以生成图片。'
  }
]);

// 图像生成函数
const handleGenerateImage = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入图像生成提示');
    return;
  }
  const prompt = inputText.value.trim();
  
  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: prompt,
  });
  
  isTyping.value = true;
  try {
    const response = await generateImageFromText(prompt);
    const { message, generation } = response.data;
    messages.value.push({
      role: 'assistant',
      content: `生成的图像: ${generation.generated_image_oss_url}`,
      imageUrl: generation.generated_image_oss_url,
    });
    inputText.value = '';
    nextTick(() => scrollToBottom());
  } catch (error) {
    console.error('图像生成失败:', error);
    ElMessage.error('图像生成失败，请重试！');
  } finally {
    isTyping.value = false;
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

.message-image {
  margin-top: 10px;
}

.message-image img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
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
</style>