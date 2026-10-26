<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { chatStream, ocrImage, type SseEvent } from '../api'
import { renderMarkdown } from '../lib/markdown'
import { useAppStore, useRecordsStore, type Mode } from '../stores/app'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const modes: Array<{ key: Mode; code: string; label: string; hint: string; placeholder: string; samples: string[] }> = [
  {
    key: 'tutor',
    code: 'TUTOR',
    label: '讲题',
    hint: '按审题、考点、分步、易错四步讲完一道题。',
    placeholder: '把题目打在这里，或拍照识别后自动填入…',
    samples: ['已知阶梯轴总长 430，分段 80/110/120/120，求各段直径与加工顺序。', '计算图示机构的自由度，并判断是否具有确定运动。'],
  },
  {
    key: 'variant',
    code: 'VARIANT',
    label: '变式',
    hint: '同考点生成三道由易到难的变式题，附答案与解析。',
    placeholder: '说明知识点或原题，例如：齿轮传动比计算…',
    samples: ['围绕「齿轮传动比计算」出三道变式题。', '围绕「铁碳相图共析转变」出三道变式题。'],
  },
  {
    key: 'rag',
    code: 'RAG',
    label: '教材',
    hint: '从教材切片里找依据回答，并标注章节出处。',
    placeholder: '问教材里的概念，例如：自由度公式里 p5 指什么？',
    samples: ['自由度公式里 p5 指什么？', '钢的热处理四把火分别起什么作用？'],
  },
  {
    key: 'drawing',
    code: 'DRAW',
    label: '图纸',
    hint: '基于已识读的图纸结果追问细节。',
    placeholder: '例如：φ64 这一段为什么标 Ra 1.6？',
    samples: ['φ64 这一段为什么标 Ra 1.6？', '这个零件的加工顺序应该怎么排？'],
  },
]

const route = useRoute()
const app = useAppStore()
const records = useRecordsStore()

const mode = ref<Mode>('tutor')
const messages = ref<ChatMessage[]>([])
const draft = ref('')
const busy = ref(false)
const errorMsg = ref('')
const ocrBusy = ref(false)
const controller = ref<AbortController | null>(null)
const logEl = ref<HTMLElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const current = computed(() => modes.find((m) => m.key === mode.value) ?? modes[0])
const hasDrawingContext = computed(() => Boolean(app.drawingContext.trim()))
const usedContext = computed(() => mode.value === 'drawing' && hasDrawingContext.value)

onMounted(() => {
  const queryMode = String(route.query.mode ?? '')
  if (modes.some((m) => m.key === queryMode)) {
    mode.value = queryMode as Mode
  }
  if (mode.value === 'drawing' && !hasDrawingContext.value) {
    app.notify('还没有图纸识读结果，先去识读台传一张图')
  }
})

function switchMode(next: Mode) {
  if (next === mode.value) return
  if (busy.value) controller.value?.abort()
  mode.value = next
  if (messages.value.length) {
    messages.value = []
    app.notify('已切换模式，开始新对话')
  }
}

function scrollToEnd() {
  requestAnimationFrame(() => logEl.value?.scrollTo({ top: logEl.value.scrollHeight, behavior: 'smooth' }))
}

async function send(text?: string) {
  const content = (text ?? draft.value).trim()
  if (!content || busy.value) return
  if (content.length > 2000) {
    app.notify('单次提问不超过 2000 字')
    return
  }

  const history = messages.value.slice(-10).map((m) => ({ role: m.role, content: m.content }))
  messages.value.push({ role: 'user', content })
  messages.value.push({ role: 'assistant', content: '' })
  draft.value = ''
  errorMsg.value = ''
  busy.value = true
  controller.value = new AbortController()
  const index = messages.value.length - 1
  let acc = ''
  scrollToEnd()

  try {
    await chatStream(
      mode.value,
      [...history, { role: 'user', content }],
      usedContext.value ? app.drawingContext : null,
      (event: SseEvent) => {
        if (event.type === 'delta' && event.text) {
          acc += event.text
          messages.value[index].content = acc
          scrollToEnd()
        } else if (event.type === 'error') {
          errorMsg.value = event.message ?? '生成失败'
        }
      },
      controller.value.signal,
    )
    if (acc.trim()) records.add(mode.value, content, acc, [])
  } catch (error) {
    const message = error instanceof Error ? error.message : '生成失败'
    if (!/abort/i.test(message)) errorMsg.value = message
    else if (acc.trim()) records.add(mode.value, content, `${acc}\n\n（已手动停止生成）`, [])
  } finally {
    busy.value = false
    controller.value = null
  }
}

function stop() {
  controller.value?.abort()
  app.notify('已停止生成')
}

async function onPickImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file || ocrBusy.value) return
  ocrBusy.value = true
  try {
    const text = await ocrImage(file)
    if (text.includes('无法识别为题目')) {
      app.notify('这张图片没能识别成题目，换一张更清晰的试试')
    } else {
      draft.value = text
      app.notify('题目已识别，检查一下再发送')
    }
  } catch (error) {
    app.notify(error instanceof Error ? error.message : '识别失败')
  } finally {
    ocrBusy.value = false
    input.value = ''
  }
}

onBeforeUnmount(() => controller.value?.abort())
</script>

