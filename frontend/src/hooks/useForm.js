import { useState, useCallback } from 'react';

export const useForm = (initialValues, options = {}) => {
  const {
    onSubmit,
    validate,
    validateOnChange = true,
  } = options;

  const [state, setState] = useState({
    values: initialValues,
    errors: {},
    submitting: false,
    touched: {},
  });

  const validateField = useCallback((name, value) => {
    if (!validate) return '';

    const fieldErrors = validate({ [name]: value });
    return fieldErrors[name] || '';
  }, [validate]);

  const validateForm = useCallback(values => {
    if (!validate) return {};
    return validate(values) || {};
  }, [validate]);

  const handleChange = useCallback((name, value) => {
    setState(prev => {
      const newValues = { ...prev.values, [name]: value };
      const newErrors = { ...prev.errors };
      const newTouched = { ...prev.touched, [name]: true };

      if (validateOnChange) {
        newErrors[name] = validateField(name, value);
      }

      return {
        ...prev,
        values: newValues,
        errors: newErrors,
        touched: newTouched,
      };
    });
  }, [validateField, validateOnChange]);

  const setFieldValue = useCallback((name, value) => {
    handleChange(name, value);
  }, [handleChange]);

  const setFieldError = useCallback((name, error) => {
    setState(prev => ({
      ...prev,
      errors: { ...prev.errors, [name]: error },
    }));
  }, []);

  const handleSubmit = async e => {
    if (e) e.preventDefault();

    const formErrors = validateForm(state.values);
    const hasErrors = Object.values(formErrors).some(error => error);

    if (hasErrors) {
      setState(prev => ({
        ...prev,
        errors: formErrors,
        touched: Object.keys(prev.values).reduce((acc, key) => ({
          ...acc,
          [key]: true,
        }), {}),
      }));
      return;
    }

    setState(prev => ({ ...prev, submitting: true }));

    try {
      await onSubmit?.(state.values);
    } catch (error) {
      console.error('Form submission error:', error);
      throw error;
    } finally {
      setState(prev => ({ ...prev, submitting: false }));
    }
  };

  const reset = useCallback(() => {
    setState({
      values: initialValues,
      errors: {},
      submitting: false,
      touched: {},
    });
  }, [initialValues]);

  const setValues = useCallback(newValues => {
    setState(prev => ({ ...prev, values: newValues }));
  }, []);

  return {
    values: state.values,
    errors: state.errors,
    submitting: state.submitting,
    touched: state.touched,
    handleChange,
    handleSubmit,
    setFieldValue,
    setFieldError,
    setValues,
    reset,
    isValid: Object.values(state.errors).every(error => !error),
  };
};