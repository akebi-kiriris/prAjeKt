import type { Task } from './task';
import type { Timeline } from './timeline';

export type ViewMode = 'card' | 'kanban' | 'timeline' | 'calendar' | 'gantt';

export interface SidebarNavItem {
  path: string;
  icon: string;
  text: string;
}

export interface TimelineForm {
  name: string;
  start_date: string;
  end_date: string;
  remark: string;
}

export interface TodoForm {
  title: string;
  content: string;
  deadline: string;
}

export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm {
  name: string;
  username: string;
  email: string;
  phone: string;
  password: string;
}

export interface NavCard {
  path: string;
  icon: string;
  title: string;
  description: string;
}

export interface UpcomingItem {
  id: number;
  type: 'task' | 'timeline';
  name: string;
  is_overdue: boolean;
  end_date: string;
}

export interface UpcomingTaskRaw extends Omit<UpcomingItem, 'id'> {
  task_id: number;
}

export interface TimelineDetailDialogProps {
  selectedTimeline: Timeline | null;
  timelineTasks: Task[];
  apiBaseUrl: string;
}

export interface TimelineViewModesProps {
  viewMode: ViewMode;
  timelines: Timeline[];
  sortedTimelines: Timeline[];
  allTasks: Task[];
}
