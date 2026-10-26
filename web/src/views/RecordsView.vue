<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { renderMarkdown } from '../lib/markdown'
import { MODE_META, useAppStore, useRecordsStore, type Mode } from '../stores/app'

const records = useRecordsStore()
const app = useAppStore()

const filter = ref<'all' | Mode>('all')
const expanded = ref<string | null>(null)

const filters = computed(() => [
  { key: 'all' as const, label: '全部', count: records.items.length },
  { key: 'tutor' as const, label: '讲题', count: records.items.filter((i) => i.mode === 'tutor').length },
  { key: 'rag' as const, label: '教材', count: records.items.filter((i) => i.mode === 'rag').length },
  { key: 'variant' as const, label: '变式', count: records.items.filter((i) => i.mode === 'variant').length },
  { key: 'drawing' as const, label: '图纸', count: records.items.filter((i) => i.mode === 'drawing').length },
])

const groups = computed(() => {
  const list = filter.value === 'all' ? records.items : records.items.filter((i) => i.mode === filter.value)
  const buckets = new Map<string, typeof list>()
  for (const item of list) {
    const key = new Date(item.ts).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    const bucket = buckets.get(key) ?? []
    bucket.push(item)
    buckets.set(key, bucket)
  }
  return Array.from(buckets.entries()).map(([date, items]) => ({ date, items }))
})

function toggle(id: string) {
  expanded.value = expanded.value === id ? null : id
}

function remove(id: string) {
  records.remove(id)
  app.notify('记录已删除')
}

function clearAll() {
  if (!records.items.length) return
  if (!window.confirm('确定清空全部学习记录？该操作不可撤销。')) return
  records.clear()
  app.notify('已清空全部记录')
}

function timeOf(ts: number) {
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <section class="px-4 pb-10 pt-6 sm:px-8 lg:px-10 lg:py-9">
    <div class="mb-5">
      <div class="font-mono text-[10px] tracking-wide text-accent">FIG. 08　学习记录</div>
      <h2 class="mt-1.5 text-[clamp(22px,5vw,32px)] font-bold">我的记录</h2>
      <p class="mt-2 max-w-[44em] text-[13.5px] leading-relaxed text-ink2">
        讲题、教材问答、变式与图纸追问的回答会自动保存在本机浏览器。记录只属于这台设备，换浏览器或换电脑不会同步。
      </p>
    </div>

    <div class="mb-3 flex flex-wrap items-center gap-2">
      <button
        v-for="item in filters"
        :key="item.key"
        type="button"
        class="inline-flex min-h-[36px] items-center gap-1.5 border px-2.5 text-[12.5px] transition-colors"
        :class="filter === item.key ? 'border-ink bg-ink text-paper' : 'border-line bg-paper text-ink2 hover:border-ink hover:text-ink'"
        @click="filter = item.key"
      >
        {{ item.label }}
        <span class="font-mono text-[10px]" :class="filter === item.key ? 'text-paper/70' : 'text-ink3'">{{ item.count }}</span>
      </button>
      <button
        type="button"
        class="ml-auto inline-flex min-h-[36px] items-center border border-line px-2.5 text-[12.5px] text-ink2 transition-colors hover:border-accent hover:text-accent disabled:opacity-45"
        :disabled="!records.items.length"
        @click="clearAll"
      >
        清空记录
      </button>
    </div>

    <div v-if="!groups.length" class="border border-dashed border-line bg-paper2 px-4 py-10 text-center">
      <div class="font-mono text-[9.5px] tracking-widest text-accent">EMPTY</div>
      <h4 class="mt-2 text-[16px] font-bold">还没有记录</h4>
      <p class="mt-1.5 text-[13px] text-ink2">去讲一道题，或问一个教材问题，回答会自动存进这里。</p>
      <RouterLink
        to="/chat"
        class="mt-4 inline-flex min-h-[44px] items-center border border-ink bg-ink px-4 text-[14px] text-paper transition-colors hover:border-accent hover:bg-accent"
      >
        去提问
      </RouterLink>
    </div>

    <div v-else class="grid gap-5">
      <section v-for="group in groups" :key="group.date">
        <div class="mb-1.5 flex items-center gap-2">
          <span class="font-mono text-[10px] tracking-wide text-ink2">{{ group.date }}</span>
          <span class="h-px flex-1 bg-linesoft" />
          <span class="font-mono text-[10px] text-ink3">{{ group.items.length }} 条</span>
        </div>
        <div class="grid gap-px border border-linesoft bg-linesoft">
          <article v-for="item in group.items" :key="item.id" class="bg-paper">
            <div class="flex items-start gap-2.5 px-3.5 py-3">
              <span class="shrink-0 border border-line px-1.5 py-0.5 font-mono text-[9.5px] tracking-wide text-accent">
                {{ MODE_META[item.mode]?.code ?? 'AI' }}
              </span>
              <button type="button" class="min-w-0 flex-1 text-left" @click="toggle(item.id)">
                <div class="text-[13.5px] font-bold leading-relaxed">{{ item.question }}</div>
                <div class="mt-0.5 font-mono text-[10px] text-ink3">{{ timeOf(item.ts) }} · {{ expanded === item.id ? '收起' : '展开回答' }}</div>
              </button>
              <button
                type="button"
                class="shrink-0 px-1.5 py-0.5 font-mono text-[10px] text-ink3 transition-colors hover:text-accent"
                :aria-label="`删除记录：${item.question}`"
                @click="remove(item.id)"
              >
                删除
              </button>
            </div>
            <div v-if="expanded === item.id" class="border-t border-linesoft px-3.5 py-3">
              <div class="md-body" v-html="renderMarkdown(item.answer)" />
              <div v-if="item.cites.length" class="mt-2 flex flex-wrap gap-1.5">
                <span
                  v-for="cite in item.cites"
                  :key="cite.book + cite.chapter"
                  class="border border-line bg-paper2 px-2 py-0.5 font-mono text-[10px] text-ink2"
                >
                  {{ cite.book }}·{{ cite.chapter }}·{{ cite.page }}
                </span>
              </div>
            </div>
          </article>
        </div>
      </section>
      <p class="border-t border-dashed border-linesoft pt-2.5 text-[11px] text-ink3">
        以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。
      </p>
    </div>
  </section>
</template>
