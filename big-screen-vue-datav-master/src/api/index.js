import axios from "axios"

// 请求基础路径

const service = axios.create({
    baseURL:"http://localhost:8000/",
    timeout:40000
})

export default service