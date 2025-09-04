<template>
  <div class="mt-8 p-4 border rounded-md shadow-sm bg-background-card">
    <h2 class="text-xl font-semibold mb-4 text-text-primary">Sledované trasy</h2>

    <!-- Loading State -->
    <div v-if="monitoringStore.isLoadingMonitoredRoutes" class="text-center py-4">
      <p class="text-text-muted">Načítání sledovaných tras...</p>
      <!-- Add a spinner component if available -->
    </div>

    <!-- Error State -->
    <div v-else-if="monitoringStore.monitoredRoutesError" class="text-center py-4 px-3 bg-background-error-lighter border border-border-error-light rounded-md">
      <p class="text-error-dark font-medium">Chyba při načítání tras:</p>
      <p class="text-error text-sm">{{ monitoringStore.monitoredRoutesError }}</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!monitoringStore.monitoredRoutes.length" class="text-center py-4">
      <p class="text-text-muted">Zatím nesledujete žádné trasy.</p>
    </div>

    <!-- New Card Layout (One card per row) -->
    <div v-else class="space-y-4">
       <div v-for="route in monitoringStore.monitoredRoutes" :key="route.route_id">
         <MonitoringTicketCard
           :id="route.id"
           :route-id="route.route_id"
           :from-location="route.from_location_name || route.from_location_id"
           :to-location="route.to_location_name || route.to_location_id"
           :departure-date-time="formatDateTime(route.departure_datetime)"
           :arrival-date-time="formatDateTime(route.arrival_datetime, '')"
           :status="route.status"
           :created-at="formatDateTime(route.created_at)"
         />
       </div>
    </div>
    <!-- End New Card Layout -->

  </div>
</template>

<script setup lang="ts">
import { useMonitoringStore } from '@/stores/monitoring';
import { formatDateTime } from '@/utils/formatters'; // Import the new formatter
import MonitoringTicketCard from './MonitoringTicketCard.vue'; // Import placeholder

const monitoringStore = useMonitoringStore();

// Old helper functions are removed as formatting is now handled by the imported function
// and status logic will be inside the card component or passed as props.

// Note: Data fetching is triggered in DashboardPage.vue
</script>
