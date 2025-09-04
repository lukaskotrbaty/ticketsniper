import apiClient from './apiClient';
import type { AvailableRoute } from '@/types/availableRoute';
import type { Location } from '@/types/location';

// Interface for the payload of the POST /routes/monitor request
export interface StartMonitoringPayload {
  from_location_id: string;
  from_location_type: Location['type'];
  to_location_id: string;
  to_location_type: Location['type'];
  departure_datetime: string; // ISO string
  arrival_datetime?: string | null; // ISO string, optional
  regiojet_route_id: string;
}

// Interface for the response of the POST /monitor request (matches backend RouteMonitorResponse)
export interface StartMonitoringResponse {
  message: string;
  available: boolean; // Indicates if tickets were available at the time of request
  details?: { // Optional details if tickets were available
    freeSeatsCount?: number;
    priceFrom?: number;
    priceTo?: number;
    booking_link?: string;
    // Add other potential detail fields if needed
  } | null;
}

// Interface for the response of the POST /monitored-routes/{db_id}/restart endpoint
export interface RestartMonitoringResponse {
  message: string;
  restarted: boolean;
  details?: { // Optional details if tickets were still available (matches StartMonitoringResponse details)
    freeSeatsCount?: number;
    priceFrom?: number;
    priceTo?: number;
    booking_link?: string;
    arrivalTime?: string; // Ensure all relevant fields from check_route_availability are here
  } | null;
}

interface GetAvailableRoutesParams {
  from_location_id: string;
  to_location_id: string;
  from_location_type: string;
  to_location_type: string;
  departure_date: string;
}

/**
 * Fetches available routes from the backend API.
 * Requires authentication.
 * @param params Parameters including origin, destination, types, and date.
 * @returns A promise that resolves to an array of AvailableRoute objects.
 */
async function getAvailableRoutes(params: GetAvailableRoutesParams): Promise<AvailableRoute[]> {
  try {
    const response = await apiClient.get<AvailableRoute[]>('/routes/available', { params });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching available routes:', error);
    // Re-throw or handle error as needed in the component/store
    throw new Error(error.response?.data?.detail || 'Nepodařilo se načíst dostupné spoje');
  }
}

/**
 * Sends a request to the backend to start monitoring a specific route.
 * Requires authentication.
 * @param payload The monitoring request data.
 * @returns A promise that resolves to the response object from the backend.
 */
async function startMonitoring(payload: StartMonitoringPayload): Promise<StartMonitoringResponse> {
  try {
    // Update the expected response type here
    const response = await apiClient.post<StartMonitoringResponse>('/routes/monitor', payload);
    return response.data;
  } catch (error: any) {
    console.error('Error starting monitoring:', error);
    // Re-throw or handle error as needed in the component/store
    throw new Error(error.response?.data?.detail || 'Nepodařilo se spustit sledování');
  }
}


// Interface for the data returned by GET /routes/monitored
export interface MonitoredRouteInfo {
  id: number;
  route_id: string;
  from_location_id: string;
  from_location_type: string;
  to_location_id: string;
  to_location_type: string;
  from_location_name?: string | null;
  to_location_name?: string | null;
  departure_datetime: string; // ISO string
  arrival_datetime?: string | null; // ISO string
  status: string;
  created_at: string;
}

/**
 * Fetches the list of routes monitored by the current user.
 * Requires authentication.
 * @returns A promise that resolves to an array of MonitoredRouteInfo objects.
 */
async function getMonitoredRoutes(): Promise<MonitoredRouteInfo[]> {
  try {
    const response = await apiClient.get<MonitoredRouteInfo[]>('/routes/monitored');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching monitored routes:', error);
    throw new Error(error.response?.data?.detail || 'Nepodařilo se načíst sledované trasy');
  }
}

/**
 * Sends a request to the backend to cancel monitoring for a specific route.
 * Requires authentication.
 * @param dbId The database ID of the monitored route to cancel.
 * @returns A promise that resolves when the cancellation is successful.
 */
async function cancelMonitoring(dbId: number): Promise<void> {
  try {
    // Expecting 204 No Content on success, so no response data needed
    await apiClient.delete(`/routes/monitor/${dbId}`);
  } catch (error: any) {
    console.error(`Error cancelling monitoring for route ID ${dbId}:`, error);
    let errorMessage = 'Nepodařilo se zrušit sledování';
    if (error.response?.status === 404) {
      errorMessage = 'Sledování nebylo nalezeno.';
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    }
    throw new Error(errorMessage);
  }
}

async function restartMonitoring(dbId: number): Promise<RestartMonitoringResponse> {
  try {
    const response = await apiClient.post<RestartMonitoringResponse>(
      `/routes/monitored-routes/${dbId}/restart`
    );
    return response.data;
  } catch (error: any) {
    console.error(`Error restarting monitoring for route ID ${dbId}:`, error);
    throw new Error(
      error.response?.data?.detail || 'Nepodařilo se obnovit sledování trasy.'
    );
  }
}

export default {
  getAvailableRoutes,
  startMonitoring,
  getMonitoredRoutes,
  cancelMonitoring,
  restartMonitoring,
};
