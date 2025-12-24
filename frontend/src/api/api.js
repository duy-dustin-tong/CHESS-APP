// frontend/src/api/api.js
import axios from 'axios';

const baseURL = 'http://127.0.0.1:5000/';

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

        if (error.response.status === 401 && !originalRequest._retry) {
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
                    originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
                    return api(originalRequest);
                }
            }
            catch (err) {
                return Promise.reject(err);
            }

            
        }
        return Promise.reject(error); 
    }
)

export default api;