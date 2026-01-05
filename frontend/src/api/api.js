// frontend/src/api/api.js
import axios from 'axios';
import { recreateSocket } from './sockets';

const rawBase = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';
const baseURL = rawBase.replace(/\/$/, '');

const api = axios.create({
  baseURL: baseURL,
});


api.interceptors.request.use(
  (config) => {
    // Get the latest token from storage
    const token = localStorage.getItem('access_token');
    
    // If the token exists, add it to the Authorization header
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
    response => response,
    async (error) =>{
        const originalRequest = error.config;
    // Defensive: ensure we have a response object
    const status = error.response?.status;

    if (status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${baseURL}/auth/refresh`, {}, {
          headers: { Authorization: `Bearer ${refreshToken}` }
        });
        if (response.status === 200) {
          const newAccessToken = response.data.access_token;
          localStorage.setItem('access_token', newAccessToken);
          api.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
          // recreate socket so it uses the refreshed access token
          try { recreateSocket(); } catch (e) { /* ignore */ }
          return api(originalRequest);
        }
      } catch (err) {
        // refresh failed: clear stored auth and force navigation to login
        try { localStorage.removeItem('access_token'); } catch {}
        try { localStorage.removeItem('refresh_token'); } catch {}
        try { localStorage.removeItem('username'); } catch {}
        try { localStorage.removeItem('user_id'); } catch {}
        // Redirect to login to prompt user to re-authenticate
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(err);
      }
    }

    return Promise.reject(error);
    }
)

export default api;