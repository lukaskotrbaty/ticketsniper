<template>
  <div class="relative bg-background-card rounded-lg shadow-md overflow-hidden border border-border-neutral-light p-4 transition-shadow duration-300 hover:shadow-lg">

    <!-- Mobile Layout (sm:hidden) -->
    <div class="flex flex-col gap-2 sm:hidden">
      <!-- Row 1: Status Badge and Cancel Button -->
      <div class="flex justify-between items-start">
         <span
           :class="[
             'px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full whitespace-nowrap',
             statusBgColor,
             statusTextColor
           ]"
         >
           {{ statusText }}
         </span>
         <div class="flex items-center">
           <button
             v-if="props.status === 'FOUND'"
             type="button"
             @click="handleRestartMonitoringClick"
             :disabled="isRestarting"
             class="p-1 rounded-full text-text-muted hover:text-primary hover:bg-primary-lighter focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors mr-1"
             title="Znovu spustit sledování"
           >
             <span class="sr-only">Znovu spustit sledování</span>
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
               <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
             </svg>
           </button>
           <button
             type="button"
             @click="handleCancelMonitoringClick"
             :disabled="isCancelling"
             class="p-1 rounded-full text-text-muted hover:text-error hover:bg-background-error-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-error disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
             title="Zrušit sledování"
           >
             <span class="sr-only">Zrušit sledování</span>
             <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
               <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
             </svg>
           </button>
         </div>
      </div>

      <!-- Row 2: Departure Info -->
      <div class="min-w-0">
         <p class="text-base font-semibold text-text-primary truncate" :title="fromLocation">{{ fromLocation }}</p>
         <div class="flex items-center text-sm text-text-secondary mt-0.5">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 inline-block text-text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>{{ props.departureDateTime || 'N/A' }}</span>
         </div>
      </div>

      <!-- Row 3: Arrow Icon -->
      <div class="my-1 text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-text-muted inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>

      <!-- Row 4: Arrival Info -->
      <div class="min-w-0">
         <p class="text-base font-semibold text-text-primary truncate" :title="toLocation">{{ toLocation }}</p>
         <div class="flex items-center text-sm text-text-secondary mt-0.5">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 inline-block text-text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
           <span>{{ props.arrivalDateTime || 'N/A' }}</span>
         </div>
      </div>
    </div>


    <!-- Desktop Layout (hidden sm:flex) -->
    <div class="hidden sm:flex sm:justify-between sm:items-center">
      <!-- Left side: Departure/Arrival Info -->
      <div class="flex items-center space-x-4 min-w-0 mr-2">
        <!-- Departure -->
        <div class="flex-shrink-0 min-w-0">
          <p class="text-base font-semibold text-text-primary truncate" :title="fromLocation">{{ fromLocation }}</p>
           <div class="flex items-center text-sm text-text-secondary mt-0.5">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 inline-block text-text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                 <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
             </svg>
             <span>{{ props.departureDateTime || 'N/A' }}</span>
           </div>
        </div>
        <!-- Arrow -->
        <div>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </div>
        <!-- Arrival -->
        <div class="flex-shrink-0 min-w-0">
          <p class="text-base font-semibold text-text-primary truncate" :title="toLocation">{{ toLocation }}</p>
           <div class="flex items-center text-sm text-text-secondary mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 inline-block text-text-muted flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                 <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
             </svg>
             <span>{{ props.arrivalDateTime || 'N/A' }}</span>
           </div>
        </div>
      </div>
      <!-- Right side: Status Badge and Cancel Button -->
      <div class="flex-shrink-0 flex items-center space-x-2">
         <span
           :class="[
             'px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full whitespace-nowrap',
             statusBgColor,
             statusTextColor
           ]"
         >
           {{ statusText }}
         </span>
         <button
           v-if="props.status === 'FOUND'"
           type="button"
           @click="handleRestartMonitoringClick"
           :disabled="isRestarting"
           class="p-1 rounded-full text-text-muted hover:text-primary hover:bg-primary-lighter focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
           title="Znovu spustit sledování"
         >
           <span class="sr-only">Znovu spustit sledování</span>
           <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
             <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
           </svg>
         </button>
         <button
           type="button"
           @click="handleCancelMonitoringClick"
           :disabled="isCancelling"
           class="p-1 rounded-full text-text-muted hover:text-error hover:bg-background-error-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-error disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
           title="Zrušit sledování"
         >
           <span class="sr-only">Zrušit sledování</span>
           <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
             <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
           </svg>
         </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useMonitoringStore } from '@/stores/monitoring';
