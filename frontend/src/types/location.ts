/**
 * Interface representing a location (city or station)
 * based on the backend schema `schemas.location.Location`.
 */
export interface Location {
  id: string;
  name: string;       // Original name for display
  type: 'CITY' | 'STATION';
  fullname?: string;  // Optional original fullname from API (used for stations)
  normalized_name: string; // Normalized name provided by backend for searching
}
