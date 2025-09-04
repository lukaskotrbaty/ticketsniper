import { defineStore } from 'pinia';
import apiClient from '@/services/apiClient';
import router from '@/router'; // Assuming router is exported from index.ts
import { isAxiosError } from 'axios';

// Define interfaces for User and AuthState based on backend schemas (adjust as needed)
interface User {
  id: number;
  email: string;
  is_verified: boolean;
  // Add other relevant user fields if returned by /auth/me
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean; // To track loading state for async actions
  error: string | null; // To store error messages
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: localStorage.getItem('authToken') || null, // Load token from localStorage
    user: null,
    isAuthenticated: false, // Will be set by checkAuth or login
    loading: false,
    error: null,
  }),
  getters: {
    isLoggedIn: (state): boolean => state.isAuthenticated,
    currentUser: (state): User | null => state.user,
    isLoading: (state): boolean => state.loading,
    authError: (state): string | null => state.error,
  },
  actions: {
    setLoading(loading: boolean) {
      this.loading = loading;
    },
    setError(error: string | null) {
      this.error = error;
    },
    setAuthData(token: string, user: User | null = null) {
      this.token = token;
      this.user = user; // User might be fetched separately
      this.isAuthenticated = true;
      localStorage.setItem('authToken', token); // Save token
      this.setError(null); // Clear previous errors
    },
    clearAuthData() {
      this.token = null;
      this.user = null;
      this.isAuthenticated = false;
      localStorage.removeItem('authToken'); // Remove token
      this.setError(null);
    },

    async login(credentials: { email: string; password: string }): Promise<boolean> {
      this.setLoading(true);
      this.setError(null);
      try {
        // FastAPI's OAuth2PasswordRequestForm expects form data
        const formData = new URLSearchParams();
        formData.append('username', credentials.email); // 'username' is the default field name
        formData.append('password', credentials.password);

        const response = await apiClient.post<{ access_token: string }>('/auth/login', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });

        const token = response.data.access_token;
        this.setAuthData(token);

        // Fetch user data after successful login
        await this.fetchCurrentUser();

        this.setLoading(false);
        return true; // Indicate success
      } catch (err: unknown) {
       console.error('Login failed:', err);
       this.clearAuthData();

       let errorMessage = 'Přihlášení selhalo. Zkuste to prosím znovu.'; // Default generic error

       if (isAxiosError(err)) {
         if (err.code === 'ERR_NETWORK') {
           errorMessage = 'Nelze se připojit k serveru. Zkontrolujte prosím své internetové připojení nebo to zkuste později.';
         } else if (err.response?.data?.detail) {
           errorMessage = err.response.data.detail;
         } else if (err.response?.status === 401) {
            errorMessage = 'Nesprávný email nebo heslo.';
         }
       }

       this.setError(errorMessage);
       this.setLoading(false);
       return false; // Indicate failure
      }
    },

    async fetchCurrentUser(): Promise<void> {
       if (!this.token) return; // No need to fetch if not logged in

       // No need to set loading here if called after login which already sets it
       // this.setLoading(true);
       try {
         const response = await apiClient.get<User>('/auth/me');
         this.user = response.data;
         this.isAuthenticated = true; // Ensure authenticated state is true
       } catch (err: any) {
         console.error('Failed to fetch current user:', err); // Keep error log
         // If fetching user fails (e.g., token expired), log out
         this.logout();
       }
    },

    logout(): void {
      this.clearAuthData();
      // Redirect to login page
      router.push('/login').catch((err: unknown) => {
        // Basic error handling for unknown type
        if (err instanceof Error) {
          console.error('Router push error:', err.message);
        } else {
          console.error('An unknown router push error occurred:', err);
        }
      });
    },

    // Action to check auth status on app load
    async checkAuth(): Promise<void> {
      if (this.token) { // Token loaded from localStorage in state definition
        this.setLoading(true); // Set loading for the initial check
        await this.fetchCurrentUser();
        this.setLoading(false); // Set loading false after check completes
      } else {
        this.clearAuthData(); // Ensure clean state if no token
      }
    }
  }
});
