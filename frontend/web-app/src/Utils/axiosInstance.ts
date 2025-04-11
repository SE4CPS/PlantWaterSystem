import axios from "axios";

const axiosInstance = axios.create({
    baseURL: 'https://dev.sprout-ly.com/api',
    timeout: 5000,
    headers: {
        "Content-Type": 'application/x-www-form-urlencoded',
    }
})

axiosInstance.interceptors.request.use(
    config => {
        config.headers.Authorization = `Bearer ${localStorage.getItem('access_token')}`;
        switch (config.url) {
            case '/plant/data':
                config.headers["Content-Type"] = 'application/json';
                break;
            default:
                config.headers["Content-Type"] = 'application/x-www-form-urlencoded';
                break;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
)

export default axiosInstance;
