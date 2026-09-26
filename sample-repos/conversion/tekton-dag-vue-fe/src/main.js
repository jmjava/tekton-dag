import { createApp } from 'vue'
import App from './App.vue'
import { defaultConfig, install } from './baggage.js'

install(defaultConfig())

createApp(App).mount('#app')
