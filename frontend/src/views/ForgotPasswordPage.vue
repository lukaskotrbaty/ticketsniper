<template>
  <div class="flex justify-center bg-background-alt pt-20">
    <div class="w-full max-w-md p-8 space-y-6 bg-background-card rounded-lg shadow-md self-start">
      <h2 class="text-2xl font-bold text-center text-text-primary">Obnovení hesla</h2>

      <!-- Status Message -->
      <div v-if="message" :class="messageClass" class="p-3 text-sm rounded-md" role="alert">
        {{ message }}
      </div>

      <form @submit.prevent="handleRequestReset" class="space-y-6" v-if="!requestSent">
        <p class="text-sm text-text-secondary">
          Zadejte svou e-mailovou adresu a my Vám pošleme odkaz pro obnovení hesla.
        </p>
        <div>
          <label for="email" class="block text-sm font-medium text-text-secondary">E-mailová adresa</label>
          <input
            id="email"
            v-model="email"
            name="email"
            type="email"
            required
            :disabled="isLoading"
            class="block w-full px-3 py-2 mt-1 placeholder-text-muted border border-border-neutral rounded-md shadow-sm appearance-none focus:outline-none focus:ring-primary-light focus:border-primary-light sm:text-sm disabled:opacity-50"
            placeholder="vas@email.cz"
          />
           <p v-if="emailError" class="mt-1 text-xs text-error">{{ emailError }}</p>
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading"
            class="flex justify-center w-full px-4 py-2 text-sm font-medium text-text-on-primary bg-primary border border-transparent rounded-md shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-light disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">Odesílám...</span>
            <span v-else>Odeslat odkaz pro obnovu</span>
          </button>
        </div>
      </form>

      <div class="text-sm text-center">
        <router-link to="/login" class="font-medium text-primary hover:text-primary-light">
          Zpět na přihlášení
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { authService } from '@/services/authService';

const email = ref('');
const emailError = ref('');
const isLoading = ref(false);
const message = ref<string | null>(null);
const isError = ref(false);
const requestSent = ref(false); // Flag to hide form after request

const messageClass = computed(() => {
  return isError.value ? 'bg-background-error-light text-error-dark' : 'bg-background-success-light text-success';
});

function validateEmail(): boolean {
  emailError.value = '';
  if (!email.value) {
    emailError.value = 'E-mail je povinný.';
    return false;
  } else if (!/\S+@\S+\.\S+/.test(email.value)) {
    emailError.value = 'Neplatná e-mailová adresa.';
    return false;
  }
  return true;
}

async function handleRequestReset() {
  if (!validateEmail()) {
    return;
  }

  isLoading.value = true;
  message.value = null;
  isError.value = false;

  try {
    const result = await authService.requestPasswordReset(email.value);
    message.value = result.message; // Show the generic message from backend
    isError.value = !result.success;
    if(result.success) {
        requestSent.value = true; // Hide form on success
    }

  } catch (err) { // Should not happen if service handles errors, but as fallback
    console.error('Unexpected error during password reset request:', err);
    message.value = 'Došlo k neočekávané chybě.';
    isError.value = true;
  } finally {
    isLoading.value = false;
  }
}
</script>
