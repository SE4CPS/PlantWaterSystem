import axios from "axios";

const axiosInstance = axios.create({
    baseURL: 'http://sproutly.com/api',
    timeout: 5000,
    headers: {
        "Content-Type": 'application/x-www-form-urlencoded',
    }
})

axiosInstance.interceptors.request.use(
    config => {
        config.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
        return config;
    },
    error => {
        return Promise.reject(error);
    }
)

export default axiosInstance;