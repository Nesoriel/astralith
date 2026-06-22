import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rolldownOptions: {
      onwarn(warning, warn) {
        // @vueuse/core 当前构建产物存在 Rolldown 不可解释的 PURE 注释位置警告；
        // 该警告来自 Element Plus 间接依赖，不影响 Astralith 业务代码构建结果。
        if (warning.code === 'INVALID_ANNOTATION') {
          return
        }
        warn(warning)
      },
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/vue') || id.includes('node_modules/vue-router') || id.includes('node_modules/vue-i18n') || id.includes('node_modules/pinia')) {
            return 'vue'
          }
          if (id.includes('node_modules/element-plus') || id.includes('node_modules/@element-plus') || id.includes('node_modules/@vueuse')) {
            return 'element'
          }
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
      },
    },
  },
})
