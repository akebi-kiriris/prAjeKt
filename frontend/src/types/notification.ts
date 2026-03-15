export type NotificationType =
  | 'task_assigned'
  | 'timeline_invited'
  | 'comment'
  | 'deadline'
  | 'mention';

export interface Notification {
  id: number;
  user_id: number;
  type: NotificationType;
  title: string;
  content: string | null;
  link: string | null;
  is_read: boolean;
  created_at: string;
}
