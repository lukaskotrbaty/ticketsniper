import axios, { type InternalAxiosRequestConfig, type AxiosResponse, type AxiosError } from 'axios';
// Import the auth store and router
import { useAuthStore } from '@/stores/auth';
import router from '@/router'; // Assuming router is exported from index.ts

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Add Authorization header
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    // Get store instance inside interceptor
    // Note: This might cause issues if Pinia is not fully initialized when apiClient is imported.
    // A more robust approach might involve initializing Pinia first or passing the store instance.
    // However, for many cases, this works.
    try {
      const authStore = useAuthStore();
      const token = authStore.token;
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
        console.warn("Pinia store not available yet for auth token injection.");
    }
    return config;
  },
  (error: AxiosError): Promise<AxiosError> => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle 401 Unauthorized
apiClient.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => response,
  (error: AxiosError): Promise<AxiosError> => {
    if (error.response && error.response.status === 401) {
      // Avoid infinite loops if the /auth/me call itself fails with 401 during checkAuth
      if (!error.config?.url?.endsWith('/auth/me')) {
          try {
            const authStore = useAuthStore();
            console.error('Unauthorized request (401), logging out.');
            authStore.logout(); // This action includes redirecting to login
          } catch (e) {
              console.error("Pinia store not available for logout on 401.");
              // Fallback redirect if store is unavailable
              router.push('/login').catch(err => console.error('Router push error:', err));
          }
      } else {
          console.warn('Ignoring 401 for /auth/me to prevent logout loop during initial check.');
          // If /auth/me fails with 401 during checkAuth, the store should handle clearing auth data.
      }
    }
    // Handle other errors globally if needed
    return Promise.reject(error);
  }
);

export default apiClient;
