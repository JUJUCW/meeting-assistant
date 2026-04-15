import { createRouter, createWebHistory } from 'vue-router'
import UploadView from '../views/UploadView.vue'
import HistoryView from '../views/HistoryView.vue'
import TranslateView from '../views/TranslateView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',          component: UploadView },
    { path: '/history',   component: HistoryView },
    { path: '/translate', component: TranslateView },
    // Live translation feature routes
    {
      path: '/live-translate',
      component: () => import('../views/LiveTranslateView.vue'),
    },
    {
      path: '/translation-history',
      component: () => import('../views/TranslationHistoryView.vue'),
    },
    {
      path: '/translation/:id',
      component: () => import('../views/TranslationDetailView.vue'),
      props: true,
    },
  ],
})
