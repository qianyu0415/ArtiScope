import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://127.0.0.1:8088',
  withCredentials: true, // 允许携带Cookie
});

export const register = (data) => instance.post('/register', data, {
  headers: { 'Content-Type': 'application/json' },
});

export const login = (data) => instance.post('/login', data, {
  headers: { 'Content-Type': 'application/json' },
});