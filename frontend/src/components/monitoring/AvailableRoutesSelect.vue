<template>
  <div class="mt-4">
    <h3 class="text-lg font-medium text-text-primary mb-2">Vyberte čas odjezdu</h3>
    <div v-if="isLoading" class="text-center py-4">
      <span class="text-text-muted">Načítání dostupných spojů...</span>
      <!-- Add a spinner here if desired -->
    </div>
    <div v-else-if="error" class="text-center py-4 text-error">
      {{ error }}
    </div>
    <div v-else-if="routes.length === 0" class="text-center py-4 text-text-muted">
      Pro vybrané datum a lokace nebyly nalezeny žádné přímé spoje.
    </div>
    <fieldset v-else class="space-y-2">
      <legend class="sr-only">Dostupné spoje</legend>
      <div
        v-for="route in routes"
        :key="route.routeId"
        class="relative flex items-start p-3 border rounded-md cursor-pointer transition-colors duration-150 ease-in-out"
        :class="{
          'border-primary-light bg-primary-lighter ring-1 ring-primary-light': modelValue?.routeId === route.routeId,
          'border-border-neutral hover:bg-background-body': modelValue?.routeId !== route.routeId && route.freeSeatsCount > 0,
          'border-border-neutral bg-background-alt hover:bg-gray-200': modelValue?.routeId !== route.routeId && route.freeSeatsCount === 0
        }"
        @click="selectRoute(route)"
      >
        <!-- Radio button removed -->
        <div class="text-sm flex-grow">
           <span class="font-medium" :class="route.freeSeatsCount > 0 ? 'text-text-primary' : 'text-text-muted'"> <!-- Dim text if sold out -->
             {{ formatTime(route.departureTime) }} - {{ formatTime(route.arrivalTime) }}
           </span>
           <!-- Display station names -->
           <p class="text-xs" :class="route.freeSeatsCount > 0 ? 'text-text-secondary' : 'text-text-muted'">
              {{ getLocationNameById(route.fromStationId) }} &rarr; {{ getLocationNameById(route.toStationId) }}
           </p>
           <p :class="route.freeSeatsCount > 0 ? 'text-text-secondary' : 'text-error font-medium'"> <!-- Highlight sold out seats with red text -->
             {{ route.freeSeatsCount }} volných míst | {{ route.vehicleTypes.join(', ') }}
           </p>
        </div>
      </div>
    </fieldset>
  </div>
</template>

<script setup lang="ts">
import type { AvailableRoute } from '@/types/availableRoute';
import { useMonitoringStore } from '@/stores/monitoring';

// --- Store Setup ---
const monitoringStore = useMonitoringStore();

// --- Props ---
interface Props {
  routes: AvailableRoute[];
  modelValue: AvailableRoute | null;
  isLoading: boolean;
  error: string | null;
}

const props = defineProps<Props>(); // Assign props to a variable
const emit = defineEmits(['update:modelValue']);

// --- Computed Properties ---
// Helper function to get location name by ID from the monitoring store
function getLocationNameById(id: string | number): string {
  // Ensure locations are loaded in monitoringStore before using this
  const location = monitoringStore.allLocations.find(loc => String(loc.id) === String(id));
  return location?.name || `ID: ${id}`; // Fallback to ID if name not found
}

// --- Methods ---
// Helper to format ISO datetime string to HH:MM
function formatTime(isoString: string | null | undefined): string {
  if (!isoString) return 'N/A'; // Return 'N/A' or similar if string is null/undefined
  try {
    // Create a Date object. It will parse the ISO string correctly, including timezone.
    const date = new Date(isoString);
    // Get hours and minutes, padding with '0' if necessary.
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
  } catch (e) {
    console.error("Error formatting time:", e);
    return 'Neplatný čas'; // Fallback for invalid date strings
  }
}

// Method to handle route selection
function selectRoute(route: AvailableRoute) {
  // Emit the full route object to update the v-model binding in the parent
  emit('update:modelValue', route);
  // The store update should happen in the parent component via the v-model binding
  // monitoringStore.setSelectedRoute(route); // This line was correctly removed previously
}
</script>
