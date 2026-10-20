import { defineStore } from 'pinia'

export type Mode = 'tutor' | 'rag' | 'variant' | 'drawing'

export interface RecordItem {
  id: string
  ts: number
  mode: Mode
  question: string
  answer: string
  cites: Array<{ book: string; chapter: string; page: string }>
}

const MODE_LABEL: Record<Mode, { label: string; code: string }> = {
  tutor: { label: '讲题', code: 'TUTOR' },
  rag: { label: '教材', code: 'RAG' },
  variant: { label: '变式', code: 'VAR' },
  drawing: { label: '图纸', code: 'DRAW' },
}

const STORAGE_KEY = 'mb_records_v1'

function load(): RecordItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as RecordItem[]) : []
  } catch {
    return []
  }
}

export const useRecordsStore = defineStore('records', {
  state: () => ({ items: load() as RecordItem[] }),
  getters: {
    labelOf: () => (mode: Mode) => MODE_LABEL[mode] ?? { label: '记录', code: 'AI' },
  },
  actions: {
    persist() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.items.slice(0, 150)))
      } catch {
        /* 存储已满或被禁用时忽略 */
      }
    },
    add(mode: Mode, question: string, answer: string, cites: RecordItem['cites']) {
      this.items.unshift({
        id: `r${Date.now()}${Math.random().toString(36).slice(2, 6)}`,
        ts: Date.now(),
        mode,
        question,
        answer,
        cites,
      })
      this.persist()
    },
    remove(id: string) {
      this.items = this.items.filter((item) => item.id !== id)
      this.persist()
    },
    clear() {
      this.items = []
      this.persist()
    },
  },
})

export const useAppStore = defineStore('app', {
  state: () => ({
    toast: '',
    toastTimer: 0 as number | ReturnType<typeof setTimeout>,
    drawingContext: '',
  }),
  actions: {
    notify(message: string) {
      this.toast = message
      if (this.toastTimer) clearTimeout(this.toastTimer)
      this.toastTimer = setTimeout(() => {
        this.toast = ''
      }, 2400)
    },
    setDrawingContext(text: string) {
      this.drawingContext = text
    },
  },
})

export const MODE_META = MODE_LABEL
