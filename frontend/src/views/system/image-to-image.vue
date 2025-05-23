<template>
  <div class="container">
    <!-- 左侧：图片预览 -->
    <div class="left-panel">
      <div v-if="originalImage" class="image-preview">
        <el-image
          :src="originalImage"
          fit="contain"
          style="max-width: 100%; max-height: 400px;"
          alt="原始图片"
        />
      </div>
      <div v-else class="placeholder">
        <el-empty description="暂无图片" />
      </div>
    </div>

    <!-- 中间：选择图片、输入框和转换按钮 -->
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
        :on-change="handleImageChange"
        :on-remove="handleImageRemove"
        :auto-upload="false"
        accept="image/*"
      >
        <el-button type="primary" :icon="UploadFilled" style="margin-top: 50px">选择图片</el-button>
        <template #tip>
          <div class="el-upload__tip">仅支持图片文件，单张上传</div>
        </template>
      </el-upload>
      
      <el-button
        type="primary"
        size="large"
        :disabled="!originalImage"
        @click="handleTransform"
        style="margin-top: 20px;"
      >
        转换图片
      </el-button>
    </div>

    <!-- 右侧：转换后图片展示及日志 -->
    <div class="right-panel">
      <div v-if="transformedImage" class="image-preview">
        <el-image
          :src="transformedImage"
          fit="contain"
          style="max-width: 100%; max-height: 400px;"
          alt="转换后图片"
        />
        <div class="download-btn-container">
          <el-button
            type="success"
            @click="downloadImage"
            :icon="Download"
          >
            下载图片
          </el-button>
        </div>
      </div>
      <div v-else class="placeholder">
        <el-empty description="暂无转换后的图片" />
      </div>

      <!-- 日志展示区域 -->
      <div class="log-panel" v-if="logs.length">
        <h3>最新图片处理记录</h3>
        <el-table :data="logs" style="width: 100%" max-height="200">
          <el-table-column prop="input_token" label="编码词" width="100" />
          <el-table-column prop="created_at" label="创建时间" />
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                type="text"
                @click="viewProcessedImage(row.output_oss_url)"
              >
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="image-to-image">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled, Download } from '@element-plus/icons-vue';
import { uploadImage, getImageLogs } from '@/api/image'; // 导入 image.js 中的 API 方法

// 原始图片和转换后图片的 URL
const originalImage = ref<string | null>(null);
const transformedImage = ref<string | null>(null);
const uploadRef = ref(null);
const userInput = ref(''); // 用户输入的文本
const selectedFile = ref<File | null>(null); // 存储选中的文件对象
const logs = ref<any[]>([]); // 存储日志记录

// 处理图片选择
const handleImageChange = (file: any) => {
  uploadRef.value.clearFiles(); // 清空之前的文件列表，确保替换
  if (file.raw && file.raw.type.startsWith('image/')) {
    originalImage.value = URL.createObjectURL(file.raw);
    transformedImage.value = null; // 清除转换后的图片
    selectedFile.value = file.raw; // 保存文件对象
  } else {
    ElMessage.error('请选择有效的图片文件！');
    uploadRef.value.clearFiles();
  }
};

// 处理图片移除
const handleImageRemove = () => {
  originalImage.value = null;
  transformedImage.value = null;
  selectedFile.value = null;
};

// 处理图片转换
const handleTransform = async () => {
  if (!originalImage.value || !selectedFile.value) {
    ElMessage.error('请先选择图片！');
    return;
  }
  
  try {
    const formData = new FormData();
    formData.append('file', selectedFile.value); // 字段名必须为 'file'
    if (userInput.value) {
      formData.append('token', userInput.value);
    }
    
    const response = await uploadImage(formData);
    
    if (response.status === 201) {
      transformedImage.value = response.data.processed_image_url;
      ElMessage.success('图片转换成功！');
      fetchLogs(); // 转换成功后刷新日志
    } else {
      throw new Error('无效的响应数据');
    }
  } catch (error: any) {
    console.error('转换错误:', error);
    const message = error.response?.data?.message || '图片转换失败，请重试';
    if (error.response?.status === 400) {
      ElMessage.error(message || '请求中未包含图片文件或文件名为空');
    } else if (error.response?.status === 401) {
      ElMessage.error('未授权访问，请先登录');
    } else if (error.response?.status === 503) {
      ElMessage.error('OSS 服务未配置或配置错误');
    } else {
      ElMessage.error(message);
    }
  }
};

// 下载转换后的图片
const downloadImage = () => {
  if (!transformedImage.value) return;
  
  const link = document.createElement('a');
  link.href = transformedImage.value;
  link.download = 'converted-image.png';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// 获取最新图片处理记录
const fetchLogs = async () => {
  try {
    const response = await getImageLogs({
      page: 1,
      per_page: 1, // 只获取一条记录
      sort_by: 'created_at',
      sort_order: 'desc', // 按创建时间降序排序，确保获取最新记录
    });
    
    if (response.status === 200) {
      logs.value = response.data.logs || [];
    } else {
      throw new Error('获取日志失败');
    }
  } catch (error: any) {
    console.error('获取日志错误:', error);
    const message = error.response?.data?.message || '获取日志失败，请重试';
    if (error.response?.status === 401) {
      ElMessage.error('未授权访问，请先登录');
    } else {
      ElMessage.error(message);
    }
  }
};

// 查看处理后的图片
const viewProcessedImage = (url: string) => {
  transformedImage.value = url;
};
</script>

<style scoped>
.container {
  display: flex;
  height: 74vh;
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
  width: 250px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 20px;
}

.image-preview {
  margin-top: 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.upload-demo {
  text-align: center;
  width: 100%;
}

.el-upload__tip {
  margin-top: 8px;
  color: #606266;
  font-size: 12px;
}

.download-btn-container {
  margin-top: 20px;
}

.log-panel {
  margin-top: 20px;
  width: 100%;
}

.log-panel h3 {
  margin-bottom: 10px;
}
</style>