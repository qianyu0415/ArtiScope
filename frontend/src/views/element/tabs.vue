<template>
  <el-tabs v-model="activeTab" type="card">
    <!-- ASCII图片栏 -->
    <el-tab-pane label="ASCII图片" name="ascii-images">
      <div class="search-container">
        <el-input
          v-model="asciiImageSearch"
          placeholder="搜索ASCII图片标题"
          clearable
          @clear="handleAsciiSearchClear"
          @keyup.enter="handleAsciiSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="handleAsciiSearch" />
          </template>
        </el-input>
      </div>
      
      <el-table 
        :data="filteredAsciiImages" 
        :show-header="false" 
        style="width: 100%"
        v-loading="asciiLoading"
        empty-text="暂无ASCII图片数据"
      >
        <el-table-column>
          <template #default="scope">
            <div class="media-item">
              <el-image
                :src="scope.row.output_oss_url"
                fit="cover"
                class="media-thumbnail"
                :preview-src-list="[scope.row.output_oss_url]"
                preview-teleported
                hide-on-click-modal
              />
              <div class="media-info">
                <span class="media-title">{{ scope.row.input_token || '未命名图片' }}</span>
                <span class="media-date">{{ formatDate(scope.row.created_at) }}</span>
              </div>
              <el-button 
                size="small" 
                type="primary" 
                @click="downloadMedia(scope.row.output_oss_url, scope.row.input_token || 'ascii-image')"
                class="download-btn"
              >
                下载
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="asciiCurrentPage"
          v-model:page-size="asciiPageSize"
          :total="asciiTotalImages"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next, jumper"
          background
          @size-change="fetchAsciiImageLogs"
          @current-change="fetchAsciiImageLogs"
        />
      </div>
    </el-tab-pane>
    
    <!-- 文生图图片栏 -->
    <el-tab-pane label="文生图图片" name="text-to-images">
      <div class="search-container">
        <el-input
          v-model="textImageSearch"
          placeholder="搜索文生图提示词"
          clearable
          @clear="handleTextImageSearchClear"
          @keyup.enter="handleTextImageSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="handleTextImageSearch" />
          </template>
        </el-input>
      </div>
      
      <el-table 
        :data="filteredTextImages" 
        :show-header="false" 
        style="width: 100%"
        v-loading="textImageLoading"
        empty-text="暂无文生图图片数据"
      >
        <el-table-column>
          <template #default="scope">
            <div class="media-item">
              <el-image
                :src="scope.row.generated_image_oss_url"
                fit="cover"
                class="media-thumbnail"
                :preview-src-list="[scope.row.generated_image_oss_url]"
                preview-teleported
                hide-on-click-modal
              />
              <div class="media-info">
                <span class="media-title">{{ scope.row.prompt || '未命名图片' }}</span>
                <span class="media-date">{{ formatDate(scope.row.created_at) }}</span>
              </div>
              <el-button 
                size="small" 
                type="primary" 
                @click="downloadMedia(scope.row.generated_image_oss_url, scope.row.prompt || 'text-to-image')"
                class="download-btn"
              >
                下载
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="textImageCurrentPage"
          v-model:page-size="textImagePageSize"
          :total="textImageTotalImages"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next, jumper"
          background
          @size-change="fetchTextToImageLogs"
          @current-change="fetchTextToImageLogs"
        />
      </div>
    </el-tab-pane>
    
    <!-- 视频栏 -->
    <el-tab-pane label="ASCII视频" name="videos">
      <div class="search-container">
        <el-input
          v-model="videoSearch"
          placeholder="搜索视频标题"
          clearable
          @clear="handleVideoSearchClear"
          @keyup.enter="handleVideoSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="handleVideoSearch" />
          </template>
        </el-input>
      </div>
      
      <el-table 
        :data="filteredVideos" 
        :show-header="false" 
        style="width: 100%"
        v-loading="videoLoading"
        empty-text="暂无视频数据"
      >
        <el-table-column>
          <template #default="scope">
            <div class="media-item">
              <video
                :src="scope.row.output_oss_url"
                controls
                class="media-thumbnail"
                @click="openFullScreenVideo(scope.row.output_oss_url)"
              ></video>
              <div class="media-info">
                <span class="media-title">{{ scope.row.input_token || '未命名视频' }}</span>
                <span class="media-date">{{ formatDate(scope.row.created_at) }}</span>
              </div>
              <el-button 
                size="small" 
                type="primary" 
                @click="downloadMedia(scope.row.output_oss_url, scope.row.input_token || 'ascii-video')"
                class="download-btn"
              >
                下载
              </el-button>
              <el-button 
                size="small" 
                type="info" 
                @click="openFullScreenVideo(scope.row.input_oss_url)"
                class="download-btn"
              >
                预览原始视频
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="videoCurrentPage"
          v-model:page-size="videoPageSize"
          :total="videoTotalItems"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next, jumper"
          background
          @size-change="fetchVideoLogs"
          @current-change="fetchVideoLogs"
        />
      </div>
    </el-tab-pane>
  </el-tabs>

  <!-- 全屏视频播放对话框 -->
  <el-dialog
    v-model="videoDialogVisible"
    title="视频播放"
    width="70%"
    :before-close="closeVideoDialog"
    center
  >
    <video 
      :src="currentVideoUrl" 
      controls 
      autoplay 
      style="width: 100%;"
      class="fullscreen-video"
    ></video>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';
