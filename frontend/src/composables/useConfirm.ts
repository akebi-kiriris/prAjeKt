import { ref } from 'vue';

interface ConfirmOptions {
  title: string;
  message?: string;
  danger?: boolean;
}

interface ConfirmDialogState {
  title: string;
  message: string;
  danger: boolean;
  resolve: (value: boolean) => void;
}

const dialogState = ref<ConfirmDialogState | null>(null);

export function useConfirm() {
  function confirm({ title, message = '', danger = false }: ConfirmOptions): Promise<boolean> {
    return new Promise((resolve) => {
      dialogState.value = { title, message, danger, resolve };
    });
  }

  return { confirm };
}

export { dialogState };
