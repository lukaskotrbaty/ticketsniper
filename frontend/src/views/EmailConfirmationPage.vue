<template>
  <div class="flex justify-center bg-background-alt pt-20">
    <div class="w-full max-w-md p-8 space-y-6 text-center bg-background-card rounded-lg shadow-md self-start">
      <h2 class="text-2xl font-bold text-text-primary">Potvrzení e-mailu</h2>

      <div v-if="isLoading" class="text-text-secondary">
        <p>Ověřování vašeho e-mailu...</p>
        <!-- Optional: Add a spinner -->
      </div>

      <div v-else-if="message" :class="messageClass" class="p-3 text-sm rounded-md" role="alert">
        {{ message }}
      </div>

      <div v-if="!isLoading" class="mt-4">
        <router-link to="/login" class="font-medium text-primary hover:text-primary-light">
          Pokračovat k přihlášení
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { authService } from '@/services/authService';

const route = useRoute();
const isLoading = ref(true);
const message = ref<string | null>(null);
const isError = ref(false);

const messageClass = computed(() => {
  return isError.value ? 'bg-background-error-light text-error-dark' : 'bg-background-success-light text-success';
});

onMounted(async () => {
  const token = route.query.token as string | undefined; // Get token from URL query ?token=...

  if (!token) {
    message.value = 'Potvrzovací token nebyl nalezen v URL.';
    isError.value = true;
    isLoading.value = false;
    return;
  }

  isLoading.value = true;
  message.value = null;
  isError.value = false;

  try {
    const result = await authService.confirmEmail(token);
    message.value = result.message;
    isError.value = !result.success;
  } catch (err) {
    console.error('Unexpected error during email confirmation:', err);
    message.value = 'Během potvrzování e-mailu došlo k neočekávané chybě.';
    isError.value = true;
  } finally {
    isLoading.value = false;
  }
});
</script>
