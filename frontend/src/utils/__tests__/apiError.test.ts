import axios, { AxiosError } from 'axios';
import { describe, expect, it } from 'vitest';

import {
  getApiErrorCode,
  getApiErrorMessage,
  mapErrorCodeToMessage,
  shouldRedirectToLogin,
} from '../apiError';

const makeAxiosError = (
  data?: unknown,
  options: { code?: string; message?: string; hasResponse?: boolean } = {},
) => {
  const error = new AxiosError(
    options.message || 'Request failed',
    options.code,
    undefined,
    {},
    options.hasResponse === false
      ? undefined
      : {
          data,
          status: 400,
          statusText: 'Bad Request',
          headers: {},
          config: {},
        } as never,
  );
  return error;
};

describe('apiError helpers', () => {
  it('maps known error codes to user-facing messages', () => {
    expect(mapErrorCodeToMessage('VALIDATION_ERROR')).toBe('輸入資料驗證失敗，請檢查欄位');
    expect(mapErrorCodeToMessage('UNAUTHORIZED')).toBe('登入已失效，請重新登入');
    expect(mapErrorCodeToMessage()).toBeUndefined();
    expect(mapErrorCodeToMessage('DOES_NOT_EXIST')).toBeUndefined();
  });

  it('prefers explicit API error text over mapped error code text', () => {
    const error = makeAxiosError({
      error: '後端提供的具體錯誤',
      error_code: 'VALIDATION_ERROR',
    });

    expect(getApiErrorMessage(error, '預設錯誤')).toBe('後端提供的具體錯誤');
  });

  it('falls back to mapped message, timeout message, network message and default text', () => {
    expect(
      getApiErrorMessage(makeAxiosError({ error_code: 'FORBIDDEN' }), '預設錯誤'),
    ).toBe('你沒有權限執行此操作');
    expect(
      getApiErrorMessage(makeAxiosError(undefined, { code: 'ECONNABORTED' }), '預設錯誤'),
    ).toBe('請求逾時，請稍後再試');
    expect(
      getApiErrorMessage(
        makeAxiosError(undefined, {
          hasResponse: false,
          message: 'Network Error',
        }),
        '預設錯誤',
      ),
    ).toBe('Network Error');
    expect(getApiErrorMessage(new Error('plain error'), '預設錯誤')).toBe('預設錯誤');
  });

  it('extracts API error codes only from Axios errors', () => {
    expect(getApiErrorCode(makeAxiosError({ error_code: 'UNAUTHORIZED' }))).toBe('UNAUTHORIZED');
    expect(getApiErrorCode(new Error('plain error'))).toBeUndefined();
  });

  it('identifies errors that should redirect to login', () => {
    expect(shouldRedirectToLogin('UNAUTHORIZED')).toBe(true);
    expect(shouldRedirectToLogin('FORBIDDEN')).toBe(false);
    expect(shouldRedirectToLogin()).toBe(false);
  });

  it('treats real Axios errors without response as network failures', () => {
    const error = axios.AxiosError.from(new Error('socket hang up'));

    expect(getApiErrorMessage(error, '預設錯誤')).toBe('socket hang up');
  });
});
