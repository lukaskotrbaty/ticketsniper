<template>
  <div class="flex flex-col items-center bg-background-alt text-center p-4 pt-20">
    <h1 class="text-6xl font-bold text-primary mb-4">404</h1>
    <h2 class="text-2xl font-semibold text-text-primary mb-2">Stránka nenalezena</h2>
    <p class="text-text-secondary mb-6">Omlouváme se, ale stránka, kterou hledáte, neexistuje nebo byla přesunuta.</p>
    <router-link
      :to="homeRoute"
      class="px-6 py-2 text-sm font-medium text-text-on-primary bg-primary rounded-md hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-light"
    >
      {{ homeRouteText }}
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();

// Determine the correct home route based on login status
const homeRoute = computed(() => (authStore.isLoggedIn ? '/dashboard' : '/'));
const homeRouteText = computed(() => (authStore.isLoggedIn ? 'Zpět na Dashboard' : 'Přejít na Hlavní stránku'));
</script>
