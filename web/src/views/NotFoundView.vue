<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <section class="px-4 pb-14 pt-8 sm:px-8 lg:px-10 lg:py-12">
    <div class="font-mono text-[10px] tracking-wide text-accent">FIG. 404　图纸未找到</div>
    <h1 class="mt-2 text-[clamp(28px,7vw,46px)] font-bold leading-tight">这一页不在图纸上</h1>
    <p class="mt-3 max-w-[40em] text-[14px] leading-[1.85] text-ink2">
      你访问的地址没有对应的页面。可能是链接写错了，或者这条记录已经被删除。
      下面四个入口是这张「学习图纸」里真实存在的位置。
    </p>

    <figure class="mt-6 border border-line bg-paper2 p-3 text-center">
      <div class="py-10">
        <div class="font-mono text-[10px] tracking-widest text-ink2">404 / NOT FOUND</div>
        <div class="mx-auto mt-4 h-px w-40 bg-line" />
        <p class="mt-4 font-mono text-[12px] text-ink2">该视图未在装配图中定义</p>
      </div>
      <figcaption class="border-t border-line pt-2 font-mono text-[10px] text-ink2">
        FIG. 404　缺省页面 · 单位 mm
      </figcaption>
    </figure>

    <div class="mt-6 flex flex-wrap gap-2.5">
      <RouterLink
        to="/"
        class="inline-flex min-h-[44px] items-center border border-ink bg-ink px-4 text-[14px] text-paper transition-colors hover:border-accent hover:bg-accent"
      >
        回到首页
      </RouterLink>
      <RouterLink
        to="/rag"
        class="inline-flex min-h-[44px] items-center border border-line px-4 text-[14px] text-ink2 transition-colors hover:border-ink hover:text-ink"
      >
        去问教材
      </RouterLink>
      <RouterLink
        to="/drawing"
        class="inline-flex min-h-[44px] items-center border border-line px-4 text-[14px] text-ink2 transition-colors hover:border-ink hover:text-ink"
      >
        去识读图纸
      </RouterLink>
    </div>
  </section>
</template>
