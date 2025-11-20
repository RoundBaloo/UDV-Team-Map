import { useState, useEffect, useCallback } from 'react';

const STORAGE_ERRORS = {
  read: key => `Error reading localStorage key "${key}"`,
  write: key => `Error setting localStorage key "${key}"`,
  remove: key => `Error removing localStorage key "${key}"`,
};

export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    return getInitialValue(key, initialValue);
  });

  const setValue = useCallback(value => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      
      if (valueToStore === undefined) {
        window.localStorage.removeItem(key);
      } else {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error(STORAGE_ERRORS.write(key), error);
    }
  }, [key, storedValue]);

  const removeValue = useCallback(() => {
    try {
      setStoredValue(undefined);
      window.localStorage.removeItem(key);
    } catch (error) {
      console.error(STORAGE_ERRORS.remove(key), error);
    }
  }, [key]);

  useEffect(() => {
    const handleStorageChange = event => {
      if (event.key === key && event.storageArea === window.localStorage) {
        try {
          const newValue = event.newValue ? JSON.parse(event.newValue) : initialValue;
          setStoredValue(newValue);
        } catch (error) {
          console.error(STORAGE_ERRORS.read(key), error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
};

const getInitialValue = (key, initialValue) => {
  if (typeof window === 'undefined') {
    return initialValue;
  }

  try {
    const item = window.localStorage.getItem(key);
    return item ? JSON.parse(item) : initialValue;
  } catch (error) {
    console.error(STORAGE_ERRORS.read(key), error);
    return initialValue;
  }
};