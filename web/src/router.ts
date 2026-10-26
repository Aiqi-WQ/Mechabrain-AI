import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('./views/HomeView.vue') },
    { path: '/drawing', name: 'drawing', component: () => import('./views/DrawingView.vue') },
    { path: '/rag', name: 'rag', component: () => import('./views/RagView.vue') },
    { path: '/chat', name: 'chat', component: () => import('./views/ChatView.vue') },
    { path: '/records', name: 'records', component: () => import('./views/RecordsView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  const titles: Record<string, string> = {
    home: '机小智 MechaBrain AI',
    drawing: '图纸识读 · 机小智',
    rag: '教材问答 · 机小智',
    chat: 'AI 讲题 · 机小智',
    records: '我的记录 · 机小智',
  }
  document.title = titles[String(to.name)] || '机小智 MechaBrain AI'
})

export default router
