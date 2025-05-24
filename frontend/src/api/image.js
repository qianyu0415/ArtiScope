import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://127.0.0.1:8088',
  withCredentials: true,
});

export const uploadImage = (formData) => instance.post('/log_image_process', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});

export const getImageLogs = (params) => instance.get('/image_process_logs', { params });

export const uploadVideo = (formData) => instance.post('/log_video_process', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
});

export const getVideoLogs = (params) => instance.get('/video_process_logs', { params });

export const generateImageFromText = (prompt) => instance.post('/generate_image_from_text', { prompt });

export const getTextToImageLogs = (params) => instance.get('/text_to_image_logs', { params });