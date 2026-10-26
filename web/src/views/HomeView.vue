<script setup lang="ts">
import { RouterLink } from 'vue-router'

const entries = [
  {
    path: '/drawing',
    code: 'DRAW 01',
    title: '图纸识读',
    desc: '上传零件图或装配图照片，按视图结构、尺寸与公差、粗糙度、材料推断、工艺建议五个维度讲解。',
    action: '打开识读台',
  },
  {
    path: '/rag',
    code: 'RAG 02',
    title: '教材问答',
    desc: '基于《机械原理》《工程材料》章节切片检索，回答末尾标注教材出处与章节页码。',
    action: '去问教材',
  },
  {
    path: '/chat',
    code: 'TUTOR 03',
    title: 'AI 讲题',
    desc: '拍照或打字提交习题，按审题、考点、分步解答、易错点四步讲完，再给一道同考点变式。',
    action: '开始讲题',
  },
  {
    path: '/chat',
    code: 'VAR 04',
    title: '变式出题',
    desc: '指定知识点，生成三道由易到难的变式题，附参考答案与解析。',
    action: '生成练习题',
  },
]

const pains = [
  { tag: 'READING', title: '图纸看不懂', desc: '尺寸标注、公差配合、表面粗糙度靠经验积累，自学时没有人告诉你这一处读得对不对。' },
  { tag: 'LOCATING', title: '教材找不到', desc: '教材厚、知识点散，遇到具体问题很难快速定位到对应章节与例题。' },
  { tag: 'FEEDBACK', title: '卡题没反馈', desc: '课后习题卡住只能等次日问老师，当天的理解窗口就这样过去了。' },
]

const layers = [
  { idx: '01', title: '表现层', desc: '页面渲染、流式输出接收、上传交互。', tech: 'Vue3 · TypeScript · Vite · TailwindCSS' },
  { idx: '02', title: '接入层', desc: 'RESTful 接口，鉴权、上传与 SSE 转发。', tech: 'FastAPI · Uvicorn' },
  { idx: '03', title: 'AI 能力层', desc: '大模型对话、多模态识图、RAG 检索、Agent 工作流。', tech: 'DeepSeek-V3 · qwen-vl-max · bge-m3' },
  { idx: '04', title: '数据层', desc: '教材切片向量化入库，学习记录留在浏览器本地。', tech: 'Chroma · localStorage' },
]
</script>

