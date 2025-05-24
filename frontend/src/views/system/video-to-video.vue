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

    <!-- 中间：选择视频、参数和转换按钮 -->
    <div class="center-panel">
      <el-input
        v-model="token"
        type="textarea"
        :rows="1"
        placeholder="请输入编码词（可选）"
        style="width: 90%;"
      />
      <el-form label-position="top" style="width: 90%; margin-top: 20px;">
        <el-form-item label="背景颜色">
          <el-select v-model="options.background" placeholder="选择背景颜色">
            <el-option label="黑色" value="black" />
            <el-option label="白色" value="white" />
          </el-select>
        </el-form-item>
        <el-form-item label="模式">
          <el-select v-model="options.mode" placeholder="选择模式">
            <el-option label="简单" value="simple" />
            <el-option label="复杂" value="complex" />
          </el-select>
        </el-form-item>
        <el-form-item label="输出宽度字符数">
          <el-input-number v-model="options.num_cols" :min="10" :max="2000" />
        </el-form-item>
        <el-form-item label="缩放比例">
          <el-input-number v-model="options.scale" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="帧率 (FPS)">
          <el-input-number v-model="options.fps" :min="0" :max="60" />
        </el-form-item>
        <el-form-item label="叠加比例">
          <el-input-number v-model="options.overlay_ratio" :min="0" :max="1" :step="0.1" />
        </el-form-item>
      </el-form>
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        :limit="1"
        :on-change="handleVideoChange"
        :on-remove="handleVideoRemove"
        :auto-upload="false"
        accept="video/*"
        :file-list="fileList"
      >
        <el-button type="primary" :icon="UploadFilled" style="margin-top: 20px">选择视频</el-button>
        <template #tip>
          <div class="el-upload__tip">仅支持视频文件，单次上传</div>
        </template>
      </el-upload>
      <el-button
        type="primary"
        size="large"
        :disabled="!originalVideo || fileList.length === 0"
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
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';
import { uploadVideo } from '@/api/image';

const originalVideo = ref(null);
const transformedVideo = ref(null);
const uploadRef = ref(null);
const isTransforming = ref(false);
const token = ref('');
const fileList = ref([]); // 跟踪上传文件列表
const options = ref({
  background: 'black',
  mode: 'simple',
  num_cols: 1080,
  scale: 1,
  fps: 30,
  overlay_ratio: 0.5
});

const handleVideoChange = (file, uploadFiles) => {
  console.log('File selected:', file);
  console.log('Upload files:', uploadFiles);
  if (file.raw && file.raw.type.startsWith('video/')) {
    originalVideo.value = URL.createObjectURL(file.raw);
    transformedVideo.value = null;
    fileList.value = [file]; // 更新 fileList
  } else {
    ElMessage.error('请选择有效的视频文件！');
    fileList.value = [];
    if (uploadRef.value) {
      uploadRef.value.clearFiles();
    }
  }
};

const handleVideoRemove = () => {
  originalVideo.value = null;
  transformedVideo.value = null;
  fileList.value = [];
  if (uploadRef.value) {
    uploadRef.value.clearFiles();
  }
};

const handleTransform = async () => {
  if (!originalVideo.value) {
    ElMessage.error('请先选择视频文件！');
    return;
  }

  if (!fileList.value.length) {
    ElMessage.error('未找到上传的视频文件！');
    return;
  }

  isTransforming.value = true;
  const formData = new FormData();
  formData.append('file', fileList.value[0].raw);
  formData.append('token', token.value);
  formData.append('background', options.value.background);
  formData.append('mode', options.value.mode);
  formData.append('num_cols', options.value.num_cols.toString());
  formData.append('scale', options.value.scale.toString());
  formData.append('fps', options.value.fps.toString());
  formData.append('overlay_ratio', options.value.overlay_ratio.toString());

  try {
    const response = await uploadVideo(formData);
    if (!response.data || !response.data.processed_video_url) {
      throw new Error('后端响应缺少 processed_video_url');
    }
    transformedVideo.value = response.data.processed_video_url;
    ElMessage.success('视频转换成功！');
  } catch (error) {
    ElMessage.error('视频转换失败: ' + (error.response?.data?.message || error.message));
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
  width: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
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