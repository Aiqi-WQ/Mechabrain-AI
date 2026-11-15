<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { fetchMeta, type MetaInfo } from './api'
import { useAppStore } from './stores/app'

const route = useRoute()
const app = useAppStore()

const nav = [
  { path: '/', label: '首页' },
  { path: '/drawing', label: '识图' },
  { path: '/rag', label: '教材' },
  { path: '/chat', label: '讲题' },
  { path: '/records', label: '记录' },
]

const current = computed(() => route.path)
const meta = ref<MetaInfo | null>(null)

onMounted(async () => {
  try {
    meta.value = await fetchMeta()
  } catch {
    meta.value = null
  }
})

const capabilityItems = computed(() => {
  if (!meta.value) return []
  const caps = meta.value.capabilities
  return [
    { key: 'chat', label: '对话', ok: caps.chat, tip: '未配置 DEEPSEEK_API_KEY' },
    { key: 'vision', label: '识图', ok: caps.vision, tip: '未配置 DASHSCOPE_API_KEY' },
    {
      key: 'rag',
      label: '知识库',
      ok: caps.rag,
      tip: '未构建索引，运行 python scripts/ingest.py',
    },
  ]
})

const ragBackend = computed(() => meta.value?.rag_backend ?? '')
</script>

<template>
  <header class="sticky top-0 z-40 border-b border-ink bg-paper">
    <div class="mx-auto flex max-w-[1180px] items-center gap-3 px-3 py-2 sm:px-4">
      <RouterLink to="/" class="flex shrink-0 items-baseline gap-2">
        <span class="text-lg font-bold tracking-tight">机小智</span>
        <span class="font-mono text-[10px] tracking-[0.14em] text-ink2">MECHABRAIN</span>
      </RouterLink>
      <div class="relative min-w-0 flex-1">
        <nav class="flex items-center gap-0.5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
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
        <div
          class="pointer-events-none absolute inset-y-0 right-0 w-6 bg-gradient-to-l from-paper to-transparent sm:right-0 lg:hidden"
          aria-hidden="true"
        />
      </div>
      <span
        class="hidden shrink-0 border border-accent px-1.5 py-0.5 font-mono text-[10px] leading-none tracking-widest text-accent sm:block"
      >
        AI
      </span>
    </div>

    <div
      v-if="capabilityItems.length"
      class="mx-auto flex max-w-[1180px] flex-wrap items-center gap-x-3 gap-y-1 border-t border-linesoft px-3 py-1.5 font-mono text-[11px] sm:px-4"
      role="status"
      aria-label="服务能力状态"
    >
      <span
        v-for="item in capabilityItems"
        :key="item.key"
        class="flex items-center gap-1"
        :class="item.ok ? 'text-ink2' : 'text-accent'"
        :title="item.ok ? '可用' : item.tip"
      >
        <span aria-hidden="true">{{ item.ok ? '✓' : '⚠' }}</span>
        <span>{{ item.label }}</span>
        <span class="sr-only">{{ item.ok ? '可用' : item.tip }}</span>
      </span>
      <span v-if="ragBackend && ragBackend !== 'none'" class="ml-auto text-ink2">检索：{{ ragBackend }}</span>
    </div>
  </header>

  <main class="mx-auto max-w-[1180px] lg:border-x lg:border-linesoft">
    <RouterView />
  </main>

  <Transition name="fade">
    <div
      v-if="app.toast"
      role="status"
      aria-live="polite"
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

@media (prefers-reduced-motion: reduce) {
  .fade-enter-active,
  .fade-leave-active {
    transition: none;
  }
}
</style>