<template>
  <section class="px-4 pb-8 pt-6 sm:px-8 lg:px-10 lg:py-9">
    <div class="mb-5">
      <div class="font-mono text-[10px] tracking-wide text-accent">FIG. 07　AI 讲题台</div>
      <h2 class="mt-1.5 text-[clamp(22px,5vw,32px)] font-bold">AI 讲题</h2>
      <p class="mt-2 max-w-[44em] text-[13.5px] leading-relaxed text-ink2">
        四个模式共用一条对话流。回答逐字流式返回，可随时停止；停止后已生成的部分仍会保存到「我的记录」。
      </p>
    </div>

    <div class="grid gap-0 border border-linesoft lg:grid-cols-[220px_1fr]">
      <aside class="border-b border-linesoft bg-paper2 p-3 lg:border-b-0 lg:border-r">
        <div class="mb-2 font-mono text-[9.5px] tracking-widest text-ink2">模式</div>
        <div class="flex gap-1.5 overflow-x-auto lg:flex-col lg:overflow-visible [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          <button
            v-for="item in modes"
            :key="item.key"
            type="button"
            class="shrink-0 border px-3 py-2 text-left text-[13.5px] leading-tight transition-colors lg:w-full"
            :class="
              item.key === mode
                ? 'border-ink bg-ink text-paper'
                : 'border-line bg-paper text-ink2 hover:border-ink hover:text-ink'
            "
            @click="switchMode(item.key)"
          >
            <span class="font-mono text-[9px] tracking-widest opacity-70">{{ item.code }}</span>
            <span class="ml-1.5">{{ item.label }}</span>
          </button>
        </div>
        <p class="mt-3 hidden text-[12px] leading-[1.75] text-ink2 lg:block">{{ current.hint }}</p>
        <div v-if="usedContext" class="mt-3 border border-blueprint bg-paper p-2 font-mono text-[10px] leading-relaxed text-blueprint">
          已载入图纸识读结果 · {{ app.drawingContext.length }} 字
        </div>
      </aside>

      <div class="flex min-h-[58vh] min-w-0 flex-col bg-paper">
        <div ref="logEl" class="flex flex-1 flex-col gap-4 overflow-y-auto px-3.5 py-4" style="max-height: 54vh">
          <div v-if="!messages.length" class="border border-dashed border-line bg-paper2 p-4">
            <h4 class="text-[15px] font-bold">{{ current.label }}模式怎么用</h4>
            <p class="mt-1.5 text-[13px] leading-[1.8] text-ink2">{{ current.hint }}</p>
            <div class="mt-3 flex flex-col gap-1.5">
              <button
                v-for="sample in current.samples"
                :key="sample"
                type="button"
                class="border border-line bg-paper px-2.5 py-1.5 text-left text-[12px] leading-[1.6] text-ink2 transition-colors hover:border-ink hover:text-ink"
                @click="send(sample)"
              >
                {{ sample }}
              </button>
            </div>
          </div>

          <template v-for="(message, index) in messages" :key="index">
            <div v-if="message.role === 'user'" class="ml-auto max-w-[88%] border border-linesoft bg-panel px-3 py-2.5 text-[14px] leading-relaxed">
              {{ message.content }}
            </div>
            <div v-else class="border-l-2 border-blueprint pl-3">
              <div class="mb-1.5 font-mono text-[9.5px] tracking-widest text-blueprint">
                MECHABRAIN · {{ current.code }}
              </div>
              <div
                v-if="message.content"
                class="md-body"
                v-html="renderMarkdown(message.content)"
              />
              <div v-else class="text-[13px] text-ink3">正在生成…</div>
            </div>
          </template>

          <p v-if="errorMsg" class="border-l-2 border-accent bg-paper2 px-3 py-2 text-[12.5px] text-accent">
            {{ errorMsg }}
          </p>
        </div>

        <div class="border-t border-linesoft px-3.5 pb-3 pt-2.5">
          <div class="mb-2 flex flex-wrap items-center gap-2">
            <button
              type="button"
              class="inline-flex min-h-[36px] items-center border border-line bg-paper px-2.5 text-[12px] text-ink2 transition-colors hover:border-ink hover:text-ink disabled:opacity-45"
              :disabled="ocrBusy || busy"
              @click="fileInput?.click()"
            >
              {{ ocrBusy ? '识别中…' : '拍照识别题目' }}
            </button>
            <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onPickImage" />
            <span class="font-mono text-[10px] text-ink3">{{ draft.length }} / 2000</span>
            <button
              v-if="busy"
              type="button"
              class="ml-auto inline-flex min-h-[36px] items-center border border-accent px-2.5 text-[12px] text-accent transition-colors hover:bg-accent hover:text-paper"
              @click="stop"
            >
              停止生成
            </button>
          </div>

          <form class="grid gap-2 sm:grid-cols-[1fr_auto] sm:items-end" @submit.prevent="send()">
            <textarea
              v-model="draft"
              rows="2"
              maxlength="2000"
              :placeholder="current.placeholder"
              class="min-h-[62px] w-full resize-y border border-line bg-paper px-3 py-2.5 text-[16px] leading-relaxed focus:border-ink focus:outline-none"
              @keydown.enter.exact.prevent="send()"
            />
            <button
              type="submit"
              class="inline-flex min-h-[44px] items-center justify-center border border-ink bg-ink px-4 text-[14px] text-paper transition-colors hover:border-accent hover:bg-accent disabled:cursor-not-allowed disabled:opacity-45"
              :disabled="busy || !draft.trim()"
            >
              发送
            </button>
          </form>
          <p class="mt-2 text-[10.5px] leading-relaxed text-ink3">
            Enter 发送，Shift + Enter 换行。以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。
          </p>
        </div>
      </div>
    </div>
  </section>
</template>
