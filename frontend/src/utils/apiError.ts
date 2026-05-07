import { isAxiosError } from 'axios';
import type { ApiErrorPayload } from '../types';

const ERROR_CODE_MESSAGE_MAP: Record<string, string> = {
  BAD_REQUEST: '請求內容有誤，請檢查後再試',
  VALIDATION_ERROR: '輸入資料驗證失敗，請檢查欄位',
  UNAUTHORIZED: '登入已失效，請重新登入',
  FORBIDDEN: '你沒有權限執行此操作',
  NOT_FOUND: '找不到指定資源',
  CONFLICT: '資料衝突，請重新整理後再試',
  UNPROCESSABLE_ENTITY: '資料格式正確，但內容無法處理',
  RATE_LIMITED: '操作太頻繁，請稍後再試',
  INTERNAL_ERROR: '伺服器發生錯誤，請稍後再試',
  SERVICE_UNAVAILABLE: '服務暫時不可用，請稍後再試',
  UNKNOWN_ERROR: '發生未知錯誤，請稍後再試',
};

export const mapErrorCodeToMessage = (errorCode?: string): string | undefined => {
  if (!errorCode) return undefined;
  return ERROR_CODE_MESSAGE_MAP[errorCode];
};

export const getApiErrorMessage = (error: unknown, fallback: string): string => {
  if (isAxiosError<ApiErrorPayload>(error)) {
    if (error.code === 'ECONNABORTED') {
      return '請求逾時，請稍後再試';
    }
    if (!error.response) {
      return error.message || '網路連線異常，請稍後再試';
    }
    const payload = error.response.data;
    const mapped = mapErrorCodeToMessage(payload?.error_code);
    return payload?.error || mapped || fallback;
  }
  return fallback;
};

export const getApiErrorCode = (error: unknown): string | undefined => {
  if (!isAxiosError<ApiErrorPayload>(error)) return undefined;
  return error.response?.data?.error_code;
};

export const shouldRedirectToLogin = (errorCode?: string): boolean => errorCode === 'UNAUTHORIZED';
