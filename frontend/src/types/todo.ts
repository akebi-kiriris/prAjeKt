export interface Todo {
  id: number;
  title: string;
  content: string;
  type: string | null;
  deadline: string | null;
  completed: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface CreateTodoPayload {
  title: string;
  content?: string;
  type?: string | null;
  deadline?: string;
  priority?: number;
}

export type UpdateTodoPayload = Partial<Pick<
  Todo,
  | 'title'
  | 'content'
  | 'type'
  | 'deadline'
  | 'priority'
  | 'completed'
>>;
