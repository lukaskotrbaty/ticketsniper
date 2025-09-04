<script setup lang="ts">
import { ref, computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const route = useRoute();
const isLoggedIn = computed(() => authStore.isLoggedIn);
const isOnDashboard = computed(() => route.name === 'Dashboard');
const isOnAuthPage = computed(() => 
  ['Login', 'Register', 'ForgotPassword', 'ResetPassword', 'EmailConfirmation'].includes(route.name as string)
);

const isMobileMenuOpen = ref(false);

function toggleMobileMenu() {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
}

function handleLogout() {
  authStore.logout();
  if (isMobileMenuOpen.value) {
    isMobileMenuOpen.value = false;
  }
}

function scrollToSection(sectionId: string) {
  const element = document.getElementById(sectionId);
  if (element) {
    const offset = 60;
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
    
    if (isMobileMenuOpen.value) {
      isMobileMenuOpen.value = false;
    }
  }
}
</script>

<template>
  <header class="bg-background-card shadow-sm sticky top-0 z-50">
    <nav 
      class="container mx-auto px-4 py-3 flex items-center justify-between h-16"
    >
      <RouterLink to="/" class="flex items-center text-primary hover:text-primary-dark">
        <img 
          src="@/assets/ticket_sniper_logo.svg" 
          alt="Ticket Sniper logo" 
          class="h-6 md:h-8 mr-2"
        >
      </RouterLink>

      <div v-if="!isOnAuthPage" class="hidden xl:flex items-center space-x-2">
         <template v-if="isLoggedIn">
            <RouterLink
              v-if="!isOnDashboard" 
              to="/dashboard"
              class="px-4 py-2 bg-primary text-text-on-primary rounded hover:bg-primary-dark font-semibold"
            >
              Dashboard
            </RouterLink>
             <button
               @click="handleLogout"
               class="px-4 py-2 border border-gray-300 rounded text-text-secondary hover:bg-background-alt"
             >
               Odhlásit se
             </button>
          </template>
          <template v-else>
            <button
              @click="scrollToSection('how-it-works')"
              class="px-4 py-2 text-text-secondary hover:text-primary"
            >
              Jak lovit lístky
            </button>
            <button
              @click="scrollToSection('benefits')"
              class="px-4 py-2 text-text-secondary hover:text-primary"
            >
              Proč Ticket Sniper
            </button>
            <button
              @click="scrollToSection('testimonials')"
              class="px-4 py-2 text-text-secondary hover:text-primary"
            >
              Úspěšné lovy
            </button>
            <RouterLink
              to="/login"
              class="px-4 py-2 border border-gray-300 rounded text-text-secondary hover:bg-background-alt"
            >
              Přihlásit se
            </RouterLink>
            <RouterLink
              to="/register"
              class="px-4 py-2 bg-primary text-text-on-primary rounded hover:bg-primary-dark font-semibold"
            >
              Chci ulovit lístek ZDARMA
            </RouterLink>
          </template>
      </div>

      <div v-if="!isOnAuthPage" class="xl:hidden">
        <button
          @click="toggleMobileMenu"
          class="text-text-secondary hover:text-primary focus:outline-none focus:text-primary"
          aria-label="Toggle menu"
        >
           <svg v-if="!isMobileMenuOpen" class="h-6 w-6" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" stroke="currentColor"><path d="M4 6h16M4 12h16m-7 6h7"></path></svg>
           <svg v-else class="h-6 w-6" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" stroke="currentColor"><path d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
    </nav>

    <div
      v-if="!isOnAuthPage"
      v-show="isMobileMenuOpen"
      class="xl:hidden bg-background-card shadow-lg absolute top-full left-0 right-0 z-40"
      @click.self="toggleMobileMenu" 
    >
      <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
         <template v-if="isLoggedIn">
            <RouterLink
              v-if="!isOnDashboard" 
              to="/dashboard"
              @click="toggleMobileMenu"
              class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-text-on-primary bg-primary hover:bg-primary-dark"
            >
              Dashboard
            </RouterLink>
            <button
              @click="handleLogout" 
              class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-text-secondary hover:text-text-primary hover:bg-background-body"
            >
              Odhlásit se
            </button>
          </template>
          <template v-else>
            <button
              @click="scrollToSection('how-it-works')"
              class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-text-secondary hover:text-text-primary hover:bg-background-body"
            >
              Jak lovit lístky
            </button>
            <button
              @click="scrollToSection('benefits')"
              class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-text-secondary hover:text-text-primary hover:bg-background-body"
            >
              Proč Ticket Sniper
            </button>
            <button
              @click="scrollToSection('testimonials')"
              class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-text-secondary hover:text-text-primary hover:bg-background-body"
            >
              Úspěšné lovy
            </button>
            <a href="mailto:info@ticketsniper.eu" @click="toggleMobileMenu" class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-text-secondary hover:text-text-primary hover:bg-background-body">
              info@ticketsniper.eu
            </a>
            <RouterLink
              to="/login"
              @click="toggleMobileMenu"
              class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-text-secondary hover:text-text-primary hover:bg-background-body"
            >
              Přihlásit se
            </RouterLink>
            <RouterLink
              to="/register"
              @click="toggleMobileMenu"
              class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-text-on-primary bg-primary hover:bg-primary-dark"
            >
              Chci ulovit lístek ZDARMA
            </RouterLink>
          </template>
      </div>
    </div>
  </header>
</template>
