declare module 'frappe-gantt' {
  export interface GanttTask {
    id: string;
    name: string;
    full_name?: string;
    start: string;
    end: string;
    progress: number;
    dependencies?: string;
    custom_class?: string;
  }

  export interface GanttDateChangedTask {
    id: string;
    name: string;
    start: Date;
    end: Date;
    progress: number;
    dependencies?: string;
    custom_class?: string;
  }

  export interface GanttOptions {
    view_mode?: 'Quarter Day' | 'Half Day' | 'Day' | 'Week' | 'Month' | 'Year';
    language?: string;
    today_button?: boolean;
    popup_on?: 'click' | 'hover';
    custom_popup_html?: (task: GanttTask) => string;
    on_click?: (task: GanttTask) => void;
    on_date_change?: (task: GanttDateChangedTask, start: Date, end: Date) => void | Promise<void>;
  }

  export default class Gantt {
    constructor(wrapper: HTMLElement | SVGElement, tasks: GanttTask[], options?: GanttOptions);
  }
}
