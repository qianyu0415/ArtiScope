<template>
  <el-card class="my-posts">
    <h2>我的作品</h2>

    <el-card v-for="post in myPosts" :key="post.id" class="mb-3">
      <el-input v-model="post.caption" placeholder="编辑描述" class="mb-2" />
      <div v-html="post.content" class="mb-2"></div>

      <el-button type="primary" size="small" @click="updatePost(post)">更新</el-button>
      <el-button type="danger" size="small" @click="deletePost(post.id)">删除</el-button>
    </el-card>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const myPosts = ref([])

const fetchMyPosts = async () => {
  const res = await fetch('/fake_api/my_posts')
  myPosts.value = await res.json()
}

const updatePost = async (post) => {
  await fetch(`/fake_api/my_posts/${post.id}`, {
    method: 'PUT',
    body: JSON.stringify({ caption: post.caption }),
    headers: { 'Content-Type': 'application/json' }
  })
  ElMessage.success('更新成功')
}

const deletePost = async (id) => {
  ElMessageBox.confirm('确定删除该作品？', '提示', {
    type: 'warning',
  }).then(async () => {
    await fetch(`/fake_api/my_posts/${id}`, { method: 'DELETE' })
    ElMessage.success('删除成功')
    fetchMyPosts()
  })
}

onMounted(fetchMyPosts)
</script>

<style scoped>
.my-posts {
  max-width: 1600px;
  margin: 20px auto;
}
.mb-2 {
  margin-bottom: 10px;
}
.mb-3 {
  margin-bottom: 20px;
}
</style>
