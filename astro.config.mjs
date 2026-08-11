import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  // 部署后改成真实域名，例如 https://xxx.pages.dev
  site: 'https://example.pages.dev',
  trailingSlash: 'never',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/resume'),
    }),
  ],
});
