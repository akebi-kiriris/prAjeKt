/**
 * 全站共用格式化工具函式
 * 使用方式：import { formatDate, formatDateTime, ... } from '@/utils/formatters'
 */

// ─── 日期 ────────────────────────────────────────

/** 完整日期，如 2026/3/4 */
export const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

/** 完整日期時間，如 2026/03/04 14:30（附件上傳時間、留言時間用）*/
export const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString('zh-TW', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  });
};

/** 簡短日期時間，如 03/04 14:30（垃圾桶「刪除於」用）*/
export const formatDateTimeCompact = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString('zh-TW', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  });
};

/** 僅月日，如 03/04（垃圾桶日期範圍用）*/
export const formatDateShort = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW', {
    month: '2-digit', day: '2-digit',
  });
};

// ─── 檔案 ────────────────────────────────────────

/** 判斷是否為圖片檔案 */
export const isImageFile = (filename) =>
  /\.(jpg|jpeg|png|gif|webp)$/i.test(filename || '');

/** 依副檔名回傳 emoji 圖示 */
export const getFileIcon = (filename) => {
  if (!filename) return '📄';
  const ext = filename.split('.').pop()?.toLowerCase();
  return (
    {
      pdf: '📕', doc: '📝', docx: '📝',
      xls: '📊', xlsx: '📊', csv: '📊',
      ppt: '📋', pptx: '📋',
      zip: '🗜️', mp4: '🎬', mov: '🎬', txt: '📃',
    }[ext] || '📄'
  );
};

/** 格式化檔案大小，如 1.2 MB */
export const formatFileSize = (bytes) => {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
};