import { getImageLogs, getTextToImageLogs, getVideoLogs } from '@/api/image';

// 定义ASCII图片项接口
interface AsciiImageItem {
  id: number;
  user_id: number;
  username: string;
  input_oss_url: string;
  input_token: string;
  output_oss_url: string;
  created_at: string;
  updated_at: string;
}

// 定义文生图图片项接口
interface TextImageItem {
  id: number;
  user_id: number;
  prompt: string;
  generated_image_oss_url: string;
  created_at: string;
  updated_at: string;
}

// 定义视频项接口
interface VideoItem {
  id: number;
  user_id: number;
  username: string;
  input_oss_url: string;
  input_token: string;
  output_oss_url: string;
  created_at: string;
  updated_at: string;
}

// 活跃标签页
const activeTab = ref('ascii-images');

// 搜索关键词
const asciiImageSearch = ref('');
const textImageSearch = ref('');
const videoSearch = ref('');

// ASCII图片分页相关
const asciiCurrentPage = ref(1);
const asciiPageSize = ref(2);
const asciiTotalImages = ref(0);
const asciiLoading = ref(false);

// 文生图图片分页相关
const textImageCurrentPage = ref(1);
const textImagePageSize = ref(2);
const textImageTotalImages = ref(0);
const textImageLoading = ref(false);

// 视频分页相关
const videoCurrentPage = ref(1);
const videoPageSize = ref(2);
const videoTotalItems = ref(0);
const videoLoading = ref(false);

// 数据
const asciiImageLogs = ref<AsciiImageItem[]>([]);
const textImageLogs = ref<TextImageItem[]>([]);
const videoLogs = ref<VideoItem[]>([]);

// 获取ASCII图片处理记录
const fetchAsciiImageLogs = async () => {
  asciiLoading.value = true;
  try {
    const response = await getImageLogs({
      page: asciiCurrentPage.value,
      per_page: asciiPageSize.value,
    });
    
    if (response.status === 200) {
      asciiImageLogs.value = response.data.logs || [];
      asciiTotalImages.value = response.data.total_logs || 0;
      if (response.data.total_pages && asciiCurrentPage.value > response.data.total_pages) {
        asciiCurrentPage.value = response.data.total_pages || 1;
        await fetchAsciiImageLogs();
      }
    } else {
      throw new Error('获取ASCII图片日志失败');
    }
  } catch (error: any) {
    console.error('获取ASCII图片日志错误:', error);
    const message = error.response?.data?.message || '获取ASCII图片日志失败，请重试';
    if (error.response?.status === 401) {
      ElMessage.error('未授权访问，请先登录');
    } else {
      ElMessage.error(message);
    }
  } finally {
    asciiLoading.value = false;
  }
};

// 获取文生图图片处理记录
const fetchTextToImageLogs = async () => {
  textImageLoading.value = true;
  try {
    const response = await getTextToImageLogs({
      page: textImageCurrentPage.value,
      per_page: textImagePageSize.value,
    });
    
    if (response.status === 200) {
      textImageLogs.value = response.data.data || [];
      textImageTotalImages.value = response.data.pagination.total || 0;
      if (response.data.pagination.pages && textImageCurrentPage.value > response.data.pagination.pages) {
        textImageCurrentPage.value = response.data.pagination.pages || 1;
        await fetchTextToImageLogs();
      }
    } else {
      throw new Error('获取文生图图片日志失败');
    }
  } catch (error: any) {
    console.error('获取文生图图片日志错误:', error);
    const message = error.response?.data?.message || '获取文生图图片日志失败，请重试';
    if (error.response?.status === 401) {
      ElMessage.error('未授权访问，请先登录');
    } else {
      ElMessage.error(message);
    }
  } finally {
    textImageLoading.value = false;
  }
};

