<template>
  <div class="container">
    <!-- 左侧：视频预览 -->
    <div class="left-panel">
      <div v-if="originalVideo" class="video-preview">
        <video
          controls
          style="max-width: 100%; max-height: 400px;"
          :src="originalVideo"
          alt="原始视频"
        />
      </div>
      <div v-else class="placeholder">
        <el-empty description="暂无视频" />
      </div>
    </div>

    <!-- 中间：选择视频和转换按钮 -->
    <div class="center-panel">
      <el-input
        v-model="userInput"
        type="textarea"
        :rows="1"
        placeholder="请输入编码词（可选）"
        style="width: 90%;"
      />

      <el-upload
        ref="uploadRef"
        class="upload-demo"
        :limit="1"
        :on-change="handleVideoChange"
        :on-remove="handleVideoRemove"
        :auto-upload="false"
        accept="video/*"
      >
        <el-button type="primary" :icon="UploadFilled" style="margin-top: 50px">选择视频</el-button>
        <template #tip>
          <div class="el-upload__tip">仅支持视频文件，单次上传</div>
        </template>
      </el-upload>
      <el-button
        type="primary"
        size="large"
        :disabled="!originalVideo"
        @click="handleTransform"
        :loading="isTransforming"
      >
        {{ isTransforming ? '转换中...' : '转换视频' }}
      </el-button>
    </div>

    <!-- 右侧：转换后视频展示 -->
    <div class="right-panel">
      <div v-if="transformedVideo" class="video-preview">
        <video
          controls
          style="max-width: 100%; max-height: 400px;"
          :src="transformedVideo"
          alt="转换后视频"
        />
      </div>
      <div v-else class="placeholder">
        <el-empty description="暂无转换后的视频" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="video-to-video">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';

// 原始视频和转换后视频的 URL
const originalVideo = ref(null);
const transformedVideo = ref(null);
const uploadRef = ref(null);
const isTransforming = ref(false);

// 处理视频选择
const handleVideoChange = (file) => {
  uploadRef.value.clearFiles(); // 清空之前的文件列表，确保替换
  if (file.raw && file.raw.type.startsWith('video/')) {
    originalVideo.value = URL.createObjectURL(file.raw);
    transformedVideo.value = null; // 清除转换后的视频
  } else {
    ElMessage.error('请选择有效的视频文件！');
    uploadRef.value.clearFiles();
  }
};

// 处理视频移除
const handleVideoRemove = () => {
  originalVideo.value = null;
  transformedVideo.value = null;
};

// 处理视频转换
const handleTransform = async () => {
  if (!originalVideo.value) return;

  isTransforming.value = true;
  
  try {
    // 这里应该是实际的视频转换逻辑
    // 模拟转换过程
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 实际应用中，这里应该调用API或使用FFmpeg等工具进行视频转换
    // 这里只是模拟，使用相同的视频URL
    transformedVideo.value = originalVideo.value;
    
    ElMessage.success('视频转换成功！');
  } catch (error) {
    ElMessage.error('视频转换失败: ' + error.message);
  } finally {
    isTransforming.value = false;
  }
};
</script>

<style scoped>
.container {
  display: flex;
  height: 100vh;
  padding: 20px;
  background-color: #f5f7fa;
}

.left-panel,
.right-panel {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.center-panel {
  width: 250px; /* 加宽以适应输入框 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center; /* 从顶部开始排列 */
  gap: 20px;
  padding: 20px;
}

.video-preview {
  margin-top: 20px;
  text-align: center;
  width: 100%;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.upload-demo {
  text-align: center;
}

.el-upload__tip {
  margin-top: 8px;
  color: #606266;
}
</style>