<template>
  <el-tabs v-model="activeTab" type="card">
    <!-- 图片栏 -->
    <el-tab-pane label="图片" name="images">
      <div class="search-container">
        <el-input
          v-model="imageSearch"
          placeholder="搜索图片标题"
          clearable
          @clear="handleSearchClear"
          @keyup.enter="handleSearch"
        >
          <template #append>
            <el-button :icon="Search" @click="handleSearch" />
          </template>
        </el-input>
      </div>
      
      <el-table 
        :data="filteredImages" 
        :show-header="false" 
        style="width: 100%"
        v-loading="loading"
        empty-text="暂无图片数据"
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
                @click="downloadMedia(scope.row.output_oss_url, scope.row.input_token || 'image')"
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
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalImages"
          :page-sizes="[10, 20, 50, 100]"
          layout="sizes, prev, pager, next, jumper"
          background
          @size-change="fetchImageLogs"
          @current-change="fetchImageLogs"
        />
      </div>
    </el-tab-pane>
    
    <!-- 视频栏 -->
    <el-tab-pane label="视频" name="videos">
      <div class="search-container">
        <el-input
          v-model="videoSearch"
          placeholder="搜索视频标题"
          clearable
        >
          <template #append>
            <el-button :icon="Search" />
          </template>
        </el-input>
      </div>
      
      <el-table 
        :data="filteredVideos" 
        :show-header="false" 
        style="width: 100%"
        empty-text="暂无视频数据"
      >
        <el-table-column>
          <template #default="scope">
            <div class="media-item">
              <video
                :src="scope.row.url"
                controls
                class="media-thumbnail"
                @click="openFullScreenVideo(scope.row.url)"
              ></video>
              <div class="media-info">
                <span class="media-title">{{ scope.row.title }}</span>
                <span class="media-date">{{ scope.row.date }}</span>
              </div>
              <el-button 
                size="small" 
                type="primary" 
                @click="downloadMedia(scope.row.url, scope.row.title)"
                class="download-btn"
              >
                下载
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
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
import { getImageLogs } from '@/api/image'; // 根据实际路径调整

// 定义图片项接口
interface ImageItem {
  id: number;
  user_id: number;
  username: string;
  input_oss_url: string;
  input_token: string;
  output_oss_url: string;
  created_at: string;
  updated_at: string;
}

// 定义视频项接口
interface VideoItem {
  id: string;
  title: string;
  url: string;
  date: string;
}

// 活跃标签页
const activeTab = ref('images');

// 搜索关键词
const imageSearch = ref('');
const videoSearch = ref('');

// 分页相关
const currentPage = ref(1);
const pageSize = ref(2);
const totalImages = ref(0);
const loading = ref(false);

// 图片数据
const imageLogs = ref<ImageItem[]>([]);

// 视频数据（示例数据，可根据需要替换为API获取）
const videoLogs = ref<VideoItem[]>([
  {
    id: '1',
    title: '示例视频1',
    url: 'https://example.com/video1.mp4',
    date: '2023-05-01'
  },
  {
    id: '2',
    title: '示例视频2',
    url: 'https://example.com/video2.mp4',
    date: '2023-05-02'
  }
]);

// 获取图片处理记录
const fetchImageLogs = async () => {
  try {
    const response = await getImageLogs({
      page: currentPage.value,
      per_page: pageSize.value,
    });
    
    if (response.status === 200) {
      imageLogs.value = response.data.logs || [];
      totalImages.value = response.data.total_logs || 0;
      // Ensure currentPage is within valid range
      if (response.data.total_pages && currentPage.value > response.data.total_pages) {
        currentPage.value = response.data.total_pages || 1;
        await fetchImageLogs(); // Re-fetch with corrected page
      }
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

// 格式化日期
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  } catch {
    return dateString;
  }
};

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  fetchImageLogs();
};

// 处理搜索框清除
const handleSearchClear = () => {
  imageSearch.value = '';
  handleSearch();
};

// 过滤图片
const filteredImages = computed(() => {
  if (!imageSearch.value) return imageLogs.value;
  return imageLogs.value.filter(item => 
    (item.input_token || '').toLowerCase().includes(imageSearch.value.toLowerCase())
  );
});

// 过滤视频
const filteredVideos = computed(() => {
  if (!videoSearch.value) return videoLogs.value;
  return videoLogs.value.filter(item => 
    item.title.toLowerCase().includes(videoSearch.value.toLowerCase())
  );
});

// 下载媒体文件
const downloadMedia = async (url: string, title: string) => {
  try {
    // 创建一个隐藏的a标签
    const link = document.createElement('a');
    link.href = url;
    
    // 从URL中提取文件名
    const fileName = url.split('/').pop()?.split('?')[0] || 'download';
    const fileExt = fileName.split('.').pop() || 'jpg';
    
    // 设置下载属性
    link.download = `${title}.${fileExt}`;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    
    // 触发点击
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

// 初始化时获取图片记录
onMounted(() => {
  fetchImageLogs();
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