import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://127.0.0.1:8088', // 替换为实际后端域名
  withCredentials: true,
});

export const uploadImage = (formData) => instance.post('/log_image_process', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});

export const getImageLogs = (params) => instance.get('/image_process_logs', { params });