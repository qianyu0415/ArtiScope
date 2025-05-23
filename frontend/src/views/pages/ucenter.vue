<template>
    <div>
        <div class="user-container">
            <el-card class="user-profile" shadow="hover" :body-style="{ padding: '0px' }">
                <div class="user-profile-bg"></div>
                <div class="user-avatar-wrap">
                    <el-avatar class="user-avatar" :size="120" :src="avatarImg" />
                </div>
                <div class="user-info">
                    <div class="info-icon">
                        <a href="https://github.com/qianyu0415/ArtiScope" target="_blank"><i class="el-icon-lx-github-fill"></i></a>
                        <i class="el-icon-lx-qq-fill"></i>
                        <i class="el-icon-lx-facebook-fill"></i>
                        <i class="el-icon-lx-twitter-fill"></i>
                    </div>
                </div>
                <div class="user-footer">
                    <div class="user-footer-item">
                        <el-statistic title="生成图片数量" :value="0" />
                    </div>
                    <div class="user-footer-item">
                        <el-statistic title="生成视频数量" :value="0" />
                    </div>
                </div>
            </el-card>
            <el-card
                class="user-content"
                shadow="hover"
                :body-style="{ padding: '15px 50px', height: '100%', width: '100%', boxSizing: 'border-box' }"
            >
                <el-tabs tab-position="left" v-model="activeName">
                    <el-tab-pane name="label1" label="我的头像" class="user-tabpane">
                        <div class="crop-wrap" v-if="activeName === 'label1'">
                            <vueCropper
                                ref="cropper"
                                :img="imgSrc"
                                :autoCrop="true"
                                :centerBox="true"
                                :full="true"
                                mode="contain"
                            >
                            </vueCropper>
                        </div>
                        <el-button class="crop-demo-btn" type="primary"
                            >选择图片
                            <input class="crop-input" type="file" name="image" accept="image/*" @change="setImage" />
                        </el-button>
                        <el-button type="success" @click="saveAvatar">上传并保存</el-button>
                    </el-tab-pane>
                    <el-tab-pane name="label2" label="修改密码" class="user-tabpane">
                        <el-form class="w500" label-position="top">
                            <el-form-item label="旧密码：">
                                <el-input type="password" v-model="form.old"></el-input>
                            </el-form-item>
                            <el-form-item label="新密码：">
                                <el-input type="password" v-model="form.new"></el-input>
                            </el-form-item>
                            <el-form-item label="确认新密码：">
                                <el-input type="password" v-model="form.new1"></el-input>
                            </el-form-item>
                            <el-form-item>
                                <el-button type="primary" @click="onSubmit">保存</el-button>
                            </el-form-item>
                        </el-form>
                    </el-tab-pane>
                    <el-tab-pane name="label3" label="历史生成" class="user-tabpane">
                        <TabsComp />
                    </el-tab-pane>
                </el-tabs>
            </el-card>
        </div>
    </div>
</template>

<script setup lang="ts" name="ucenter">
import { reactive, ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { VueCropper } from 'vue-cropper';
import 'vue-cropper/dist/index.css';
import avatar from '@/assets/img/img.jpg';
import TabsComp from '../element/tabs.vue';

const name = localStorage.getItem('vuems_name');
const form = reactive({
    new1: '',
    new: '',
    old: '',
});
const onSubmit = () => {};

const activeName = ref('label1');

const avatarImg = ref(localStorage.getItem('userAvatar') || avatar);
const imgSrc = ref(avatar);
const cropImg = ref('');
const cropper = ref<InstanceType<typeof VueCropper>>();

// 可选：添加上传到服务器的函数
const uploadAvatarToServer = (imageData: string) => {
    // 这里添加将头像上传到服务器的逻辑
    // 例如使用fetch或axios发送POST请求
    console.log('上传头像到服务器的代码将在这里实现');
    
    // 示例代码（需要替换为实际的API端点）
    /*
    fetch('/api/user/avatar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            avatar: imageData,
            userId: localStorage.getItem('userId') // 假设有用户ID存储
        }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('头像上传成功:', data);
    })
    .catch(error => {
        console.error('头像上传失败:', error);
        ElMessage.error('头像上传到服务器失败');
    });
    */
};

const setImage = (e: Event) => {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file || !file.type.includes('image/')) {
        ElMessage.error('请选择有效的图片文件');
        return;
    }
    console.log('File selected:', file.name, file.type);
    const reader = new FileReader();
    reader.onload = (event) => {
        if (event.target?.result) {
            imgSrc.value = event.target.result as string;
            console.log('imgSrc updated:', imgSrc.value);
        } else {
            console.error('FileReader result is empty');
        }
    };
    reader.readAsDataURL(file);
    target.value = '';
};

