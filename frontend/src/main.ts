import { createApp } from 'vue';
import { createPinia } from 'pinia';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import App from './App.vue';
import router from './router';
import { usePermissStore } from './store/permiss';
import 'element-plus/dist/index.css';
import './assets/css/icon.css';
import { ElConfigProvider } from 'element-plus';
import zhCn from 'element-plus/es/locale/lang/zh-cn';
import axios from 'axios';
import './assets/css/main.css';

const app = createApp(App);
app.use(createPinia());
app.use(router);

// 配置 axios 拦截器处理 401 未授权
axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        router.push('/403');
      }
      return Promise.reject(error);
    }
  );

// 注册elementplus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
}
// 自定义权限指令
const permiss = usePermissStore();
app.directive('permiss', {
    mounted(el, binding) {
        if (binding.value && !permiss.key.includes(String(binding.value))) {
            el['hidden'] = true;
        }
    },
});

app.use(router);
app.use(ElConfigProvider, { locale: zhCn });
app.mount('#app');
