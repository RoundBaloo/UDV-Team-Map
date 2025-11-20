import { tokenStorage } from '../storage/tokenStorage';
import { API_BASE_URL, HTTP_ERRORS, API_CONFIG } from '../../utils/constants';

class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = this.buildRequestConfig(options);

    this.logRequest(config.method, url, config);

    try {
      const response = await fetch(url, config);
      return await this.handleResponse(response, config.method, url);
    } catch (error) {
      this.logError(error);
      throw error;
    }
  }

  buildRequestConfig(options) {
    const headers = this.buildHeaders(options.headers);
    
    return {
      headers,
      ...options,
    };
  }

  buildHeaders(customHeaders = {}) {
    const headers = { ...API_CONFIG.DEFAULT_HEADERS, ...customHeaders };
    const token = tokenStorage.getToken();

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  }

  async handleResponse(response, method, url) {
    if (!response.ok) {
      throw await this.handleErrorResponse(response);
    }

    if (response.status === API_CONFIG.EMPTY_RESPONSE_STATUS) {
      return null;
    }

    const data = await response.json();
    this.logResponse(method, url, data);
    
    return data;
  }

  async handleErrorResponse(response) {
    let errorMessage = `HTTP error! status: ${response.status}`;
    
    try {
      const errorData = await response.json();
      errorMessage = this.extractErrorMessage(errorData);
    } catch {
      errorMessage = this.getHttpErrorMessage(response.status);
    }
    
    const error = new Error(errorMessage);
    error.status = response.status;
    
    return error;
  }

  extractErrorMessage(errorData) {
    if (!errorData.detail) {
      return HTTP_ERRORS.DEFAULT;
    }

    if (Array.isArray(errorData.detail)) {
      return errorData.detail.map(err => err.msg).join(', ');
    }

    return errorData.detail;
  }

  getHttpErrorMessage(status) {
    return HTTP_ERRORS[status] || HTTP_ERRORS.DEFAULT;
  }

  logRequest(method, url, config) {
    console.log(`API Request: ${method} ${url}`, config);
  }

  logResponse(method, url, data) {
    console.log(`API Response: ${method} ${url}`, data);
  }

  logError(error) {
    console.error('API request failed:', error);
  }

  async get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  async post(endpoint, data = {}, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async patch(endpoint, data = {}, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH', 
      body: JSON.stringify(data),
    });
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();