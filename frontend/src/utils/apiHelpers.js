export const buildEndpoint = (endpoint, params = {}) => {
  let url = endpoint;
  
  // Заменяем path parameters
  Object.keys(params).forEach(key => {
    if (url.includes(`{${key}}`)) {
      url = url.replace(`{${key}}`, params[key].toString());
    }
  });
  
  return url;
};

export const buildQueryString = (params = {}) => {
  const searchParams = new URLSearchParams();
  
  Object.keys(params).forEach(key => {
    if (params[key] !== null && params[key] !== undefined) {
      searchParams.append(key, params[key].toString());
    }
  });
  
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
};