import { tokenStorage } from '../storage/tokenStorage';
import { API_BASE_URL } from '../../utils/constants';

class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  // Базовый метод для HTTP запросов
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Добавляем токен авторизации если есть
    const token = tokenStorage.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    console.log(`API Request: ${config.method} ${url}`, config);

    try {
      const response = await fetch(url, config);
      
      // Обрабатываем ответ
      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        
        try {
          const errorData = await response.json();
          console.log('API Error response:', errorData);
          
          if (errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail.map(err => err.msg).join(', ');
            } else {
              errorMessage = errorData.detail;
            }
          }
        } catch (parseError) {
          // Если не удалось распарсить JSON, используем стандартное сообщение
          if (response.status === 401) {
            errorMessage = 'Неавторизованный доступ';
          } else if (response.status === 403) {
            errorMessage = 'Доступ запрещен';
          } else if (response.status === 404) {
            errorMessage = 'Ресурс не найден';
          } else if (response.status >= 500) {
            errorMessage = 'Ошибка сервера';
          }
        }
        
        const error = new Error(errorMessage);
        error.status = response.status;
        throw error;
      }

      // Для пустого ответа
      if (response.status === 204) {
        return null;
      }

      const data = await response.json();
      console.log(`API Response: ${config.method} ${url}`, data);
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // GET запрос
  async get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  // POST запрос  
  async post(endpoint, data = {}, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // PATCH запрос
  async patch(endpoint, data = {}, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH', 
      body: JSON.stringify(data),
    });
  }

  // DELETE запрос
  async delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

// Создаем экземпляр клиента
export const apiClient = new ApiClient();