<template>
  <section class="border-t border-linesoft px-4 pb-8 pt-6 sm:px-8 lg:px-10 lg:py-11">
    <div class="grid gap-7 lg:grid-cols-[1.02fr_0.98fr] lg:gap-9">
      <div>
        <div class="font-mono text-[10px] tracking-wide text-accent">FIG. 01　项目总览</div>
        <h1 class="mt-2 text-[clamp(44px,12vw,78px)] font-bold leading-[0.95] tracking-[-0.05em]">机小智</h1>
        <div class="mt-3 flex items-center gap-2 font-mono text-[11px] tracking-[0.2em] text-ink2">
          MECHABRAIN AI
          <span class="h-px flex-1 bg-linesoft" />
        </div>
        <p class="mt-4 max-w-[33em] text-[15px] leading-[1.9] text-ink2">
          面向机械类专业学生的 AI 学习与工程图纸助手。上传一张零件图，它把<b class="text-ink">视图结构、尺寸公差、表面粗糙度</b>逐项讲清楚；
          翻教材卡住时，它从《机械原理》《工程材料》找到出处再回答；题目不会做，它按
          <b class="text-ink">审题 → 考点 → 分步 → 易错</b>讲到你会。
        </p>

        <div class="mt-6 flex flex-wrap gap-2.5">
          <RouterLink
            to="/chat"
            class="inline-flex min-h-[44px] items-center border border-ink bg-ink px-4 text-[14px] text-paper transition-colors hover:border-accent hover:bg-accent"
          >
            打开对话台
          </RouterLink>
          <RouterLink
            to="/drawing"
            class="inline-flex min-h-[44px] items-center border border-ink px-4 text-[14px] transition-colors hover:bg-ink hover:text-paper"
          >
            试一次图纸识读
          </RouterLink>
        </div>

        <dl class="mt-6 grid grid-cols-2 gap-px border border-linesoft bg-linesoft sm:grid-cols-4">
          <div class="bg-paper px-3 py-2.5">
            <dt class="font-mono text-[9px] tracking-wide text-ink2">PAGES</dt>
            <dd class="mt-0.5 text-[18px] font-bold leading-tight">5<span class="ml-1 text-[11px] font-normal text-ink2">页</span></dd>
          </div>
          <div class="bg-paper px-3 py-2.5">
            <dt class="font-mono text-[9px] tracking-wide text-ink2">AI LAYERS</dt>
            <dd class="mt-0.5 text-[18px] font-bold leading-tight">4<span class="ml-1 text-[11px] font-normal text-ink2">条链路</span></dd>
          </div>
          <div class="bg-paper px-3 py-2.5">
            <dt class="font-mono text-[9px] tracking-wide text-ink2">TEXTBOOKS</dt>
            <dd class="mt-0.5 text-[18px] font-bold leading-tight">2<span class="ml-1 text-[11px] font-normal text-ink2">本入库</span></dd>
          </div>
          <div class="bg-paper px-3 py-2.5">
            <dt class="font-mono text-[9px] tracking-wide text-ink2">STREAM</dt>
            <dd class="mt-0.5 text-[18px] font-bold leading-tight">SSE<span class="ml-1 text-[11px] font-normal text-ink2">逐字</span></dd>
          </div>
        </dl>
      </div>

      <figure class="border border-line bg-paper2 p-2.5">
        <svg class="block h-auto w-full" viewBox="0 0 520 360" role="img" aria-label="阶梯轴零件图示意">
          <g fill="none" stroke="#2a5c8a" stroke-width="1.15">
            <path d="M40 160 H120 V148 H230 V138 H350 V152 H470 V208 H350 V222 H230 V212 H120 V200 H40 Z" />
          </g>
          <g fill="none" stroke="#848da0" stroke-width="0.9" stroke-dasharray="11 4 3 4">
            <path d="M16 180 H496" />
          </g>
          <g fill="none" stroke="#c2402a" stroke-width="1">
            <path d="M40 100 H470" />
            <path d="M40 100 l10 -4 M40 100 l10 4" />
            <path d="M470 100 l-10 -4 M470 100 l-10 4" />
            <path d="M40 306 H470" />
            <path d="M40 306 l10 -4 M40 306 l10 4" />
            <path d="M470 306 l-10 -4 M470 306 l-10 4" />
            <path d="M120 306 l10 -4 M120 306 l10 4 M120 306 l-10 -4 M120 306 l-10 4" />
            <path d="M230 306 l10 -4 M230 306 l10 4 M230 306 l-10 -4 M230 306 l-10 4" />
            <path d="M350 306 l10 -4 M350 306 l10 4 M350 306 l-10 -4 M350 306 l-10 4" />
          </g>
          <g fill="none" stroke="#848da0" stroke-width="0.8">
            <path d="M40 160 V90 M470 152 V90 M40 200 V298 M120 212 V298 M230 222 V298 M350 222 V298 M470 208 V298" />
            <path d="M282 138 V130 M150 148 V130 M70 200 V262 M410 208 V262" />
            <path d="M330 138 l6 -11 l6 11 M330 138 H322 M196 138 l6 -11 l6 11 M196 138 H188" />
          </g>
          <g fill="#4c5872" font-family="Consolas, monospace" font-size="9">
            <text x="255" y="92" text-anchor="middle">430</text>
            <text x="288" y="126">φ84</text>
            <text x="145" y="126" text-anchor="end">φ64</text>
            <text x="70" y="276" text-anchor="middle">φ40</text>
            <text x="410" y="276" text-anchor="middle">φ56</text>
            <text x="80" y="322" text-anchor="middle">80</text>
            <text x="175" y="322" text-anchor="middle">110</text>
            <text x="290" y="322" text-anchor="middle">120</text>
            <text x="410" y="322" text-anchor="middle">120</text>
          </g>
          <g fill="#c2402a" font-family="Consolas, monospace" font-size="9">
            <text x="348" y="130">Ra 1.6</text>
            <text x="214" y="130">Ra 3.2</text>
          </g>
        </svg>
        <figcaption class="mt-2 flex flex-wrap justify-between gap-2 border-t border-line pt-2 font-mono text-[10px] text-ink2">
          <span>FIG. 01　阶梯轴 · 教学示例</span>
          <span>单位 mm</span>
        </figcaption>
      </figure>
    </div>
  </section>

  <section class="border-t border-linesoft px-4 py-7 sm:px-8 lg:px-10 lg:py-10">
    <div class="mb-2 flex flex-wrap items-baseline gap-3">
      <span class="font-mono text-[10px] tracking-wide text-accent">FIG. 02</span>
      <h2 class="text-[clamp(20px,4.4vw,28px)] font-bold">四个入口，一条学习链路</h2>
    </div>
    <p class="mb-5 max-w-[34em] text-[14px] text-ink2">
      从「看不懂图」到「讲得明白」，四个入口对应你在一门机械课里最常卡住的四个地方。
    </p>
    <div class="grid gap-px border border-linesoft bg-linesoft sm:grid-cols-2 lg:grid-cols-4">
      <RouterLink
        v-for="entry in entries"
        :key="entry.code"
        :to="entry.path === '/chat' && entry.code.startsWith('VAR') ? { path: '/chat', query: { mode: 'variant' } } : entry.path"
        class="group flex min-h-[168px] flex-col gap-2.5 bg-paper p-4 transition-colors hover:bg-panel"
      >
        <span class="font-mono text-[9px] tracking-widest text-accent">{{ entry.code }}</span>
        <h3 class="text-[17px] font-bold">{{ entry.title }}</h3>
        <p class="text-[13.5px] leading-[1.75] text-ink2">{{ entry.desc }}</p>
        <span class="mt-auto font-mono text-[10px] text-ink2 transition-colors group-hover:text-accent">
          {{ entry.action }} →
        </span>
      </RouterLink>
    </div>
  </section>

  <section class="border-t border-linesoft px-4 py-7 sm:px-8 lg:px-10 lg:py-10">
    <div class="mb-5 flex flex-wrap items-baseline gap-3">
      <span class="font-mono text-[10px] tracking-wide text-accent">FIG. 03</span>
      <h2 class="text-[clamp(20px,4.4vw,28px)] font-bold">为什么要做这件事</h2>
    </div>
    <div class="grid gap-px border border-linesoft bg-linesoft md:grid-cols-3">
      <div v-for="pain in pains" :key="pain.tag" class="bg-paper p-4">
        <div class="font-mono text-[9.5px] tracking-widest text-accent">{{ pain.tag }}</div>
        <h4 class="mt-2 text-[16px] font-bold">{{ pain.title }}</h4>
        <p class="mt-1.5 text-[13.5px] leading-[1.75] text-ink2">{{ pain.desc }}</p>
      </div>
    </div>
  </section>

  <section class="border-t border-linesoft px-4 py-7 sm:px-8 lg:px-10 lg:py-10">
    <div class="mb-2 flex flex-wrap items-baseline gap-3">
      <span class="font-mono text-[10px] tracking-wide text-accent">FIG. 04</span>
      <h2 class="text-[clamp(20px,4.4vw,28px)] font-bold">系统架构</h2>
    </div>
    <p class="mb-5 max-w-[44em] text-[14px] text-ink2">
      前后端分离四层结构，数据自下而上流动。API Key 只存在服务端环境变量，前端代码里不出现任何密钥。
    </p>
    <div class="grid gap-px border border-linesoft bg-linesoft lg:grid-cols-4">
      <div v-for="layer in layers" :key="layer.idx" class="bg-paper p-4">
        <div class="font-mono text-[9px] tracking-widest text-blueprint">LAYER {{ layer.idx }}</div>
        <h4 class="mt-1.5 text-[15px] font-bold">{{ layer.title }}</h4>
        <p class="mt-1 text-[12.5px] leading-[1.7] text-ink2">{{ layer.desc }}</p>
        <div class="mt-2 break-words font-mono text-[10px] leading-relaxed text-ink3">{{ layer.tech }}</div>
      </div>
    </div>
  </section>

  <footer class="border-t border-ink px-4 py-6 sm:px-8 lg:px-10 lg:py-8">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <div class="text-[15px] font-bold">机小智 MechaBrain AI</div>
        <div class="mt-1.5 font-mono text-[10px] leading-relaxed text-ink2">传智杯 · 全国高校 AI Web 开发挑战赛</div>
      </div>
      <div class="font-mono text-[10px] leading-relaxed text-ink2">
        作者　张照<br />
        绵阳城市学院 · 智能制造与工程学院<br />
        机械设计制造及其自动化 2025 级
      </div>
    </div>
    <p class="mt-4 border-t border-dashed border-linesoft pt-3 text-[12px] leading-[1.8] text-ink2">
      以上内容由 AI 生成，仅供学习参考，请以教材与老师讲解为准。
    </p>
  </footer>
</template>
