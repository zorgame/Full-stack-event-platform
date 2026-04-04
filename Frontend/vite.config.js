import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    sourcemap: false,
    cssCodeSplit: true,
    reportCompressedSize: false,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined

          if (
            id.includes('/jspdf/')
            || id.includes('/jspdf-autotable/')
            || id.includes('/jsbarcode/')
            || id.includes('/qrcode/')
          ) {
            return 'vendor-pdf'
          }

          if (id.includes('/vue/') || id.includes('/vue-router/') || id.includes('/pinia/')) {
            return 'vendor-vue'
          }

          if (id.includes('/bootstrap/')) {
            return 'vendor-ui'
          }

          if (id.includes('/axios/')) {
            return 'vendor-http'
          }

          return undefined
        },
      },
    },
  },
})
