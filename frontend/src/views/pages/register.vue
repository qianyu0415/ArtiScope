<template>
  <div class="login-bg">
    <div class="login-container">
      <div class="login-header">
        <img class="logo mr10" src="../../assets/img/logo.svg" alt="" />
        <div class="login-title">后台管理系统</div>
      </div>
      <el-form :model="param" :rules="rules" ref="registerForm" size="large">
        <el-form-item prop="username">
          <el-input v-model="param.username" placeholder="用户名">
            <template #prepend><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            type="password"
            placeholder="密码"
            v-model="param.password"
            @keyup.enter="submitForm"
          >
            <template #prepend><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            type="password"
            placeholder="确认密码"
            v-model="param.confirmPassword"
            @keyup.enter="submitForm"
          >
            <template #prepend><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button class="login-btn" type="primary" size="large" @click="submitForm">注册</el-button>
        <p class="login-text">
          已有账号，<el-link type="primary" @click="$router.push('/login')">立即登录</el-link>
        </p>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { register } from '@/api/user';

interface RegisterParams {
  username: string;
  password: string;
  confirmPassword: string;
}

const router = useRouter();
const param = reactive<RegisterParams>({ username: '', password: '', confirmPassword: '' });
const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请输入确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== param.password) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur',
    },
  ],
};
const registerForm = ref<FormInstance>();

const submitForm = async () => {
  if (!registerForm.value) return;
  registerForm.value.validate(async (valid: boolean) => {
    if (valid) {
      try {
        // 仅发送username和password给后端
        const response = await register({ username: param.username, password: param.password });
        ElMessage.success(response.data?.message || '注册成功，请登录');
        router.push('/login');
      } catch (error: any) {
        const message = error.response?.data?.message || '注册失败';
        ElMessage.error(message);
      }
    }
  });
};
</script>

<style scoped>
.login-bg {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100vh;
  background: url(../../assets/img/login-bg.jpg) center/cover no-repeat;
}
.login-header {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 40px;
}
.logo {
  width: 35px;
}
.login-title {
  font-size: 22px;
  color: #333;
  font-weight: bold;
}
.login-container {
  width: 450px;
  border-radius: 5px;
  background: #fff;
  padding: 40px 50px 50px;
  box-sizing: border-box;
}
.login-btn {
  display: block;
  width: 100%;
}
.login-text {
  display: flex;
  align-items: center;
  margin-top: 20px;
  font-size: 14px;
  color: #787878;
}
</style>
