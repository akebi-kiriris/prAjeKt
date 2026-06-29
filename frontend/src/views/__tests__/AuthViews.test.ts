import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
  login: vi.fn(),
  post: vi.fn(),
  push: vi.fn(),
}));

vi.mock('../../stores/auth', () => ({
  useAuthStore: () => ({ login: mocks.login }),
}));

vi.mock('../../services/api', () => ({
  default: { post: mocks.post },
}));

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mocks.push }),
}));

import LoginView from '../LoginView.vue';
import RegisterView from '../RegisterView.vue';

const mountOptions = {
  global: {
    stubs: {
      RouterLink: { template: '<a><slot /></a>' },
    },
  },
};

const inputByPlaceholder = (wrapper: ReturnType<typeof mount>, placeholder: string) => {
  const input = wrapper.find(`input[placeholder="${placeholder}"]`);
  if (!input.exists()) throw new Error(`找不到輸入欄位：${placeholder}`);
  return input;
};

describe('authentication views', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('redirects to home after a successful login', async () => {
    mocks.login.mockResolvedValueOnce({ success: true });
    const wrapper = mount(LoginView, mountOptions);

    await inputByPlaceholder(wrapper, '請輸入 email').setValue('user@example.com');
    await inputByPlaceholder(wrapper, '請輸入密碼').setValue('secret123');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(mocks.login).toHaveBeenCalledWith('user@example.com', 'secret123');
    expect(mocks.push).toHaveBeenCalledWith('/');
    expect(wrapper.text()).not.toContain('登入失敗');
  });

  it('renders the returned error after a failed login', async () => {
    mocks.login.mockResolvedValueOnce({ success: false, error: '帳號或密碼錯誤' });
    const wrapper = mount(LoginView, mountOptions);

    await inputByPlaceholder(wrapper, '請輸入 email').setValue('user@example.com');
    await inputByPlaceholder(wrapper, '請輸入密碼').setValue('wrong-password');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(wrapper.text()).toContain('帳號或密碼錯誤');
    expect(mocks.push).not.toHaveBeenCalled();
  });

  it('submits registration data and redirects to login after two seconds', async () => {
    vi.useFakeTimers();
    mocks.post.mockResolvedValueOnce({ data: {} });
    const wrapper = mount(RegisterView, mountOptions);

    await inputByPlaceholder(wrapper, '請輸入姓名').setValue('王小明');
    await inputByPlaceholder(wrapper, '請輸入唯一用戶名，如：john_doe').setValue('ming');
    await inputByPlaceholder(wrapper, '請輸入 email').setValue('ming@example.com');
    await inputByPlaceholder(wrapper, '請輸入電話').setValue('0912345678');
    await inputByPlaceholder(wrapper, '請輸入密碼').setValue('secret123');
    await inputByPlaceholder(wrapper, '請再次輸入密碼').setValue('secret123');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(mocks.post).toHaveBeenCalledWith('/auth/register', {
      name: '王小明',
      username: 'ming',
      email: 'ming@example.com',
      phone: '0912345678',
      password: 'secret123',
    });
    expect(wrapper.text()).toContain('註冊成功！即將跳轉到登入頁面...');
    expect(mocks.push).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(2000);
    expect(mocks.push).toHaveBeenCalledWith('/login');
  });

  it('renders the API error after registration fails', async () => {
    mocks.post.mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { error: 'Email 已被使用' } },
    });
    const wrapper = mount(RegisterView, mountOptions);

    await inputByPlaceholder(wrapper, '請輸入姓名').setValue('王小明');
    await inputByPlaceholder(wrapper, '請輸入 email').setValue('used@example.com');
    await inputByPlaceholder(wrapper, '請輸入密碼').setValue('secret123');
    await inputByPlaceholder(wrapper, '請再次輸入密碼').setValue('secret123');
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(wrapper.text()).toContain('Email 已被使用');
    expect(mocks.push).not.toHaveBeenCalled();
  });

  it.each([
    ['兩次密碼輸入不一致', 'secret123', 'different'],
    ['密碼長度至少需要 6 個字元', '12345', '12345'],
  ])('rejects invalid passwords without calling the API: %s', async (message, password, confirmation) => {
    const wrapper = mount(RegisterView, mountOptions);

    await inputByPlaceholder(wrapper, '請輸入密碼').setValue(password);
    await inputByPlaceholder(wrapper, '請再次輸入密碼').setValue(confirmation);
    await wrapper.get('form').trigger('submit');
    await flushPromises();

    expect(wrapper.text()).toContain(message);
    expect(mocks.post).not.toHaveBeenCalled();
  });
});
