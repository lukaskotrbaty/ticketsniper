import apiClient from './apiClient';
import type { Location } from '@/types/location'; // Assuming types are defined in @/types

/**
 * Fetches locations from the backend API.
 * @param query Optional query string for filtering locations by name.
 * @returns A promise that resolves to an array of Location objects.
 */
async function getLocations(query?: string): Promise<Location[]> {
  try {
    const params = query ? { query } : {};
    const response = await apiClient.get<Location[]>('/data/locations', { params });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching locations:', error);
    // Re-throw or handle error as needed in the component/store
    throw new Error(error.response?.data?.detail || 'Nepodařilo se načíst lokace');
  }
}

export default {
  getLocations,
};
