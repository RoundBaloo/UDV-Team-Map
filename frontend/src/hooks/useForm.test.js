// src/hooks/useForm.test.js
import React from 'react';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { useForm } from './useForm';

// Простая validate-функция для тестов
const validate = (values) => {
  const errors = {};
  if ('name' in values) {
    if (!values.name || values.name.toString().trim() === '') errors.name = 'Name required';
    else errors.name = '';
  }
  if ('email' in values) {
    if (!values.email || !values.email.toString().includes('@')) errors.email = 'Invalid email';
    else errors.email = '';
  }
  return errors;
};

// Тестовый компонент: обёртка вокруг useForm, предоставляет кнопки для действий и отображение состояния
function TestComponent({ initialValues, options = {} }) {
  const form = useForm(initialValues, options);

  return (
    <div>
      <div data-testid="values">{JSON.stringify(form.values)}</div>
      <div data-testid="errors">{JSON.stringify(form.errors)}</div>
      <div data-testid="touched">{JSON.stringify(form.touched)}</div>
      <div data-testid="submitting">{String(form.submitting)}</div>
      <div data-testid="isValid">{String(form.isValid)}</div>
      <div data-testid="submitError">{/* reserved for tests that handle exception externally */}</div>

      <button data-testid="change-name-empty" onClick={() => form.handleChange('name', '')}>change-name-empty</button>
      <button data-testid="change-name-john" onClick={() => form.handleChange('name', 'John')}>change-name-john</button>
      <button data-testid="change-email-bad" onClick={() => form.handleChange('email', 'bad')}>change-email-bad</button>
      <button data-testid="set-field-value" onClick={() => form.setFieldValue('name', 'Alice')}>set-field-value</button>
      <button data-testid="set-field-error" onClick={() => form.setFieldError('email', 'err')}>set-field-error</button>

      <button data-testid="submit" onClick={async () => { try { await form.handleSubmit(); } catch (e) { /* swallow for test wrapper */ } }}>submit</button>

      <button data-testid="reset" onClick={() => form.reset()}>reset</button>
      <button data-testid="setValues" onClick={() => form.setValues({ name: 'New', email: 'a@b.com' })}>setValues</button>
    </div>
  );
}

