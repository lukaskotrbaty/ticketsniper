<template>
  <div class="flex justify-center bg-background-alt pt-20">
    <div class="w-full max-w-md p-8 space-y-6 bg-background-card rounded-lg shadow-md self-start">
      <h2 class="text-2xl font-bold text-center text-text-primary">Přihlášení</h2>

      <!-- Error Message -->
      <div v-if="authError" class="p-3 text-sm text-error-dark bg-background-error-light rounded-md" role="alert">
        {{ authError }}
      </div>

      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label for="email" class="block text-sm font-medium text-text-secondary">E-mailová adresa</label>
          <input
            id="email"
            v-model="email"
            name="email"
            type="email"
            required
            class="block w-full px-3 py-2 mt-1 placeholder-text-muted border border-border-neutral rounded-md shadow-sm appearance-none focus:outline-none focus:ring-primary-light focus:border-primary-light sm:text-sm"
            placeholder="vas@email.cz"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-text-secondary">Heslo</label>
          <input
            id="password"
            v-model="password"
            name="password"
            type="password"
            required
            class="block w-full px-3 py-2 mt-1 placeholder-text-muted border border-border-neutral rounded-md shadow-sm appearance-none focus:outline-none focus:ring-primary-light focus:border-primary-light sm:text-sm"
            placeholder="Heslo"
          />
        </div>

        <div class="text-sm text-right">
          <router-link to="/forgot-password" class="font-medium text-primary hover:text-primary-light">
            Zapomněli jste heslo?
          </router-link>
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading"
            class="flex justify-center w-full px-4 py-2 text-sm font-medium text-text-on-primary bg-primary border border-transparent rounded-md shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-light disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">Přihlašuji...</span>
            <span v-else>Přihlásit se</span>
          </button>
        </div>
      </form>

      <div class="text-sm text-center">
        <router-link to="/register" class="font-medium text-primary hover:text-primary-light">
          Ještě nemáte účet? Zaregistrujte se
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const email = ref('');
const password = ref('');

// Computed properties to access store state/getters reactively
const isLoading = computed(() => authStore.isLoading);
const authError = computed(() => authStore.authError);

async function handleLogin() {
  if (!email.value || !password.value) {
    // Basic frontend validation (already handled by 'required' attribute, but good practice)
    authStore.setError('Zadejte prosím e-mail a heslo.');
    return;
  }

  const success = await authStore.login({ email: email.value, password: password.value });

  if (success) {
    // Redirect to dashboard on successful login
    router.push({ name: 'Dashboard' });
  }
  // Error message is handled reactively via computed property 'authError'
}
</script>