import { useToast } from 'vue-toastification';
// Removed Element Plus imports

const props = defineProps<{
  id: number; // Add database primary key
  routeId: string; // Change to string (Regiojet ID)
  fromLocation: string;
  toLocation: string;
  departureDateTime: string; // Formatted DD.MM.YYYY HH:MM
  arrivalDateTime: string; // Can be empty string or formatted DD.MM.YYYY HH:MM
  status: string; // Added: expected 'MONITORING', 'FOUND', 'EXPIRED'
  createdAt: string; // Formatted DD.MM.YYYY HH:MM - Not used in template anymore
}>();
// --- Computed properties for status ---

const statusText = computed(() => {
  switch (props.status) {
    case 'FOUND':
      return 'Nalezeno';
    case 'MONITORING':
      return 'Sledováno';
    case 'EXPIRED':
      return 'Expirováno';
    default:
      return 'Neznámý stav';
  }
});

// Dynamic background color for the status badge (softer colors)
const statusBgColor = computed(() => {
  switch (props.status) {
    case 'FOUND':
      return 'bg-background-success-light';
    case 'MONITORING':
      return 'bg-background-warning-lighter';
    case 'EXPIRED':
      return 'bg-background-alt';
    default:
      return 'bg-primary-lighter'; // Default for unknown status
  }
});

// Dynamic text color for the status badge
const statusTextColor = computed(() => {
  switch (props.status) {
    case 'FOUND':
      return 'text-success-dark';
    case 'MONITORING':
      return 'text-warning-dark';
    case 'EXPIRED':
      return 'text-text-secondary';
    default:
      return 'text-primary-dark'; // Default for unknown status
  }
});

const monitoringStore = useMonitoringStore();
const toast = useToast();
const isCancelling = ref(false);
const isRestarting = ref(false); // Added for restart button state

// --- Methods ---

async function handleRestartMonitoringClick() {
  if (isRestarting.value) return;
  isRestarting.value = true;
  try {
    const response = await monitoringStore.restartRouteMonitoring(props.id);
    // Show specific toast based on whether monitoring was restarted or tickets are still available
    if (response.restarted) {
      toast.success('Sledování trasy bylo obnoveno.');
    } else {
      toast.info('Jízdenky jsou stále dostupné. Sledování nebylo znovu aktivováno.');
    }
  } catch (error: any) {
    console.error('Error restarting monitoring:', error);
    toast.error(error.message || 'Nepodařilo se obnovit sledování.');
  } finally {
    isRestarting.value = false;
  }
}

async function handleCancelMonitoringClick() {
  if (isCancelling.value) return; // Prevent double clicks

  const confirmed = window.confirm('Opravdu chcete zrušit sledování této trasy?');
  if (!confirmed) {
    return;
  }

  isCancelling.value = true;
  try {
    await monitoringStore.cancelRouteMonitoring(props.id);
    toast.success('Sledování trasy bylo zrušeno.');
    // The store action will trigger a refresh of the list
  } catch (error: any) {
    console.error('Error cancelling monitoring:', error);
    toast.error(error.message || 'Nepodařilo se zrušit sledování.');
  } finally {
    isCancelling.value = false;
  }
}
</script>

<style scoped>
/* Minimal styles, relying on Tailwind */
</style>
