<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { ragStream, type SseEvent } from '../api'
import { renderMarkdown } from '../lib/markdown'
import { useAppStore, useRecordsStore } from '../stores/app'

interface Chapter {
  no: string
  title: string
  page: string
}

interface Book {
  name: string
  meta: string
  chapters: Chapter[]
}

const books: Book[] = [
  {
    name: '机械原理',
    meta: '孙桓 等 · 已入库',
    chapters: [
      { no: '第1章', title: '绪论', page: 'p.1–12' },
      { no: '第2章', title: '平面机构的运动简图及自由度', page: 'p.13–38' },
      { no: '第3章', title: '平面连杆机构', page: 'p.39–66' },
      { no: '第4章', title: '凸轮机构', page: 'p.67–92' },
      { no: '第5章', title: '齿轮机构', page: 'p.93–128' },
      { no: '第6章', title: '轮系', page: 'p.129–152' },
      { no: '第7章', title: '间歇运动机构', page: 'p.153–166' },
      { no: '第8章', title: '机械运转与调速', page: 'p.167–186' },
    ],
  },
  {
    name: '工程材料',
    meta: '重点章节 · 已入库',
    chapters: [
      { no: '第1章', title: '金属材料的力学性能', page: 'p.1–20' },
      { no: '第2章', title: '金属的晶体结构与结晶', page: 'p.21–44' },
      { no: '第3章', title: '合金的相结构与相图基础', page: 'p.45–68' },
      { no: '第4章', title: '铁碳合金相图', page: 'p.69–96' },
      { no: '第5章', title: '钢的热处理', page: 'p.97–124' },
      { no: '第6章', title: '合金钢与铸铁', page: 'p.125–150' },
    ],
  },
]

const app = useAppStore()
const records = useRecordsStore()

const scope = ref<{ book: string; chapter: string } | null>(null)
const question = ref('')
const answer = ref('')
const cites = ref<Array<{ book: string; chapter: string; page: string }>>([])
const backend = ref('')
const busy = ref(false)
const asked = ref('')
const errorMsg = ref('')
const controller = ref<AbortController | null>(null)
const logEl = ref<HTMLElement | null>(null)

const scopeLabel = computed(() =>
  scope.value ? `${scope.value.book} · ${scope.value.chapter}` : '全部章节 · Top-5 切片',
)

const rendered = computed(() => renderMarkdown(answer.value))

function pick(book: string, chapter: string) {
  if (scope.value && scope.value.book === book && scope.value.chapter === chapter) {
    scope.value = null
    app.notify('已取消章节限定')
  } else {
    scope.value = { book, chapter }
    app.notify(`检索范围限定为：${book} ${chapter}`)
  }
}

async function ask(text?: string) {
  const content = (text ?? question.value).trim()
  if (!content || busy.value) return
  question.value = ''
  asked.value = content
  answer.value = ''
  cites.value = []
  errorMsg.value = ''
  busy.value = true
  controller.value = new AbortController()
  let acc = ''
  try {
    await ragStream(
      content,
      scope.value ? { book: scope.value.book, chapter: scope.value.chapter } : {},
      (event: SseEvent) => {
        if (event.type === 'delta' && event.text) {
          acc += event.text
          answer.value = acc
          requestAnimationFrame(() => logEl.value?.scrollTo({ top: logEl.value.scrollHeight }))
        } else if (event.type === 'cites' && event.items) {
          cites.value = event.items
          backend.value = event.backend ?? ''
        } else if (event.type === 'error') {
          errorMsg.value = event.message ?? '生成失败'
        }
      },
      controller.value.signal,
    )
    if (acc) records.add('rag', content, acc, cites.value)
  } catch (error) {
    const message = error instanceof Error ? error.message : '生成失败'
    if (!/abort/i.test(message)) errorMsg.value = message
  } finally {
    busy.value = false
    controller.value = null
  }
}

onBeforeUnmount(() => controller.value?.abort())
</script>