const saveAvatar = () => {
    console.log('saveAvatar called, cropper:', cropper.value);
    if (!cropper.value) {
        ElMessage.error('裁剪组件未初始化，请重试');
        return;
    }

    // 正确使用getCropData方法，传入回调函数
    cropper.value.getCropData((data: string) => {
        if (data) {
            // 更新UI上的头像
            avatarImg.value = data;
            cropImg.value = data;
            
            // 保存到localStorage中实现持久化
            localStorage.setItem('userAvatar', data);
            
            // 这里也可以添加上传到服务器的代码
            // uploadAvatarToServer(data);
            
            ElMessage.success('头像更新成功');
        } else {
            ElMessage.error('获取裁剪数据失败');
        }
    });
};

onMounted(() => {
    console.log('Cropper instance available:', !!cropper.value);
    
    // 检查localStorage中是否有保存的头像
    const savedAvatar = localStorage.getItem('userAvatar');
    if (savedAvatar) {
        avatarImg.value = savedAvatar;
    }
});
</script>

<style scoped>
.user-container {
    display: flex;
}

.user-profile {
    position: relative;
}

.user-profile-bg {
    width: 100%;
    height: 200px;
    background-image: url('../../assets/img/login-bg.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

.user-profile {
    width: 500px;
    margin-right: 20px;
    flex: 0 0 auto;
    align-self: flex-start;
}

.user-avatar-wrap {
    position: absolute;
    top: 135px;
    width: 100%;
    text-align: center;
}

.user-avatar {
    border: 5px solid #fff;
    border-radius: 50%;
    overflow: hidden;
    box-shadow: 0 7px 12px 0 rgba(62, 57, 107, 0.16);
}

.user-info {
    text-align: center;
    padding: 80px 0 30px;
}

.info-name {
    margin: 0 0 20px;
    font-size: 22px;
    font-weight: 500;
    color: #373a3c;
}

.info-desc {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 5px;
}

.info-desc,
.info-desc a {
    font-size: 18px;
    color: #55595c;
}

.info-icon {
    margin-top: 10px;
}

.info-icon i {
    font-size: 30px;
    margin: 0 10px;
    color: #343434;
}

.user-content {
    flex: 1.1;
}

.user-tabpane {
    padding: 10px 20px;
}

.crop-wrap {
    width: 600px;
    height: 350px;
    margin-bottom: 20px;
}

.crop-demo-btn {
    position: relative;
}

.crop-input {
    position: absolute;
    width: 100px;
    height: 40px;
    left: 0;
    top: 0;
    opacity: 0;
    cursor: pointer;
}

.w500 {
    width: 500px;
}

.user-footer {
    display: flex;
    border-top: 1px solid rgba(83, 70, 134, 0.1);
}

.user-footer-item {
    padding: 20px 0;
    width: 50%;
    text-align: center;
}

.user-footer > div + div {
    border-left: 1px solid rgba(83, 70, 134, 0.1);
}
</style>

<style>
.el-tabs.el-tabs--left {
    height: 100%;
}
</style>