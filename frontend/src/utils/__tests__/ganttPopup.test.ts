import { describe, expect, it } from 'vitest';

import { buildGanttPopupHtml, escapeHtml } from '../ganttPopup';

describe('ganttPopup', () => {
  it('escapeHtml should escape html special chars', () => {
    const input = `<script>alert("x")</script>'`;
    expect(escapeHtml(input)).toBe('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;&#39;');
  });

  it('buildGanttPopupHtml should sanitize dynamic fields', () => {
    const html = buildGanttPopupHtml({
      fullName: '<img src=x onerror=alert(1)>',
      timelineName: '<b>TL</b>',
      statusLabel: '進行中',
      start: '2026-06-02',
      end: '2026-06-08',
      progress: '50%',
      dependencyNames: '<script>dep</script>',
    });

    expect(html).not.toContain('<img');
    expect(html).not.toContain('<script>');
    expect(html).toContain('&lt;img src=x onerror=alert(1)&gt;');
    expect(html).toContain('&lt;script&gt;dep&lt;/script&gt;');
  });
});
