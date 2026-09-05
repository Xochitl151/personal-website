import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://personal-website-8ja.pages.dev',
  trailingSlash: 'never',
  redirects: {
    '/pitch/ai': '/',
    '/pitch/data': '/',
    '/tour': '/',
    '/projects': '/#cases',
  },
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/resume'),
    }),
  ],
});
