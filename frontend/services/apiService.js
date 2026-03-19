// API 服务层，用于与后端进行通信

const API_BASE_URL = 'http://localhost:8000'; // 后端服务地址

// 通用请求方法
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}/api${endpoint}`;
  
  // 设置默认请求头
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // 如果有 token，添加到请求头
  const token = localStorage.getItem('token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    // 解析响应数据
    const data = await response.json();
    
    // 检查响应状态
    if (!response.ok) {
      throw new Error(data.message || '请求失败');
    }
    
    return data;
  } catch (error) {
    console.error('API 请求错误:', error);
    throw error;
  }
}

// 认证相关 API
export const authAPI = {
  // 注册
  register: async (userData) => {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },
  
  // 登录
  login: async (credentials) => {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },
  
  // 获取当前用户信息
  getCurrentUser: async () => {
    return request('/auth/me');
  },
};

// 聊天相关 API
export const chatAPI = {
  // 发送消息
  sendMessage: async (message) => {
    return request('/chat/send', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
  
  // 获取聊天历史
  getChatHistory: async () => {
    return request('/chat/history');
  },
};

// 导出默认对象
export default {
  auth: authAPI,
  chat: chatAPI,
};