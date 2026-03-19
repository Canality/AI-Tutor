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
  // 发送问题，获取解答
  ask: async (message) => {
    return request('/chat/ask', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
  
  // 流式获取解答 (SSE)，支持图片上传
  askStream: async (message, imageFile, onMessage, onError) => {
    const url = `${API_BASE_URL}/api/chat/ask-stream`;
    const token = localStorage.getItem('token');
    
    // HTML实体解码函数
    const decodeHtmlEntities = (text) => {
      const txt = document.createElement('textarea');
      txt.innerHTML = text;
      return txt.value;
    };
    
    try {
      const formData = new FormData();
      formData.append('question', message);
      if (imageFile) {
        formData.append('image', imageFile);
      }
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('请求失败');
      }
      
      const reader = response.body.getReader();
      let accumulatedData = '';
      let lastUpdateTime = Date.now();
      const updateInterval = 100; // 每100ms更新一次
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          // 处理最后一批数据
          if (accumulatedData) {
            const decodedData = decodeHtmlEntities(accumulatedData);
            onMessage(decodedData);
          }
          break;
        }
        
        const chunk = new TextDecoder('utf-8').decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6);
            if (data) {
              accumulatedData += data;
              
              // 定期更新，避免过于频繁的渲染
              const currentTime = Date.now();
              if (currentTime - lastUpdateTime >= updateInterval) {
                const decodedData = decodeHtmlEntities(accumulatedData);
                onMessage(decodedData);
                lastUpdateTime = currentTime;
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('SSE 请求错误:', error);
      onError(error);
    }
  },
};

// 学生画像相关 API
export const profileAPI = {
  // 获取学生画像
  getProfile: async () => {
    return request('/profile');
  },
  
  // 更新学生画像
  updateProfile: async (profileData) => {
    return request('/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },
};

// 练习题相关 API
export const exercisesAPI = {
  // 获取推荐练习题
  getRecommendations: async () => {
    return request('/exercises/recommend');
  },
  
  // 获取学习计划
  getPlan: async () => {
    return request('/exercises/plan');
  },
};

// 上传相关 API
export const uploadAPI = {
  // 上传图片题目
  uploadImage: async (imageFile) => {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    return request('/upload/image', {
      method: 'POST',
      headers: {
        // 不需要设置 Content-Type，浏览器会自动设置
        ...(localStorage.getItem('token') ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` } : {}),
      },
      body: formData,
    });
  },
};

// 导出默认对象
export default {
  auth: authAPI,
  chat: chatAPI,
  profile: profileAPI,
  exercises: exercisesAPI,
  upload: uploadAPI,
};