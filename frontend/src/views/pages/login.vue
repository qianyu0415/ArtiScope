<template>
    <div class="login-bg">
      <div class="login-container">
        <div class="login-header">
          <img class="logo mr10" src="../../assets/img/logo.svg" alt="" />
          <div class="login-title">ASCII Generator</div>
        </div>
        <el-form :model="param" :rules="rules" ref="loginForm" size="large">
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
          <div class="pwd-tips">
            <el-checkbox class="pwd-checkbox" v-model="checked" label="记住密码" />
            <el-link type="primary" @click="$router.push('/reset-pwd')">忘记密码</el-link>
          </div>
          <el-button class="login-btn" type="primary" size="large" @click="submitForm">登录</el-button>
          <p class="login-text">
            没有账号？<el-link type="primary" @click="$router.push('/register')">立即注册</el-link>
          </p>
        </el-form>
      </div>
    </div>
</template>
  
  <script setup lang="ts">
  import { ref, reactive } from 'vue';
  import { useRouter } from 'vue-router';
  import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
  import { login } from '@/api/user';
  import { usePermissStore } from '@/store/permiss';
  
  interface LoginInfo {
    username: string;
    password: string;
  }
  
  const lgStr = localStorage.getItem('login-param');
  const defParam = lgStr ? JSON.parse(lgStr) : null;
  const checked = ref(lgStr ? true : false);
  const router = useRouter();
  const param = reactive<LoginInfo>({
    username: defParam?.username || '',
    password: defParam?.password || '',
  });
  const rules: FormRules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  };
  const loginForm = ref<FormInstance>();
  const permiss = usePermissStore();
  
  const submitForm = async () => {
    if (!loginForm.value) return;
    loginForm.value.validate(async (valid: boolean) => {
      if (valid) {
        try {
          const response = await login(param);
          localStorage.setItem('vuems_name', param.username);
          localStorage.setItem('user_id', response.data.user_id.toString());
          const keys = permiss.defaultList[param.username === 'admin' ? 'admin' : 'user'];
          permiss.handleSet(keys);
          if (checked.value) {
            localStorage.setItem('login-param', JSON.stringify(param));
          } else {
            localStorage.removeItem('login-param');
          }
          ElMessage.success('登录成功');
          router.push('/');
        } catch (error: any) {
          const message = error.response?.data?.message || '登录失败';
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
  .pwd-tips {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    margin: -10px 0 10px;
    color: #787878;
  }
  .pwd-checkbox {
    height: auto;
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