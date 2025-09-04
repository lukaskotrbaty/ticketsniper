import { defineStore } from 'pinia';
import { ref, reactive, computed, onMounted } from 'vue';
import type { Location } from '@/types/location';
import type { AvailableRoute } from '@/types/availableRoute';
import monitoringService from '@/services/monitoringService';
import dataService from '@/services/dataService';
import type { StartMonitoringPayload, StartMonitoringResponse, MonitoredRouteInfo } from '@/services/monitoringService';

interface MonitoringFormState {
  fromLocation: Location | null;
  toLocation: Location | null;
  departureDate: string | null; // YYYY-MM-DD
  selectedRoute: AvailableRoute | null; // Store the whole selected route object
}

export const useMonitoringStore = defineStore('monitoring', () => {
  // State
  const formState = reactive<MonitoringFormState>({
    fromLocation: null,
    toLocation: null,
    departureDate: null,
    selectedRoute: null,
  });

  const availableRoutes = ref<AvailableRoute[]>([]);
  const isLoadingAvailableRoutes = ref(false);
  const availableRoutesError = ref<string | null>(null);

  const monitoredRoutes = ref<MonitoredRouteInfo[]>([]); // State for monitored routes
  const isLoadingMonitoredRoutes = ref(false); // Loading state
  const monitoredRoutesError = ref<string | null>(null); // Error state

  const allLocations = ref<Location[]>([]); // State for all locations
  const isLoadingAllLocations = ref(false);
  const allLocationsError = ref<string | null>(null);

  // Getters - Computed properties
  const canFetchAvailableRoutes = computed(() => {
    return formState.fromLocation?.id &&
           formState.toLocation?.id &&
           formState.departureDate;
  });

  // Actions
  function setFromLocation(location: Location | null) {
    formState.fromLocation = location;
    // Reset downstream state if location changes
    availableRoutes.value = [];
    formState.selectedRoute = null;
  }

  function setToLocation(location: Location | null) {
    formState.toLocation = location;
    // Reset downstream state if location changes
    availableRoutes.value = [];
    formState.selectedRoute = null;
  }

  function setDepartureDate(date: string | null) {
    formState.departureDate = date;
    // Reset downstream state if date changes
    availableRoutes.value = [];
    formState.selectedRoute = null;
  }

  // Action called when a specific route/time is selected from the list
  function setSelectedRoute(route: AvailableRoute | null) {
    formState.selectedRoute = route;
  }

  async function fetchAvailableRoutes() {
    if (!canFetchAvailableRoutes.value) {
      console.warn('Cannot fetch available routes: Missing form data.');
      availableRoutes.value = []; // Clear routes if params become invalid
      return;
    }

    isLoadingAvailableRoutes.value = true;
    availableRoutesError.value = null;
    availableRoutes.value = []; // Clear previous results
    // Reset selection when fetching new routes
    formState.selectedRoute = null;

    try {
      // Assert non-null values because of the computed guard
      const params = {
        from_location_id: formState.fromLocation!.id,
        to_location_id: formState.toLocation!.id,
        from_location_type: formState.fromLocation!.type,
        to_location_type: formState.toLocation!.type,
        departure_date: formState.departureDate!,
      };
      const routes = await monitoringService.getAvailableRoutes(params);
      availableRoutes.value = routes;
    } catch (error: any) {
      availableRoutesError.value = error.message || 'Při načítání spojů došlo k neznámé chybě.';
      availableRoutes.value = []; // Ensure routes are empty on error
    } finally {
      isLoadingAvailableRoutes.value = false;
    }
  }

  // Action to start monitoring a route
  // Correct the return type annotation here
  async function startMonitoring(payload: StartMonitoringPayload): Promise<StartMonitoringResponse> {
    // The component handles loading state and errors/success via toast
    // This action just forwards the call to the service
    try {
      const response = await monitoringService.startMonitoring(payload);
      // Optionally trigger fetching monitored routes again after success
      // fetchMonitoredRoutes(); // Implement in Task 8
      return response;
    } catch (error) {
      // Re-throw the error so the component can catch it and display toast
      console.error('Error in startMonitoring store action:', error);
      throw error;
    }
  }

  // Action to fetch all locations (used for name lookups)
  async function fetchAllLocations() {
    if (allLocations.value.length > 0) return; // Don't refetch if already loaded

    isLoadingAllLocations.value = true;
    allLocationsError.value = null;
    try {
      // Fetch without a query to get all locations
      allLocations.value = await dataService.getLocations();
    } catch (error: any) {
      console.error('Error fetching all locations in store:', error);
      allLocationsError.value = error.message || 'Nepodařilo se načíst data lokací.';
      allLocations.value = []; // Clear on error
    } finally {
      isLoadingAllLocations.value = false;
    }
  }

  // Action to fetch monitored routes
  async function fetchMonitoredRoutes() {
    isLoadingMonitoredRoutes.value = true;
    monitoredRoutesError.value = null;
    try {
      monitoredRoutes.value = await monitoringService.getMonitoredRoutes();
    } catch (error: any) {
      console.error('Error fetching monitored routes in store:', error);
      monitoredRoutesError.value = error.message || 'Nepodařilo se načíst sledované trasy.';
      monitoredRoutes.value = []; // Clear on error
    } finally {
      isLoadingMonitoredRoutes.value = false;
    }
  }

  // Action to reset the form state
  function resetForm() {
    formState.fromLocation = null;
    formState.toLocation = null;
    formState.departureDate = null;
    formState.selectedRoute = null;
    availableRoutes.value = [];
    availableRoutesError.value = null;
  }

  // Fetch all locations when the store is initialized
  onMounted(() => {
    fetchAllLocations();
  });

  // Action to cancel monitoring for a specific route
  async function cancelRouteMonitoring(dbId: number) {
    // Let the component handle loading state and toast notifications
    try {
      await monitoringService.cancelMonitoring(dbId);
      // Refresh the list of monitored routes after successful cancellation
      await fetchMonitoredRoutes();
      // No return value needed, success is implied if no error is thrown
    } catch (error) {
      // Re-throw the error so the component can catch it and display toast
      console.error(`Error in cancelRouteMonitoring store action for ID ${dbId}:`, error);
      throw error;
    }
  }

  // Action to restart monitoring for a specific route
  async function restartRouteMonitoring(dbId: number) {
    // Let the component handle loading state and toast notifications for now
    // The component will also decide if a list refresh is needed based on the response
    try {
      const response = await monitoringService.restartMonitoring(dbId);
      // After successful restart, refresh the list of monitored routes
      // to show the updated status (e.g., from FOUND to MONITORING)
      if (response.restarted) { // Only refresh if monitoring was actually restarted
        await fetchMonitoredRoutes();
      }
      return response; // Return the response so component can use it (e.g. for specific toasts)
    } catch (error) {
      console.error(`Error in restartRouteMonitoring store action for ID ${dbId}:`, error);
      throw error; // Re-throw for the component to handle with a toast
    }
  }

  return {
    // State
    formState,
    availableRoutes,
    isLoadingAvailableRoutes,
    availableRoutesError,
    monitoredRoutes,
    isLoadingMonitoredRoutes,
    monitoredRoutesError,
    allLocations,
    isLoadingAllLocations,
    allLocationsError,
    // Getters
    canFetchAvailableRoutes,
    // Actions
    setFromLocation,
    setToLocation,
    setDepartureDate,
    setSelectedRoute,
    fetchAvailableRoutes,
    startMonitoring,
    resetForm,
    fetchMonitoredRoutes,
    fetchAllLocations,
    cancelRouteMonitoring,
    restartRouteMonitoring,
  };
});
