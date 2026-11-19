import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ mode }) => ({
  plugins: [svelte()],
  server:
    mode === 'mock'
      ? {}
      : {
          proxy: {
            '/data.json': {
              target: 'https://road-conditions.ryanh.click',
              changeOrigin: true,
            },
            '/images': {
              target: 'https://road-conditions.ryanh.click',
              changeOrigin: true,
            },
          },
        },
}));
