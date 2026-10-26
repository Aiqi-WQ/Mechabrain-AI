<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { visionStream, type SseEvent } from '../api'
import { useAppStore } from '../stores/app'

interface DimCard {
  key: string
  title: string
  content: string
  confidence: string
}

const router = useRouter()
const app = useAppStore()

const file = ref<File | null>(null)
const previewUrl = ref('')
const busy = ref(false)
const dims = ref<DimCard[]>([])
const notes = ref('')
const errorMsg = ref('')
const dragging = ref(false)
const controller = ref<AbortController | null>(null)

const sizeLabel = computed(() => {
  if (!file.value) return ''
  return `${Math.round(file.value.size / 1024)} KB`
})

const contextText = computed(() => {
  if (!dims.value.length) return ''
  const body = dims.value.map((d) => `${d.title}：${d.content}`).join('\n')
  return body + (notes.value ? `\n识别备注：${notes.value}` : '')
})

function acceptFile(candidate?: File | null) {
  if (!candidate) return
  if (!/^image\/(jpeg|png|webp)$/.test(candidate.type)) {
    app.notify('仅支持 JPG / PNG / WEBP 图片')
    return
  }
  if (candidate.size > 10 * 1024 * 1024) {
    app.notify('图片超过 10MB，压缩后再传')
    return
  }
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  file.value = candidate
  previewUrl.value = URL.createObjectURL(candidate)
  dims.value = []
  notes.value = ''
  errorMsg.value = ''
}

function onDrop(event: DragEvent) {
  dragging.value = false
  acceptFile(event.dataTransfer?.files?.[0])
}

function onChange(event: Event) {
  const target = event.target as HTMLInputElement
  acceptFile(target.files?.[0])
}

function reset() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
  file.value = null
  dims.value = []
  notes.value = ''
  errorMsg.value = ''
}

async function run() {
  if (!file.value || busy.value) return
  busy.value = true
  dims.value = []
  notes.value = ''
  errorMsg.value = ''
  controller.value = new AbortController()
  try {
    await visionStream(
      file.value,
      (event: SseEvent) => {
        if (event.type === 'dimension') {
          dims.value.push({
            key: event.key ?? '',
            title: event.title ?? '',
            content: event.content ?? '',
            confidence: event.confidence ?? 'medium',
          })
        } else if (event.type === 'meta') {
          notes.value = event.notes ?? ''
        } else if (event.type === 'error') {
          errorMsg.value = event.message ?? '识读失败'
        }
      },
      controller.value.signal,
    )
  } catch (error) {
    const message = error instanceof Error ? error.message : '识读失败'
    if (!/abort/i.test(message)) errorMsg.value = message
  } finally {
    busy.value = false
    controller.value = null
  }
}

function askMore() {
  app.setDrawingContext(contextText.value)
  router.push({ path: '/chat', query: { mode: 'drawing' } })
}

onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  controller.value?.abort()
})
</script>

<template>
  <section class="px-4 pb-10 pt-6 sm:px-8 lg:px-10 lg:py-9">
    <div class="mb-5">
      <div class="font-mono text-[10px] tracking-wide text-accent">FIG. 05　图纸识读台</div>
      <h2 class="mt-1.5 text-[clamp(22px,5vw,32px)] font-bold">图纸识读</h2>
      <p class="mt-2 max-w-[44em] text-[13.5px] leading-relaxed text-ink2">
        支持 JPG / PNG / WEBP，单张不超过 10MB。识读按「视图结构 → 尺寸与公差 → 表面粗糙度 → 材料推断 → 加工工艺」五个维度输出。
        图片直接发给多模态模型，不落盘、不入库。
      </p>
    </div>

    <div class="grid gap-3">
      <label
        class="relative block cursor-pointer border border-dashed bg-paper2 px-4 py-7 text-center transition-colors"
        :class="dragging ? 'border-accent bg-[#e9e6e2]' : 'border-line hover:border-accent'"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
      >
        <div class="font-mono text-[9.5px] tracking-widest text-accent">UPLOAD · IMAGE</div>
        <h4 class="mt-2 text-[16px] font-bold">拖一张零件图到这里，或点击选择文件</h4>
        <p class="mt-1.5 text-[12.5px] text-ink2">零件图、装配图、课本习题截图都可以 · JPG / PNG / WEBP · ≤ 10MB</p>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
          @change="onChange"
        />
      </label>

      <div v-if="previewUrl" class="border border-line bg-white p-2">
        <img :src="previewUrl" alt="待识读图纸预览" class="mx-auto block max-h-[420px] w-auto max-w-full object-contain" />
        <div class="mt-2 flex flex-wrap justify-between gap-2 border-t border-linesoft pt-1.5 font-mono text-[10px] text-ink2">
          <span class="break-all">{{ file?.name }}</span>
          <span>{{ sizeLabel }}</span>
        </div>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="inline-flex min-h-[44px] items-center border border-ink bg-ink px-4 text-[14px] text-paper transition-colors hover:border-accent hover:bg-accent disabled:cursor-not-allowed disabled:opacity-45"
          :disabled="!file || busy"
          @click="run"
        >
          {{ busy ? '识读中…' : dims.length ? '重新识读' : '开始识读' }}
        </button>
        <button
          type="button"
          class="inline-flex min-h-[44px] items-center border border-line px-4 text-[14px] text-ink2 transition-colors hover:border-ink hover:text-ink disabled:cursor-not-allowed disabled:opacity-45"
          :disabled="!file"
          @click="reset"
        >
          重新选择
        </button>
        <button
          type="button"
          class="inline-flex min-h-[44px] items-center border border-line px-4 text-[14px] text-ink2 transition-colors hover:border-ink hover:text-ink disabled:cursor-not-allowed disabled:opacity-45"
          :disabled="!dims.length"
          @click="askMore"
        >
          追问细节
        </button>
      </div>

      <p v-if="errorMsg" class="border-l-2 border-accent bg-paper2 px-3 py-2 text-[13px] text-accent">
        {{ errorMsg }}
      </p>

      <div v-if="dims.length" class="grid gap-px border border-linesoft bg-linesoft md:grid-cols-2">
        <article
          v-for="(dim, index) in dims"
          :key="dim.key"
          class="min-w-0 bg-paper p-4"
          :class="index === 0 ? 'md:col-span-2' : ''"
        >
          <div class="flex items-center justify-between gap-2 font-mono text-[9.5px] tracking-widest text-accent">
            <span>{{ dim.key.toUpperCase() }}</span>
            <span>{{ dim.confidence === 'high' ? '高置信' : dim.confidence === 'low' ? '低置信' : '中置信' }}</span>
          </div>
          <h4 class="mt-1.5 text-[16px] font-bold">{{ dim.title }}</h4>
          <p class="mt-2 whitespace-pre-wrap text-[13.5px] leading-[1.8] text-ink2">{{ dim.content }}</p>
        </article>
        <article v-if="notes" class="bg-paper p-4 md:col-span-2">
          <div class="font-mono text-[9.5px] tracking-widest text-ink3">NOTE</div>
          <p class="mt-1.5 text-[13px] leading-[1.8] text-ink2">{{ notes }}</p>
        </article>
      </div>

      <p class="border-t border-dashed border-linesoft pt-2.5 text-[11.5px] leading-relaxed text-ink3">
        以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。
      </p>
    </div>
  </section>
</template>
