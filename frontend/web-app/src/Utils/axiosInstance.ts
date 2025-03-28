import axios from "axios";


const access_token = localStorage.getItem('access_token')

const axiosInstance = axios.create({
    baseURL: 'https://dev.sprout-ly.com/api',
    timeout: 5000,
    headers: {
        "Content-Type": 'application/x-www-form-urlencoded',
        Authorization: `Bearer ${access_token}`
    }
})

export default axiosInstance;