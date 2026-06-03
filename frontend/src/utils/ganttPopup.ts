const escapeMap: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

export const escapeHtml = (value: string): string => {
  return value.replace(/[&<>"']/g, (char) => escapeMap[char] ?? char);
};

export interface GanttPopupPayload {
  fullName: string;
  timelineName: string;
  statusLabel: string;
  start: string;
  end: string;
  progress: string;
  dependencyNames: string;
}

export const buildGanttPopupHtml = (payload: GanttPopupPayload): string => {
  return `
    <div class="details-container">
      <h5>${escapeHtml(payload.fullName)}</h5>
      <p>專案：${escapeHtml(payload.timelineName)}</p>
      <p>狀態：${escapeHtml(payload.statusLabel)}</p>
      <p>日期：${escapeHtml(payload.start)} ~ ${escapeHtml(payload.end)}</p>
      <p>進度：${escapeHtml(payload.progress)}</p>
      <p>依賴：${escapeHtml(payload.dependencyNames)}</p>
    </div>
  `;
};
