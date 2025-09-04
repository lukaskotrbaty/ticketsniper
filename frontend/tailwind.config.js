/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#2563EB', // blue-600
        'primary-dark': '#1D4ED8', // blue-700
        'primary-light': '#3B82F6', // blue-500
        'primary-lighter': '#EFF6FF', // blue-50
        'text-primary': '#111827', // gray-900
        'text-secondary': '#4B5563', // gray-600
        'text-muted': '#9CA3AF', // gray-400
        'text-on-primary': '#FFFFFF', // white
        'background-body': '#F9FAFB', // gray-50
        'background-card': '#FFFFFF', // white
        'background-alt': '#F3F4F6', // gray-100
        'background-footer': '#1F2937', // gray-800
        'gradient-indigo-start': '#DBEAFE', // blue-200 
        'gradient-indigo-end': '#C7D2FE',   // indigo-200

        'error': '#DC2626', // red-600
        'error-dark': '#B91C1C', // red-700
        'background-error-lighter': '#FEF2F2', // red-50
        'background-error-light': '#FEE2E2', // red-100
        'border-error-light': '#FECACA', // red-200
        'border-error': '#EF4444', // red-500

        'success': '#047857', // green-700
        'success-dark': '#065F46', // green-800
        'background-success-lighter': '#ECFDF5', // green-50
        'background-success-light': '#D1FAE5', // green-100

        'warning-dark': '#9A3412', // yellow-800
        'background-warning-lighter': '#FEF9C3', // yellow-100

        'border-neutral': '#D1D5DB', // gray-300
        'border-neutral-light': '#E5E7EB', // gray-200
      }
    },
  },
  plugins: [],
}
