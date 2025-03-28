import axios from "axios";

// Dummy URL is used here we need to change it later.

const axiosInstance = axios.create({
    baseURL: 'https://dev.sprout-ly.com/api',
    timeout: 5000,
    headers: {
        "Content-Type": 'application/x-www-form-urlencoded',
    }
})

export default axiosInstance;