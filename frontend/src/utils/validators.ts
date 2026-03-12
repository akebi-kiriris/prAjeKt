/**
 * 全站共用表單驗證工具函式
 * 回傳 string 代表錯誤訊息，回傳 null 代表驗證通過
 * 使用方式：import { validateEmail, validateRequired, ... } from '@/utils/validators'
 */

/** 必填欄位 */
export const validateRequired = (value: string | null | undefined, label = '此欄位'): string | null => {
  if (!value || !value.trim()) return `${label}為必填`;
  return null;
};

/** Email 格式 */
export const validateEmail = (value: string | null | undefined): string | null => {
  if (!value || !value.trim()) return 'Email 為必填';
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(value.trim())) return 'Email 格式不正確';
  return null;
};

/** 密碼強度（至少 8 碼，含英文和數字）*/
export const validatePassword = (value: string | null | undefined): string | null => {
  if (!value) return '密碼為必填';
  if (value.length < 8) return '密碼至少需要 8 個字元';
  if (!/[a-zA-Z]/.test(value)) return '密碼需包含英文字母';
  if (!/[0-9]/.test(value)) return '密碼需包含數字';
  return null;
};

/** 確認密碼 */
export const validateConfirmPassword = (password: string, confirm: string): string | null => {
  if (!confirm) return '請再次輸入密碼';
  if (password !== confirm) return '兩次密碼輸入不一致';
  return null;
};

/** 日期範圍（start 不得晚於 end）*/
export const validateDateRange = (
  startDate: string | null | undefined,
  endDate: string | null | undefined,
): string | null => {
  if (!startDate || !endDate) return null;
  if (new Date(startDate) > new Date(endDate)) return '開始日期不得晚於結束日期';
  return null;
};

/** 字串長度上限 */
export const validateMaxLength = (
  value: string | null | undefined,
  max: number,
  label = '此欄位',
): string | null => {
  if (!value) return null;
  if (value.length > max) return `${label}不得超過 ${max} 個字元`;
  return null;
};