const fetchVideoLogs = async () => {
  videoLoading.value = true;
  try {
    const response = await getVideoLogs({
      page: videoCurrentPage.value,
      per_page: videoPageSize.value,
    });
    
    if (response.status === 200) {
      videoLogs.value = response.data.logs || [];
      videoTotalItems.value = response.data.total_logs || 0;
      if (response.data.total_pages && videoCurrentPage.value > response.data.total_pages) {
        videoCurrentPage.value = response.data.total_pages || 1;
        await fetchVideoLogs();
      }
    } else {
      throw new Error('获取视频日志失败');
    }
  } catch (error: any) {
    console.error('获取视频日志错误:', error);
    const message = error.response?.data?.message || '获取视频日志失败，请重试';
    if (error.response?.status === 401) {
      ElMessage.error('未授权访问，请先登录');
    } else {
      ElMessage.error(message);
    }
  } finally {
    videoLoading.value = false;
  }
};

// 格式化日期
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  } catch {
    return dateString;
  }
};

// 处理ASCII图片搜索
const handleAsciiSearch = () => {
  asciiCurrentPage.value = 1;
  fetchAsciiImageLogs();
};

// 处理ASCII图片搜索框清除
const handleAsciiSearchClear = () => {
  asciiImageSearch.value = '';
  handleAsciiSearch();
};

// 处理文生图图片搜索
const handleTextImageSearch = () => {
  textImageCurrentPage.value = 1;
  fetchTextToImageLogs();
};

// 处理文生图图片搜索框清除
const handleTextImageSearchClear = () => {
  textImageSearch.value = '';
  handleTextImageSearch();
};

// 处理视频搜索
const handleVideoSearch = () => {
  videoCurrentPage.value = 1;
  fetchVideoLogs();
};

// 处理视频搜索框清除
const handleVideoSearchClear = () => {
  videoSearch.value = '';
  handleVideoSearch();
};

// 过滤ASCII图片
const filteredAsciiImages = computed(() => {
  if (!asciiImageSearch.value) return asciiImageLogs.value;
  return asciiImageLogs.value.filter(item => 
    (item.input_token || '').toLowerCase().includes(asciiImageSearch.value.toLowerCase())
  );
});

// 过滤文生图图片
const filteredTextImages = computed(() => {
  if (!textImageSearch.value) return textImageLogs.value;
  return textImageLogs.value.filter(item => 
    (item.prompt || '').toLowerCase().includes(textImageSearch.value.toLowerCase())
  );
});

// 过滤视频
const filteredVideos = computed(() => {
  if (!videoSearch.value) return videoLogs.value;
  return videoLogs.value.filter(item => 
    (item.input_token || '').toLowerCase().includes(videoSearch.value.toLowerCase())
  );
});

// 下载媒体文件
const downloadMedia = async (url: string, title: string) => {
  try {
    const link = document.createElement('a');
    link.href = url;
    const fileName = url.split('/').pop()?.split('?')[0] || 'download';
    const fileExt = fileName.split('.').pop() || 'mp4';
    link.download = `${title}.${fileExt}`;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    ElMessage.success('下载已开始');
  } catch (error) {
    ElMessage.error('下载失败，请检查 URL 或网络');
    console.error('Download error:', error);
  }
};

// 全屏播放视频相关逻辑
const videoDialogVisible = ref(false);
const currentVideoUrl = ref('');

const openFullScreenVideo = (url: string) => {
  currentVideoUrl.value = url;
  videoDialogVisible.value = true;
};

const closeVideoDialog = () => {
  videoDialogVisible.value = false;
  currentVideoUrl.value = '';
};

// 初始化时获取所有记录
onMounted(() => {
  fetchAsciiImageLogs();
  fetchTextToImageLogs();
  fetchVideoLogs();
});
</script>

<style scoped>
.search-container {
  margin-bottom: 20px;
  max-width: 400px;
}

.media-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.media-thumbnail {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
}

.media-info {
  flex: 1;
  margin-left: 15px;
  display: flex;
  flex-direction: column;
}

.media-title {
  font-size: 14px;
  color: var(--el-color-primary);
  margin-bottom: 5px;
  word-break: break-all;
}

.media-date {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.download-btn {
  margin-left: 15px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.fullscreen-video {
  max-height: 70vh;
}

.el-table {
  --el-table-border-color: transparent;
}

.el-table::before {
  display: none;
}
</style>