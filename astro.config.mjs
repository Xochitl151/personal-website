import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://personal-website-8ja.pages.dev',
  trailingSlash: 'never',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/resume'),
    }),
  ],
});
