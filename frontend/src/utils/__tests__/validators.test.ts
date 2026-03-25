import { describe, expect, it } from 'vitest';
import {
  validateRequired,
  validateEmail,
  validatePassword,
  validateConfirmPassword,
  validateDateRange,
  validateMaxLength,
} from '../validators';

describe('validators', () => {
  it('validateRequired should validate blank and pass non-blank', () => {
    expect(validateRequired('', '名稱')).toBe('名稱為必填');
    expect(validateRequired('  ', '名稱')).toBe('名稱為必填');
    expect(validateRequired('ok', '名稱')).toBeNull();
  });

  it('validateEmail should check required and format', () => {
    expect(validateEmail('')).toBe('Email 為必填');
    expect(validateEmail('abc')).toBe('Email 格式不正確');
    expect(validateEmail('a@b.com')).toBeNull();
  });

  it('validatePassword should validate all password rules', () => {
    expect(validatePassword('')).toBe('密碼為必填');
    expect(validatePassword('abc123')).toBe('密碼至少需要 8 個字元');
    expect(validatePassword('12345678')).toBe('密碼需包含英文字母');
    expect(validatePassword('abcdefgh')).toBe('密碼需包含數字');
    expect(validatePassword('abcd1234')).toBeNull();
  });

  it('validateConfirmPassword should validate empty/mismatch/match', () => {
    expect(validateConfirmPassword('abc12345', '')).toBe('請再次輸入密碼');
    expect(validateConfirmPassword('abc12345', 'abc12346')).toBe('兩次密碼輸入不一致');
    expect(validateConfirmPassword('abc12345', 'abc12345')).toBeNull();
  });

  it('validateDateRange should allow missing dates and validate order', () => {
    expect(validateDateRange(null, '2026-03-01')).toBeNull();
    expect(validateDateRange('2026-03-02', null)).toBeNull();
    expect(validateDateRange('2026-03-02', '2026-03-01')).toBe('開始日期不得晚於結束日期');
    expect(validateDateRange('2026-03-01', '2026-03-02')).toBeNull();
  });

  it('validateMaxLength should validate upper bound', () => {
    expect(validateMaxLength(null, 5, '備註')).toBeNull();
    expect(validateMaxLength('12345', 5, '備註')).toBeNull();
    expect(validateMaxLength('123456', 5, '備註')).toBe('備註不得超過 5 個字元');
  });
});