<template>
  <section class="px-4 pb-10 pt-6 sm:px-8 lg:px-10 lg:py-9">
    <div class="mb-5">
      <div class="font-mono text-[10px] tracking-wide text-accent">FIG. 06　教材知识库</div>
      <h2 class="mt-1.5 text-[clamp(22px,5vw,32px)] font-bold">教材问答</h2>
      <p class="mt-2 max-w-[44em] text-[13.5px] leading-relaxed text-ink2">
        先选章节限定范围，再提问。答案由检索到的教材切片生成，末尾回标教材、章节与页码；资料里没有的内容会直说「没有」，不编造。
      </p>
    </div>

    <div class="grid gap-3 lg:grid-cols-[280px_1fr] lg:gap-0 lg:border lg:border-linesoft">
      <aside class="border border-linesoft bg-paper2 p-3.5 lg:border-0 lg:border-r">
        <div class="mb-2 font-mono text-[9.5px] tracking-widest text-ink2">教材目录</div>
        <div v-for="book in books" :key="book.name" class="mb-3.5">
          <div class="mb-1.5 flex items-baseline justify-between gap-2 border-b border-line pb-1.5">
            <b class="text-[14px]">{{ book.name }}</b>
            <span class="font-mono text-[9.5px] text-ink3">{{ book.meta }}</span>
          </div>
          <button
            v-for="chapter in book.chapters"
            :key="chapter.no"
            type="button"
            class="flex min-h-[38px] w-full items-baseline gap-1.5 border-l-2 border-transparent bg-transparent px-2 py-1.5 text-left text-[12.5px] leading-[1.5] text-ink2 transition-colors hover:bg-paper hover:text-ink"
            :class="
              scope?.book === book.name && scope?.chapter === chapter.no
                ? 'border-accent bg-paper text-ink'
                : ''
            "
            :aria-pressed="scope?.book === book.name && scope?.chapter === chapter.no"
            @click="pick(book.name, chapter.no)"
          >
            <span>{{ chapter.no }}　{{ chapter.title }}</span>
            <span class="ml-auto shrink-0 font-mono text-[9px] text-ink3">{{ chapter.page }}</span>
          </button>
        </div>
        <button
          type="button"
          class="w-full border border-line px-2 py-2 text-[12px] text-ink2 transition-colors hover:border-ink hover:text-ink"
          @click="scope = null; app.notify('已清除章节限定')"
        >
          清除章节限定
        </button>
      </aside>

      <div class="min-w-0 bg-paper p-3.5">
        <div class="flex flex-wrap items-center gap-2.5 border-b border-linesoft pb-2.5 text-[12.5px] text-ink2">
          <span>当前检索范围</span>
          <span class="font-mono text-[11px] text-accent">{{ scopeLabel }}</span>
          <span v-if="backend" class="ml-auto font-mono text-[10px] text-ink3">backend: {{ backend }}</span>
        </div>

        <div ref="logEl" class="flex max-h-[52vh] min-h-[280px] flex-col gap-4 overflow-y-auto py-4">
          <div v-if="!asked" class="border border-dashed border-line bg-paper2 p-4">
            <h4 class="text-[15px] font-bold">从教材里找答案</h4>
            <p class="mt-1.5 text-[13px] leading-[1.8] text-ink2">
              先选左侧章节缩小范围，再提问。可以试：为什么铁碳相图在 1148℃ 发生共晶转变？／自由度公式里 p5 指什么？／齿轮传动比怎么算？
            </p>
            <div class="mt-3 flex flex-wrap gap-1.5">
              <button
                v-for="sample in ['为什么铁碳相图在 1148℃ 发生共晶转变？', '自由度公式里 p5 指什么？', '齿轮传动比怎么算？']"
                :key="sample"
                type="button"
                class="border border-line bg-paper px-2 py-1 text-[11.5px] text-ink2 transition-colors hover:border-ink hover:text-ink"
                @click="ask(sample)"
              >
                {{ sample }}
              </button>
            </div>
          </div>

          <div v-else>
            <div class="ml-auto max-w-[90%] border border-linesoft bg-panel px-3 py-2.5 text-[14px]">{{ asked }}</div>
            <div class="mt-3 border-l-2 border-blueprint pl-3">
              <div class="mb-1.5 font-mono text-[9.5px] tracking-widest text-blueprint">MECHABRAIN · RAG</div>
              <div class="md-body" v-html="rendered || '正在检索教材切片…'" />
              <div v-if="cites.length" class="mt-2 flex flex-wrap gap-1.5">
                <span
                  v-for="cite in cites"
                  :key="cite.book + cite.chapter"
                  class="border border-line bg-paper2 px-2 py-0.5 font-mono text-[10.5px] text-ink2"
                >
                  {{ cite.book }}·{{ cite.chapter }}·{{ cite.page }}
                </span>
              </div>
              <p v-if="errorMsg" class="mt-2 border-l-2 border-accent pl-2 text-[12.5px] text-accent">{{ errorMsg }}</p>
              <p class="mt-3 border-t border-dashed border-linesoft pt-2 text-[10.5px] leading-relaxed text-ink3">
                以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。
              </p>
            </div>
          </div>
        </div>

        <form class="grid gap-2 border-t border-linesoft pt-2.5 sm:grid-cols-[1fr_auto] sm:items-end" @submit.prevent="ask()">
          <textarea
            v-model="question"
            rows="2"
            maxlength="2000"
            placeholder="例如：为什么铁碳相图在 1148℃ 发生共晶转变？"
            class="w-full min-h-[58px] resize-y border border-line bg-paper px-3 py-2.5 text-[16px] leading-relaxed focus:border-ink focus:outline-none"
            @keydown.enter.exact.prevent="ask()"
          />
          <button
            type="submit"
            class="inline-flex min-h-[44px] items-center justify-center border border-ink bg-ink px-4 text-[14px] text-paper transition-colors hover:border-accent hover:bg-accent disabled:cursor-not-allowed disabled:opacity-45"
            :disabled="busy || !question.trim()"
          >
            {{ busy ? '生成中…' : '提问' }}
          </button>
        </form>
        <div class="mt-2 flex flex-wrap justify-between gap-2 font-mono text-[10px] text-ink3">
          <span>检索策略：章节元数据过滤 → 语义召回 Top-5</span>
          <span>{{ records.items.filter((i) => i.mode === 'rag').length }} 条已存入记录</span>
        </div>
      </div>
    </div>
  </section>
</template>
