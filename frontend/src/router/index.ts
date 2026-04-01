import { createRouter, createWebHistory } from 'vue-router'
import UploadView from '../views/UploadView.vue'
import HistoryView from '../views/HistoryView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',        component: UploadView },
    { path: '/history', component: HistoryView },
  ],
})
