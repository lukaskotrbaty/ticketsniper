import apiClient from './apiClient';
import { isAxiosError } from 'axios';
import type { AxiosError } from 'axios';

// Request/response data interfaces based on backend schemas
interface RegisterData {
  email: string;
  password: string;
  password_confirm: string; // Added confirmation field
}

interface LoginCredentials {
  email: string;
  password: string;
}

// Specific type for API error responses (FastAPI specific structure)
interface ApiErrorDetail {
    detail: string | { msg: string; type: string }[];
}

// Function to extract a user-friendly error message from various error types
function getErrorMessage(error: unknown): string {
    if (typeof error === 'object' && error !== null && 'response' in error) {
        const axiosError = error as AxiosError<ApiErrorDetail>;
        if (axiosError.response?.data?.detail) {
            const detail = axiosError.response.data.detail;
            if (typeof detail === 'string') {
                return detail; // Simple string error
            } else if (Array.isArray(detail) && detail.length > 0 && typeof detail[0].msg === 'string') {
                // Handle FastAPI validation errors (potentially multiple)
                return detail.map(d => d.msg).join(', ');
            }
        }
    }
    if (error instanceof Error) {
        return error.message;
    }
    return 'Vyskytla se neznámá chyba.';
}


export const authService = {
  async register(userData: RegisterData): Promise<{ success: boolean; message: string }> {
    try {
      // Backend expects JSON including password_confirm now
      const response = await apiClient.post('auth/register', userData);
      // Assuming backend returns a success message or User object
      // For register, a generic message is often better until email is confirmed
      return { success: true, message: 'Registrace zahájena. Zkontrolujte prosím svůj e-mail pro potvrzení.' };
    } catch (error: unknown) {
      let message = 'Registrace se nezdařila.';

      if (isAxiosError(error)) {
        if (error.code === 'ERR_NETWORK') {
          message = 'Nelze se připojit k serveru. Zkontrolujte prosím své internetové připojení nebo to zkuste znovu později.';
        } else {
          message = getErrorMessage(error);
        }
      } else if (error instanceof Error) {
        message = error.message;
      }

      console.error('Registration failed:', error); // Keep original error log
      return { success: false, message };
    }
  },

  // Note: Login logic is handled directly in the Pinia store (useAuthStore.login)
  // because it needs to directly manipulate the store's state (token, user).

  async confirmEmail(token: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.get(`auth/confirm/${token}`);
      return { success: true, message: response.data?.message || 'E-mail byl úspěšně potvrzen. Nyní se můžete přihlásit.' };
    } catch (error: unknown) {
      const message = getErrorMessage(error); // Handles invalid/expired token errors from backend
      console.error('Email confirmation failed:', message);
      return { success: false, message };
    }
  },

  async requestPasswordReset(email: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.post('auth/request-password-reset', { email });
      return { success: true, message: response.data?.message || 'Žádost o resetování hesla byla odeslána.' };
    } catch (error: unknown) {
      let message = 'Žádost o resetování hesla se nezdařila.';
      if (isAxiosError(error) && error.code === 'ERR_NETWORK') {
        message = 'Nelze se připojit k serveru. Zkontrolujte prosím své internetové připojení nebo to zkuste znovu později.';
      } else {
        message = getErrorMessage(error);
      }
      console.error('Password reset request failed:', error);
      return { success: false, message };
    }
  },

  async confirmPasswordReset(token: string, newPassword: string): Promise<{ success: boolean; message: string }> {
      try {
          const response = await apiClient.post('auth/reset-password', {
              token: token,
              new_password: newPassword,
          });
          return {success: true, message: response.data?.message || 'Heslo bylo úspěšně resetováno.'};
      } catch (error: unknown) {
          let message = 'Nastavení nového hesla se nezdařilo.';
          if (isAxiosError(error)) {
              if (error.code === 'ERR_NETWORK') {
                  message = 'Nelze se připojit k serveru. Zkontrolujte prosím své internetové připojení nebo to zkuste znovu později.';
              } else {
                  message = getErrorMessage(error);
              }
          } else if (error instanceof Error) {
              message = error.message;
          }
          console.error('Password reset confirmation failed:', error);
          return {success: false, message};
      }
  }
};
