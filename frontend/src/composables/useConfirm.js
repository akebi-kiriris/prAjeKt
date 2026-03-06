import { ref } from 'vue';

// 這份狀態是模組層級的 singleton — 整個 app 共用同一個 Modal 實例
const dialogState = ref(null);
// dialogState 的結構：
// {
//   title: string,
//   message?: string,
//   danger: boolean,
//   resolve: (value: boolean) => void
// }

/**
 * useConfirm — 全域確認對話框 composable
 *
 * 用法（在任何 <script setup> 裡）：
 *   import { useConfirm } from '@/composables/useConfirm'
 *   const { confirm } = useConfirm()
 *
 *   // 需要加上 async 函式
 *   const ok = await confirm({ title: '確定刪除？', danger: true })
 *   if (!ok) return
 */
export function useConfirm() {
  /**
   * 顯示確認 Modal，回傳 Promise<boolean>
   * @param {object} options
   * @param {string}  options.title   主標題（必填）
   * @param {string} [options.message] 補充說明（選填）
   * @param {boolean}[options.danger]  危險操作：確認按鈕顯示紅色（預設 false）
   */
  function confirm({ title, message = '', danger = false }) {
    return new Promise((resolve) => {
      dialogState.value = { title, message, danger, resolve };
    });
  }

  return { confirm };
}

// 給 ConfirmDialog.vue 內部使用 — 讀取 / 清除狀態
export { dialogState };
