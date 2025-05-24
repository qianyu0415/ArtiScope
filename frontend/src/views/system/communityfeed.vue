<template>
  <el-card class="community-feed">
    <h2>社区作品</h2>

    <el-card v-for="post in posts" :key="post.id" class="mb-3">
      <p><strong>{{ post.caption }}</strong></p>
      <div v-html="post.content" class="mb-2"></div>

      <el-button type="primary" size="small" @click="likePost(post.id)">
        👍 {{ post.likes }}
      </el-button>

      <el-input v-model="comment" placeholder="发表评论" size="small" class="mt-2" />
      <el-button type="success" size="small" class="mt-1" @click="submitComment(post.id)">评论</el-button>

      <el-divider></el-divider>
      <div v-for="(c, index) in post.comments" :key="index">
        <el-tag class="mr-1">{{ c }}</el-tag>
      </div>
    </el-card>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const posts = ref([])
const comment = ref('')

const fetchPosts = async () => {
  const res = await fetch('/fake_api/posts')
  posts.value = await res.json()
}

const likePost = async (id) => {
  await fetch(`/fake_api/posts/${id}/like`, { method: 'POST' })
  ElMessage.success('已点赞')
  fetchPosts()
}

const submitComment = async (id) => {
  await fetch(`/fake_api/posts/${id}/comment`, {
    method: 'POST',
    body: JSON.stringify({ text: comment.value }),
    headers: { 'Content-Type': 'application/json' }
  })
  comment.value = ''
  fetchPosts()
}

onMounted(fetchPosts)
</script>

<style scoped>
.community-feed {
  max-width: 1600px;
  margin: 20px auto;
}
.mb-3 {
  margin-bottom: 20px;
}
.mt-1 {
  margin-top: 8px;
}
.mt-2 {
  margin-top: 12px;
}
.mr-1 {
  margin-right: 6px;
}
</style>
