import axios from "axios";

// Dummy URL is used here we need to change it later.

const axiosInstance = axios.create({
    baseURL: 'http://sproutly.com/api',
    timeout: 5000,
    headers: {
        "Content-Type": 'application/json',
    }
})

export default axiosInstance;