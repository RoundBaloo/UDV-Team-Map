export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const APP_NAME = process.env.REACT_APP_APP_NAME || 'UDV Team Map';

export const USER_ROLES = {
  EMPLOYEE: 'employee',
  ADMIN: 'admin',
};

export const PHOTO_MODERATION_STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved', 
  REJECTED: 'rejected',
};

export const WORK_FORMATS = {
  OFFICE: 'office',
  HYBRID: 'hybrid',
  REMOTE: 'remote',
};

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  PROFILE: '/profile/:id?',
  TEAM: '/team/:id',
  ADMIN_USERS: '/admin/users',
  ADMIN_PHOTOS: '/admin/photos',
  ORG_STRUCTURE: '/structure',
};

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/auth/login',
    ME: '/api/auth/me',
  },
  EMPLOYEES: {
    LIST: '/api/employees/',
    DETAIL: '/api/employees/{employee_id}', 
    ME: '/api/employees/me',
  },
  PHOTO_MODERATION: {
    PENDING: '/api/photo-moderation/pending',
    DECISION: '/api/photo-moderation/{moderation_id}/decision',
    MY_STATUS: '/api/photo-moderation/me/status',
    REQUESTS_ME: '/api/photo-moderation/requests/me',
  },
  MEDIA: {
    INIT_UPLOAD: '/api/media/uploads/init',
    FINALIZE_UPLOAD: '/api/media/uploads/finalize',
  },
  ORG_UNITS: {
    LIST: '/api/org-units/',
    UNIT_EMPLOYEES: '/api/org-units/{org_unit_id}/employees',
  },
};

export const HTTP_ERRORS = {
  401: 'Неавторизованный доступ',
  403: 'Доступ запрещен', 
  404: 'Ресурс не найден',
  500: 'Ошибка сервера',
  DEFAULT: 'Произошла ошибка',
};

export const API_CONFIG = {
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
  },
  EMPTY_RESPONSE_STATUS: 204,
};

export const MAX_FILE_SIZE = 5 * 1024 * 1024;
export const ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/gif'];