<template>
  <div class="flex justify-center bg-background-alt pt-20">
    <div class="w-full max-w-md p-8 space-y-6 bg-background-card rounded-lg shadow-md self-start">
      <h2 class="text-2xl font-bold text-center text-text-primary">Registrovat</h2>

      <!-- Status Message -->
      <div v-if="message" :class="messageClass" class="p-3 text-sm rounded-md" role="alert">
        {{ message }}
      </div>

      <form @submit.prevent="handleRegister" class="space-y-6">
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
          <p v-if="errors.email" class="mt-1 text-xs text-error">{{ errors.email }}</p>
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
            placeholder="Heslo (min. 8 znaků, písmeno, číslice)"
          />
           <p v-if="errors.password" class="mt-1 text-xs text-error">{{ errors.password }}</p>
        </div>

        <!-- Confirm Password field -->
        <div>
          <label for="confirmPassword" class="block text-sm font-medium text-text-secondary">Potvrdit heslo</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            name="confirmPassword"
            type="password"
            required
            class="block w-full px-3 py-2 mt-1 placeholder-text-muted border border-border-neutral rounded-md shadow-sm appearance-none focus:outline-none focus:ring-primary-light focus:border-primary-light sm:text-sm"
            placeholder="Potvrdit heslo"
           />
          <p v-if="errors.confirmPassword" class="mt-1 text-xs text-error">{{ errors.confirmPassword }}</p>
        </div>

        <div>
          <button
            type="submit"
            :disabled="isLoading"
            class="flex justify-center w-full px-4 py-2 text-sm font-medium text-text-on-primary bg-primary border border-transparent rounded-md shadow-sm hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-light disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="isLoading">Registruji...</span>
            <span v-else>Registrovat</span>
          </button>
        </div>
      </form>

      <div class="text-sm text-center">
        <router-link to="/login" class="font-medium text-primary hover:text-primary-light">
          Máte již účet? Přihlaste se
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { authService } from '@/services/authService';

const email = ref('');
const password = ref('');
const confirmPassword = ref('');

const isLoading = ref(false);
const message = ref<string | null>(null);
const isError = ref(false);

// Frontend validation errors store
const errors = reactive({
  email: '',
  password: '',
  confirmPassword: ''
});

const messageClass = computed(() => {
  return isError.value ? 'bg-background-error-light text-error-dark' : 'bg-background-success-light text-success';
});

function validateForm(): boolean {
  let isValid = true;
  errors.email = '';
  errors.password = '';
  errors.confirmPassword = ''; // Reset confirmation error
  message.value = null; // Clear general message on new validation

  // --- Email Validation ---
  if (!email.value) {
    errors.email = 'E-mail je povinný.';
    isValid = false;
  } else if (!/\S+@\S+\.\S+/.test(email.value)) { // Simple email regex
    errors.email = 'Neplatná e-mailová adresa.';
    isValid = false;
  }

  // --- Password Validation ---
  if (!password.value) {
    errors.password = 'Heslo je povinné.';
    isValid = false;
  } else {
    if (password.value.length < 8) {
      errors.password = 'Heslo musí mít alespoň 8 znaků.';
      isValid = false;
    } else if (!/[a-zA-Z]/.test(password.value)) {
      errors.password = 'Heslo musí obsahovat alespoň jedno písmeno.';
      isValid = false;
    } else if (!/\d/.test(password.value)) {
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

async function handleRegister() {
  if (!validateForm()) {
    return;
  }

  isLoading.value = true;
  message.value = null;
  isError.value = false;

  try {
    const result = await authService.register({
      email: email.value,
      password: password.value,
      password_confirm: confirmPassword.value
    });

    message.value = result.message;
    isError.value = !result.success;

    if (result.success) {
      email.value = '';
      password.value = '';
      confirmPassword.value = ''; // Clear confirmation field as well
    }
  } catch (err) {
    console.error('Unexpected error during registration:', err);
    message.value = 'Během registrace došlo k neočekávané chybě.';
    isError.value = true;
  } finally {
    isLoading.value = false;
  }
}
</script>
