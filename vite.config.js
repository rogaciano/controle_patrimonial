import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: resolve('./static'),
  base: '/static/',
  server: {
    host: 'localhost',
    port: 5173,
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: ['.js', '.css'],
  },
  build: {
    outDir: resolve('./static/dist'),
    assetsDir: '',
    manifest: 'manifest.json',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve('./static/js/app.js'),
        styles: resolve('./static/css/app.css'),
      },
    },
  },
});
