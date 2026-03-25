import { describe, expect, it } from 'vitest';
import {
  formatDate,
  formatDateTime,
  formatDateTimeCompact,
  formatDateShort,
  isImageFile,
  getFileIcon,
  formatFileSize,
} from '../formatters';

describe('formatters', () => {
  it('date formatters should return empty string for empty input', () => {
    expect(formatDate('')).toBe('');
    expect(formatDateTime(undefined)).toBe('');
    expect(formatDateTimeCompact(null)).toBe('');
    expect(formatDateShort('')).toBe('');
  });

  it('date formatters should output localized date-like text', () => {
    const date = '2026-03-04T14:30:00';

    expect(formatDate(date)).toContain('2026');
    expect(formatDateTime(date)).toContain('2026');
    expect(formatDateTimeCompact(date)).toMatch(/03\/04|3\/4/);
    expect(formatDateShort(date)).toMatch(/03\/04|3\/4/);
  });

  it('isImageFile should detect common image extensions', () => {
    expect(isImageFile('a.jpg')).toBe(true);
    expect(isImageFile('a.JPEG')).toBe(true);
    expect(isImageFile('a.png')).toBe(true);
    expect(isImageFile('a.txt')).toBe(false);
    expect(isImageFile(null)).toBe(false);
  });

  it('getFileIcon should map extension and fallback to default icon', () => {
    expect(getFileIcon('a.pdf')).toBe('📕');
    expect(getFileIcon('a.docx')).toBe('📝');
    expect(getFileIcon('a.xlsx')).toBe('📊');
    expect(getFileIcon('a.mov')).toBe('🎬');
    expect(getFileIcon('a.unknown')).toBe('📄');
    expect(getFileIcon(undefined)).toBe('📄');
  });

  it('formatFileSize should format bytes, KB, MB and handle zero-like values', () => {
    expect(formatFileSize(undefined)).toBe('');
    expect(formatFileSize(0)).toBe('');
    expect(formatFileSize(512)).toBe('512 B');
    expect(formatFileSize(1536)).toBe('1.5 KB');
    expect(formatFileSize(1572864)).toBe('1.5 MB');
  });
});
