import { createApp } from 'vue'
import App from './App.vue'
import { authStore } from './auth/store'
import { taskStore } from './data-collection/taskStore'
import router from './router'
import './style.css'

authStore.hydrate()
taskStore.hydrate()

createApp(App).use(router).mount('#app')
