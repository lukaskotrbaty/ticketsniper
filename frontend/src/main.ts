import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import Toast, { type PluginOptions } from "vue-toastification";
import "vue-toastification/dist/index.css";
import './style.css';
import App from '@/App.vue';
import { useAuthStore } from '@/stores/auth';

const app = createApp(App)
const pinia = createPinia()

app.use(pinia);

// Configure Toast options (optional)
const toastOptions: PluginOptions = {};
app.use(Toast, toastOptions);

// Initialize the auth store AFTER Pinia, Router, and Toast are used
const authStore = useAuthStore();

// Wrap initialization and mounting in an async function
async function initializeAndMount() {
  try {
    // Wait for the initial authentication check to complete
    await authStore.checkAuth();
  } catch (error) {
    console.error("Error during initial auth check:", error);
  }

  // Use the router plugin AFTER the auth check
  app.use(router);

  try {
    // Wait for the router to be ready before mounting
    // This ensures async components and initial navigation are resolved
    await router.isReady();
  } catch (error) {
      console.error("Router failed to become ready:", error);
  }

  app.mount('#app');
}

initializeAndMount();