describe('useForm hook', () => {
  test('initial state is correct', () => {
    render(<TestComponent initialValues={{ name: '', email: '' }} />);

    expect(screen.getByTestId('values').textContent).toBe(JSON.stringify({ name: '', email: '' }));
    expect(screen.getByTestId('errors').textContent).toBe(JSON.stringify({}));
    expect(screen.getByTestId('touched').textContent).toBe(JSON.stringify({}));
    expect(screen.getByTestId('submitting').textContent).toBe('false');
    expect(screen.getByTestId('isValid').textContent).toBe('true');
  });

  test('handleChange updates value, touched and errors when validateOnChange=true', async () => {
    render(<TestComponent initialValues={{ name: '', email: '' }} options={{ validate, validateOnChange: true }} />);

    // set name -> empty (should produce error)
    act(() => {
      fireEvent.click(screen.getByTestId('change-name-empty'));
    });

    await waitFor(() => {
      const errors = JSON.parse(screen.getByTestId('errors').textContent);
      const touched = JSON.parse(screen.getByTestId('touched').textContent);
      expect(touched).toHaveProperty('name', true);
      expect(errors).toHaveProperty('name', 'Name required');
      expect(screen.getByTestId('isValid').textContent).toBe('false'); // string 'false'
    });

    // change to valid value -> error cleared (empty string per validate implementation)
    act(() => {
      fireEvent.click(screen.getByTestId('change-name-john'));
    });

    await waitFor(() => {
      const errors = JSON.parse(screen.getByTestId('errors').textContent);
      // validate returns '' for no error, hook stores that value
      expect(errors.name === '' || errors.name === undefined).toBeTruthy();
      expect(screen.getByTestId('isValid').textContent).toBe('true'); // string 'true'
    });
  });

  test('setFieldValue calls handleChange and marks touched', () => {
    render(<TestComponent initialValues={{ name: '', email: '' }} options={{ validate }} />);

    act(() => {
      fireEvent.click(screen.getByTestId('set-field-value'));
    });

    const values = JSON.parse(screen.getByTestId('values').textContent);
    const touched = JSON.parse(screen.getByTestId('touched').textContent);
    expect(values.name).toBe('Alice');
    expect(touched).toHaveProperty('name', true);
  });

  test('setFieldError sets field error and affects isValid', () => {
    render(<TestComponent initialValues={{ name: '', email: '' }} />);

    act(() => {
      fireEvent.click(screen.getByTestId('set-field-error'));
    });

    const errors = JSON.parse(screen.getByTestId('errors').textContent);
    expect(errors.email).toBe('err');
    expect(screen.getByTestId('isValid').textContent).toBe('false'); // string 'false'
  });

  test('handleSubmit sets errors and touched if validation fails', async () => {
    const onSubmit = jest.fn();
    render(<TestComponent initialValues={{ name: '', email: '' }} options={{ validate, onSubmit }} />);

    await act(async () => {
      fireEvent.click(screen.getByTestId('submit'));
    });

    await waitFor(() => {
      const errors = JSON.parse(screen.getByTestId('errors').textContent);
      const touched = JSON.parse(screen.getByTestId('touched').textContent);

      expect(errors).toEqual({ name: 'Name required', email: 'Invalid email' });
      expect(Object.keys(touched).sort()).toEqual(['email', 'name']);
      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  test('handleSubmit calls onSubmit when validation passes and toggles submitting', async () => {
    const onSubmit = jest.fn().mockResolvedValue(undefined);

    render(<TestComponent initialValues={{ name: 'John', email: 'john@example.com' }} options={{ validate, onSubmit }} />);

    await act(async () => {
      fireEvent.click(screen.getByTestId('submit'));
    });

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({ name: 'John', email: 'john@example.com' });
      // submitting should be false after finally block
      expect(screen.getByTestId('submitting').textContent).toBe('false');
      // errors object for this implementation may be {} (hook doesn't fill empty strings after success)
      const errors = JSON.parse(screen.getByTestId('errors').textContent);
      expect(typeof errors === 'object').toBeTruthy();
    });
  });

  test('handleSubmit rethrows and logs error when onSubmit throws', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const onSubmit = jest.fn().mockImplementation(() => { throw new Error('submit fail'); });

    render(<TestComponent initialValues={{ name: 'John' }} options={{ onSubmit }} />);

    await act(async () => {
      fireEvent.click(screen.getByTestId('submit'));
    });

    await waitFor(() => {
      // console.error must have been called inside the hook on catch
      expect(consoleSpy).toHaveBeenCalled();
      // submitting must be set back to false
      expect(screen.getByTestId('submitting').textContent).toBe('false');
    });

    consoleSpy.mockRestore();
  });

  test('reset restores initial values and clears errors and touched', () => {
    render(<TestComponent initialValues={{ name: 'Old' }} options={{ validate }} />);

    // change
    act(() => fireEvent.click(screen.getByTestId('change-name-john')));
    expect(JSON.parse(screen.getByTestId('values').textContent).name).toBe('John');

    // reset
    act(() => fireEvent.click(screen.getByTestId('reset')));
    expect(JSON.parse(screen.getByTestId('values').textContent)).toEqual({ name: 'Old' });
    expect(JSON.parse(screen.getByTestId('errors').textContent)).toEqual({});
    expect(JSON.parse(screen.getByTestId('touched').textContent)).toEqual({});
  });

  test('setValues replaces values', () => {
    render(<TestComponent initialValues={{ name: 'Old' }} />);

    act(() => fireEvent.click(screen.getByTestId('setValues')));
    expect(JSON.parse(screen.getByTestId('values').textContent)).toEqual({ name: 'New', email: 'a@b.com' });
  });

  test('isValid reflects when errors present', () => {
    render(<TestComponent initialValues={{ name: 'John' }} />);

    expect(screen.getByTestId('isValid').textContent).toBe('true');
    act(() => fireEvent.click(screen.getByTestId('set-field-error')));
    expect(screen.getByTestId('isValid').textContent).toBe('false');
  });
});
