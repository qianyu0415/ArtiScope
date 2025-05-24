<template>
  <el-card class="post-creator">
    <h2>选择创作作品进行发布</h2>

    <el-form label-width="80px" class="form">
      <el-form-item label="描述">
        <el-input v-model="caption" placeholder="请输入作品描述" />
      </el-form-item>

      <el-form-item label="作品类型">
        <el-select v-model="type" placeholder="请选择类型" @change="fetchLogs">
          <el-option label="ASCII 图片" value="ascii" />
          <el-option label="文生图" value="text2img" />
          <el-option label="ASCII 视频" value="video" />
        </el-select>
      </el-form-item>

      <el-form-item label="选择作品">
        <el-select v-model="selectedLog" placeholder="请选择一个作品">
          <el-option
            v-for="log in logs"
            :key="log.id"
            :label="type === 'text2img' ? log.generated_image_oss_url : log.output_oss_url"
            :value="log"
          >
            <span>{{ log.created_at }} - {{ type === 'text2img' ? log.generated_image_oss_url : log.output_oss_url }}</span>
          </el-option>
        </el-select>
      </el-form-item>
        <el-form-item label="预览">
        <div v-if="selectedLog">
            <video
            v-if="type === 'video'"
            controls
            :src="selectedLog.output_oss_url"
            style="max-width: 100%"
            />
            <img
            v-else
            :src="type === 'text2img' ? selectedLog.generated_image_oss_url : selectedLog.output_oss_url"
            style="max-width: 100%"
            />
        </div>
        <div v-else>未选择作品</div>
        </el-form-item>

      <el-button type="primary" @click="submitPost" :disabled="!selectedLog">发布</el-button>
    </el-form>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import {
  getImageLogs,
  getTextToImageLogs,
  getVideoLogs,
} from '@/api/image.js'
import { ElMessage } from 'element-plus'

const caption = ref('')
const type = ref('')
const logs = ref([])
const selectedLog = ref(null)

const fetchLogs = async () => {
  selectedLog.value = null
  if (type.value === 'ascii') {
    const res = await getImageLogs({ page: 1, per_page: 5 })
    logs.value = res.data.logs
  } else if (type.value === 'text2img') {
    const res = await getTextToImageLogs({ page: 1, per_page: 5 })
    logs.value = res.data.data
    console.log(logs.value)
  } else if (type.value === 'video') {
    const res = await getVideoLogs({ page: 1, per_page: 5 })
    logs.value = res.data.logs
  }
}

const submitPost = async () => {
  if (!selectedLog.value || !caption.value) {
    ElMessage.warning('请填写描述并选择一个作品')
    return
  }

  // 模拟调用后端发表接口
  await fetch('/fake_api/publish_post', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      caption: caption.value,
      type: type.value,
      source_url: selectedLog.value.output_oss_url,
      created_at: selectedLog.value.created_at,
    }),
  })

  ElMessage.success('发布成功！')
  caption.value = ''
  selectedLog.value = null
}
</script>

<style scoped>
.post-creator {
  max-width: 1000px;
  margin: 30px auto;
}
.form {
  margin-top: 20px;
}
</style>
