<template>
  <div class="flex justify-center bg-background-alt pt-20">
    <div class="w-full max-w-md p-8 space-y-6 bg-background-card rounded-lg shadow-md self-start">
      <h2 class="text-2xl font-bold text-center text-text-primary">Nastavit nové heslo</h2>

       <!-- Status Message -->
      <div v-if="message" :class="messageClass" class="p-3 text-sm rounded-md" role="alert">
        {{ message }}
      </div>

      <form @submit.prevent="handleResetPassword" class="space-y-6" v-if="!resetComplete">
         <div>
          <label for="password" class="block text-sm font-medium text-text-secondary">Nové heslo</label>
          <input
            id="password"
            v-model="password"
            name="password"
            type="password"
            required
            :disabled="isLoading"
            class="block w-full px-3 py-2 mt-1 placeholder-text-muted border border-border-neutral rounded-md shadow-sm appearance-none focus:outline-none focus:ring-primary-light focus:border-primary-light sm:text-sm disabled:opacity-50"
            placeholder="Nové heslo (min. 8 znaků, písmeno, číslice)"
          />
           <p v-if="errors.password" class="mt-1 text-xs text-error">{{ errors.password }}</p>
        </div>

        <div>
          <label for="confirmPassword" class="block text-sm font-medium text-text-secondary">Potvrdit nové heslo</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            name="confirmPassword"
            type="password"
            required
             :disabled="isLoading"
            class="block w-full px-3 py-2 mt-1 placeholder-text-muted border border-border-neutral rounded-md shadow-sm appearance-none focus:outline-none focus:ring-primary-light focus:border-primary-light sm:text-sm disabled:opacity-50"
            placeholder="Potvrdit nové heslo"
          />
           <p v-if="errors.confirmPassword" class="mt-1 text-xs text-error">{{ errors.confirmPassword }}</p>
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading"
            class="flex justify-center w-full px-4 py-2 text-sm font-medium text-text-on-primary bg-primary border border-transparent rounded-md shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-light disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">Nastavuji...</span>
            <span v-else>Nastavit nové heslo</span>
          </button>
        </div>
      </form>

        <div v-if="resetComplete && !isError" class="text-sm text-center">
            <router-link to="/login" class="font-medium text-primary hover:text-primary-light">
            Heslo úspěšně změněno. Přejít na přihlášení.
            </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { authService } from '@/services/authService';

const route = useRoute();
const router = useRouter();

const password = ref('');
const confirmPassword = ref('');
const token = ref<string | null>(null);

const isLoading = ref(false);
const message = ref<string | null>(null);
const isError = ref(false);
const resetComplete = ref(false); // Flag to hide form or show success/error message/link

const errors = reactive({
  password: '',
  confirmPassword: ''
});

const messageClass = computed(() => {
  return isError.value ? 'bg-background-error-light text-error-dark' : 'bg-background-success-light text-success';
});

onMounted(() => {
  if (typeof route.params.token === 'string') {
    token.value = route.params.token;
  } else {
    // Handle case where token is missing or invalid early
    message.value = 'Chybějící nebo neplatný odkaz pro obnovu hesla.';
    isError.value = true;
    resetComplete.value = true; // Prevent form rendering if token is invalid
  }
});

function validateForm(): boolean {
  let isValid = true;
  errors.password = '';
  errors.confirmPassword = '';
  message.value = null; // Clear general message

  // --- Password Validation ---
  if (!password.value) {
    errors.password = 'Heslo je povinné.';
    isValid = false;
  } else {
      if (password.value.length < 8) {
        errors.password = 'Heslo musí mít alespoň 8 znaků.';
        isValid = false;
      }
      else if (!/[a-zA-Z]/.test(password.value)) {
        errors.password = 'Heslo musí obsahovat alespoň jedno písmeno.';
        isValid = false;
      }
      else if (!/\d/.test(password.value)) {
        errors.password = 'Heslo musí obsahovat alespoň jednu číslici.';
        isValid = false;
      }
  }

  // --- Confirm Password Validation ---
  if (!confirmPassword.value) {
    errors.confirmPassword = 'Potvrzení hesla je povinné.';
    isValid = false;
  } else if (password.value && password.value !== confirmPassword.value) { // Check match only if password is provided
    errors.confirmPassword = 'Hesla se neshodují.';
    isValid = false;
  }

  return isValid;
}


async function handleResetPassword() {
  if (!validateForm() || !token.value) {
    return;
  }

  isLoading.value = true;
  message.value = null;
  isError.value = false;

  try {
    const result = await authService.confirmPasswordReset(token.value, password.value);
    message.value = result.message;
    isError.value = !result.success;
    resetComplete.value = true; // Mark as complete to show success/error message

    if (result.success) {
      // Optionally clear form
      password.value = '';
      confirmPassword.value = '';
      // setTimeout(() => router.push('/login'), 3000); // Alternative: redirect after delay
    }
  } catch (err) { // Should generally not happen if service handles errors, but acts as fallback
    console.error('Unexpected error during password reset confirmation:', err);
    message.value = 'Došlo k neočekávané chybě při nastavování hesla.';
    isError.value = true;
    resetComplete.value = true;
  } finally {
    isLoading.value = false;
  }
}
</script>
