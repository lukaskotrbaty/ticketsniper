/**
 * Interface representing an available route/connection
 * based on the backend schema `schemas.available_route.AvailableRoute`.
 */
export interface AvailableRoute {
  routeId: string;
  departureTime: string; // Keep as string for simplicity, can parse if needed
  arrivalTime: string;   // Keep as string
  freeSeatsCount: number;
  vehicleTypes: string[];
  fromStationId: string;
  toStationId: string;
}
