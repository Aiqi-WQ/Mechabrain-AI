<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink, RouterView } from 'vue-router'
import { useAppStore } from './stores/app'

const route = useRoute()
const app = useAppStore()

const nav = [
  { path: '/', label: '首页' },
  { path: '/drawing', label: '图纸识读' },
  { path: '/rag', label: '教材问答' },
  { path: '/chat', label: 'AI 讲题' },
  { path: '/records', label: '我的记录' },
]

const current = computed(() => route.path)
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-ink bg-paper">
    <div class="mx-auto flex max-w-[1180px] items-center gap-3 px-3 py-2 sm:px-4">
      <RouterLink to="/" class="flex shrink-0 items-baseline gap-2">
        <span class="text-lg font-bold tracking-tight">机小智</span>
        <span class="font-mono text-[9px] tracking-[0.14em] text-ink2">MECHABRAIN</span>
      </RouterLink>
      <nav class="flex min-w-0 flex-1 items-center gap-0.5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <RouterLink
          v-for="item in nav"
          :key="item.path"
          :to="item.path"
          class="shrink-0 whitespace-nowrap border px-2.5 py-1.5 text-[13px] transition-colors"
          :class="
            current === item.path
              ? 'border-ink bg-ink text-paper'
              : 'border-transparent text-ink2 hover:border-line hover:text-ink'
          "
        >
          {{ item.label }}
        </RouterLink>
      </nav>
      <span
        class="hidden shrink-0 border border-accent px-1.5 py-0.5 font-mono text-[9px] leading-none tracking-widest text-accent sm:block"
      >
        AI
      </span>
    </div>
  </header>

  <main class="mx-auto max-w-[1180px] lg:border-x lg:border-linesoft">
    <RouterView />
  </main>

  <Transition name="fade">
    <div
      v-if="app.toast"
      class="fixed bottom-6 left-1/2 z-50 w-[min(88vw,520px)] -translate-x-1/2 bg-ink px-4 py-2.5 text-center text-[13px] text-paper"
    >
      {{ app.toast }}
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
