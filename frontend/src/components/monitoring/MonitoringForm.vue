<template>
  <div class="p-4 border rounded-md shadow-sm bg-background-card">
    <h2 class="text-xl font-semibold mb-4 text-text-primary">Spustit nové sledování</h2>
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <LocationAutocomplete
          label="Odkud"
          inputId="from-location"
          placeholder="Zadejte místo odjezdu"
          :modelValue="monitoringStore.formState.fromLocation"
          @update:modelValue="monitoringStore.setFromLocation($event)"
        />
        <LocationAutocomplete
          label="Kam"
          inputId="to-location"
          placeholder="Zadejte cílové místo"
          :modelValue="monitoringStore.formState.toLocation"
          @update:modelValue="monitoringStore.setToLocation($event)"
        />
        <div>
          <label for="departure-date" class="block text-sm font-medium text-text-secondary mb-1">Datum</label>
          <input
            type="date"
            id="departure-date"
            :value="monitoringStore.formState.departureDate"
            @input="monitoringStore.setDepartureDate(($event.target as HTMLInputElement)?.value || null)"
            :min="todayDate"
            required
            class="mt-1 block w-full px-3 py-2 border border-border-neutral rounded-md shadow-sm focus:outline-none focus:ring-primary-light focus:border-primary-light sm:text-sm"
          />
        </div>
      </div>

      <!-- Available Routes Section - Shown when routes are loading, loaded, or error occurred -->
      <div v-if="showAvailableRoutesSection">
        <AvailableRoutesSelect
          :routes="monitoringStore.availableRoutes"
          :isLoading="monitoringStore.isLoadingAvailableRoutes"
          :error="monitoringStore.availableRoutesError"
          :modelValue="monitoringStore.formState.selectedRoute" 
          @update:modelValue="monitoringStore.setSelectedRoute($event)"
        />
      </div>

      <!-- Submit Button -->
       <div class="mt-6">
         <button
           type="submit"
           :disabled="!canSubmit || isSubmitting"
           class="w-full inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-text-on-primary bg-primary hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-light disabled:opacity-50 disabled:cursor-not-allowed"
         >
           {{ isSubmitting ? 'Spouštím sledování...' : (canSubmit ? 'Spustit sledování' : 'Nejprve vyberte detaily trasy') }}
         </button>
       </div>

    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, reactive, toRaw } from 'vue';
import LocationAutocomplete from './LocationAutocomplete.vue';
import AvailableRoutesSelect from './AvailableRoutesSelect.vue';
import { useMonitoringStore } from '@/stores/monitoring';
import { useToast } from 'vue-toastification';
import type { StartMonitoringPayload } from '@/services/monitoringService';

const monitoringStore = useMonitoringStore();
const toast = useToast(); // Initialize toast

// Control when to show the available routes section
const showAvailableRoutesSection = ref(false);

// Watch for changes that trigger fetching available routes
watch(
  () => monitoringStore.canFetchAvailableRoutes,
  (canFetch) => {
    if (canFetch) {
      showAvailableRoutesSection.value = true; // Show section immediately
      monitoringStore.fetchAvailableRoutes();
    }
  },
  { immediate: false } // Don't run immediately on component mount
);

// Watch individual fields to potentially clear routes if a prerequisite changes
watch(() => [monitoringStore.formState.fromLocation, monitoringStore.formState.toLocation, monitoringStore.formState.departureDate], () => {
    // If the combination becomes invalid, the computed `canFetchAvailableRoutes` will handle clearing
    // but we might want to hide the section if inputs are cleared manually
    if (!monitoringStore.formState.fromLocation || !monitoringStore.formState.toLocation || !monitoringStore.formState.departureDate) {
        // Keep showing the section to display potential errors or empty states from AvailableRoutesSelect
        // showAvailableRoutesSection.value = false;
    } else if (!monitoringStore.isLoadingAvailableRoutes && !monitoringStore.availableRoutesError && monitoringStore.availableRoutes.length === 0) {
        // If inputs are valid but fetch resulted in no routes, ensure section is shown
        showAvailableRoutesSection.value = true;
    }
});


// Get today's date for min attribute on date input
const todayDate = new Date().toISOString().split('T')[0];

// --- Submit Logic ---
const isSubmitting = ref(false);

// Determine if the form can be submitted
const canSubmit = computed(() => {
  // Ensure all required fields for submission are present
  return (
    monitoringStore.formState.fromLocation !== null &&
    monitoringStore.formState.toLocation !== null &&
    monitoringStore.formState.departureDate !== null &&
    monitoringStore.formState.selectedRoute !== null // Check for selectedRoute object
  );
});

async function handleSubmit() {
  if (!canSubmit.value || isSubmitting.value) return;

  isSubmitting.value = true;

  try {
    // 1. Use the stored selected route object directly
    const selectedRoute = monitoringStore.formState.selectedRoute;

    if (!selectedRoute) {
      // This should ideally not happen if canSubmit is true, but good to check
      throw new Error('Chybí vybraná trasa. Vyberte prosím trasu znovu.');
    }

    // 2. Ensure all location data is available
    const fromLocation = toRaw(monitoringStore.formState.fromLocation); // Use toRaw if it's a reactive proxy
    const toLocation = toRaw(monitoringStore.formState.toLocation);

    if (!fromLocation || !toLocation || !monitoringStore.formState.departureDate) {
         throw new Error('Chybí informace o místě nebo datu.');
    }

    // 3. Construct the payload using datetime fields from the selectedRoute object
    const payload: StartMonitoringPayload = {
      from_location_id: String(selectedRoute.fromStationId), // Ensure string
      from_location_type: "STATION",
      to_location_id: String(selectedRoute.toStationId), // Ensure string
      to_location_type: "STATION",
      departure_datetime: selectedRoute.departureTime, // Already ISO string
      arrival_datetime: selectedRoute.arrivalTime || null, // Already ISO string or null
      regiojet_route_id: selectedRoute.routeId,
    };

    // 4. Call the store action (which calls the service)
    // This action needs to be created in the store
    const response = await monitoringStore.startMonitoring(payload);

    // Use info toast if tickets are available, success if monitoring started
    if (response.available) {
      toast.info(response.message || 'Jízdenky jsou aktuálně dostupné.');
      // Optionally display details from response.details if needed
    } else {
      toast.success(response.message || 'Sledování úspěšně spuštěno!');
      // Reset form only if monitoring actually started
      monitoringStore.resetForm();
    }

  } catch (error: any) {
    console.error('Error submitting monitoring request:', error);
    toast.error(error.message || 'Nepodařilo se spustit sledování. Zkuste to prosím znovu.');
  } finally {
    isSubmitting.value = false;
    await monitoringStore.fetchMonitoredRoutes();
  }
}
</script>
