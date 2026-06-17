export type NotificationType =
  | 'task_assigned'
  | 'timeline_invited'
  | 'comment'
  | 'deadline'
  | 'mention';

export interface Notification {
  id: number;
  type: NotificationType;
  title: string;
  content: string | null;
  link: string | null;
  is_read: boolean;
  user_id?: number;
  created_at: string | null;
}
