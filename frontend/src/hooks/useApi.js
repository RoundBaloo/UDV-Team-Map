import { useState, useEffect, useRef } from 'react';

export const useApi = (apiFunction, immediate = true) => {
  const [state, setState] = useState({
    data: null,
    loading: immediate,
    error: null,
  });

  const isMounted = useRef(true);
  const executeRef = useRef();

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  const execute = async (...params) => {
    if (!isMounted.current) return;

    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const result = await apiFunction(...params);
      
      if (isMounted.current) {
        setState({ data: result, loading: false, error: null });
      }
      
      return result;
    } catch (err) {
      if (isMounted.current) {
        setState(prev => ({ 
          ...prev, 
          loading: false, 
          error: err.message || 'Произошла ошибка',
        }));
      }
      throw err;
    }
  };

  executeRef.current = execute;

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate]);

  const refetch = () => {
    executeRef.current?.();
  };

  return { 
    ...state, 
    execute, 
    refetch,
  };
};