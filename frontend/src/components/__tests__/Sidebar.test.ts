import { defineComponent } from 'vue';
import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import Sidebar from '../Sidebar.vue';

const RouterLinkStub = defineComponent({
  name: 'RouterLink',
  props: {
    to: {
      type: String,
      required: true,
    },
  },
  template: '<a :data-to="to"><slot /></a>',
});

const mountSidebar = (open: boolean, routePath = '/tasks') => mount(Sidebar, {
  props: { open },
  global: {
    stubs: {
      RouterLink: RouterLinkStub,
    },
    mocks: {
      $route: { path: routePath },
    },
  },
});

describe('Sidebar', () => {
  it('renders every navigation entry and marks the current route', () => {
    const wrapper = mountSidebar(true);
    const links = wrapper.findAll('a[data-to]');

    expect(links).toHaveLength(16);
    expect(wrapper.text()).toContain('主頁');
    expect(wrapper.text()).toContain('知識庫');
    expect(wrapper.text()).toContain('垃圾桶');

    const taskLinks = links.filter((link) => link.attributes('data-to') === '/tasks');
    expect(taskLinks).toHaveLength(2);
    expect(taskLinks.every((link) => link.classes().includes('text-primary'))).toBe(true);
  });

  it('applies the desktop collapsed state without hiding mobile navigation', () => {
    const wrapper = mountSidebar(false, '/');
    const navs = wrapper.findAll('nav');

    expect(navs).toHaveLength(2);
    expect(navs[0].classes()).toContain('-translate-x-full');
    expect(navs[0].classes()).not.toContain('translate-x-0');
    expect(navs[1].classes()).toContain('md:hidden');
  });
});
