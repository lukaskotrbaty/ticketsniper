# Frontend Architecture (Vue.js)

This document describes the structure and key aspects of the frontend application built on Vue.js.

## 1. Technologies and Libraries

*   **Framework:** Vue.js 3 (with Composition API for better logic organization)
*   **Router:** Vue Router 4
*   **State Management:** Pinia (official, lightweight and intuitive state management for Vue 3)
*   **HTTP Client:** Axios (for Backend API communication)
*   **UI Components/Styling:** Recommendation: Tailwind CSS (utility-first) or Vuetify (material design components). Choice depends on preferences.
*   **Form Validation:** VeeValidate or built-in HTML5 validation with custom logic.
*   **Utility:** Lodash-es (e.g., for `debounce`)

## 2. Project Structure (Current)

```text
/src
|-- components/      # Reusable UI components
|   |-- monitoring/  # Components for monitoring display and management
|       |-- AvailableRoutesSelect.vue
|       |-- LocationAutocomplete.vue
|       |-- MonitoringForm.vue
|       |-- MonitoringList.vue
|-- views/           # Application pages (composed of components)
|   |-- DashboardPage.vue
|   |-- EmailConfirmationPage.vue
|   |-- LoginPage.vue
|   |-- NotFoundPage.vue
|   |-- RegisterPage.vue
|-- router/          # Vue Router configuration
|   |-- index.ts
|-- stores/          # Pinia stores (state management)
|   |-- auth.ts      # State and actions for authentication (user, token)
|   |-- monitoring.ts # State and actions for monitored routes and form
|-- services/        # Logic for API communication
|   |-- apiClient.ts # Axios instance with interceptors (for JWT and error handling)
|   |-- authService.ts
|   |-- dataService.ts # Service for calling /data endpoints (locations)
|   |-- monitoringService.ts # Service for calling /routes endpoints (available, monitor, monitored)
|-- types/           # TypeScript type definitions
|   |-- availableRoute.ts
|   |-- location.ts
|-- App.vue          # Main application component
|-- main.ts          # Application entry point (Vue, Pinia, Router initialization)
|-- style.css        # Global styles
```

## 3. Key Components and Views

*   **`LoginPage.vue`:** Login form that calls `authService.login` and stores token via Pinia store.
*   **`RegisterPage.vue`:** Registration form that calls `authService.register`. Displays informational message about the need for email confirmation.
*   **`EmailConfirmationPage.vue`:** Displays message about email confirmation status (success/failure), calls `authService.confirmEmail` on load (if token is in URL).
*   **`DashboardPage.vue`:** Main page for logged-in users. Contains:
    *   `MonitoringForm.vue` for entering new routes.
    *   `MonitoringList.vue` for displaying active and past monitored routes.
*   **`MonitoringForm.vue`:** Component implementing **hybrid UX flow**:
    *   Displays "From", "To" fields (uses `LocationAutocomplete.vue`), "Date".
    *   Once these 3 fields are filled, triggers loading of available connections (calls store action).
    *   Displays `AvailableRoutesSelect.vue` (or similar component) for selecting specific departure time (active/visible only after loading connections). Shows loading indicator.
    *   Contains fields for selecting Fares and Preferred classes (may be visible always or activated after time selection).
    *   Contains "Start monitoring" button that is active only after filling all required fields (including time).
    *   On submit calls `startMonitoring` action in store.
    *   Processes and displays error/success messages (e.g., toast notifications or messages directly in form).
*   **`LocationAutocomplete.vue`:** Reusable component for input with location autocomplete. Calls (with debouncing) `dataService.getLocations(query)` and displays results. On selection emits object `{id, name, type}`. Shows error on loading failure below input field.
*   **`AvailableRoutesSelect.vue`:** Component (list of clickable items) displaying available connections (departure time, arrival time, free seats) and allowing selection of one. On selection emits unique `routeId` of selected connection. Visually distinguishes sold-out connections.
*   **`MonitoringList.vue`:** Displays list of routes obtained from `monitoring.ts` store. Shows route status (Active/Found).

## 4. State Management (Pinia)

*   **`auth.ts` store:**
    *   `state`: `user` (object with user info or null), `token` (JWT or null), `isAuthenticated` (boolean).
    *   `actions`: `login`, `register`, `logout`, `confirmEmail`, `loadUserFromLocalStorage`.
    *   `getters`: `isAuthenticated`.
*   **`monitoring.ts` store:**
    *   `state`: `monitoredRoutes` (array of objects), `isLoadingRoutes` (boolean), `availableRoutes` (array of `AvailableRoute` objects), `isLoadingAvailableRoutes` (boolean), `availableRoutesError` (string/null), `formState` (reactive object with `fromLocation`, `toLocation`, `departureDate`, `selectedRouteId`).
    *   `actions`: `fetchMonitoredRoutes`, `fetchAvailableRoutes(params)`, `startMonitoring(formData)`, `setFromLocation`, `setToLocation`, `setDepartureDate`, `setSelectedRouteId`.
    *   `getters`: `activeRoutes`, `inactiveRoutes`, `canFetchAvailableRoutes`.

## 5. API Communication

*   **`apiClient.ts`:** Creates Axios instance.
    *   Sets `baseURL` to Backend API address.
    *   Adds interceptor for outgoing requests that automatically attaches `Authorization: Bearer <token>` header if token is stored in Pinia store.
    *   Adds interceptor for incoming responses for global error handling (e.g., unauthorized access 401 -> user logout, other errors -> notification display).
*   **`authService.ts`, `monitoringService.ts`:** Contain functions that use `apiClient` to call specific Backend API endpoints. Encapsulate HTTP request logic.
*   **`dataService.ts`:** New service containing `getLocations(query)` function calling `GET /data/locations`.
*   **`monitoringService.ts`:** Extended/modified service:
    *   `getAvailableRoutes(params)`: Calls `GET /routes/available`.
    *   `startMonitoring(data)`: Calls `POST /routes/monitor`.
    *   `getMonitoredRoutes()`: Calls `GET /routes/monitored`.

## 6. Input Validation

*   Occurs on FE (for UX) and BE (for security/integrity).
*   FE validation in `MonitoringForm.vue` checks required field completion (including time selection) and formats.
*   Should validate formats (date, time, email), required fields and possibly logical relationships (date must not be in the past, etc.).

## 7. Routing

*   Vue Router will manage navigation between pages (`LoginPage`, `RegisterPage`, `DashboardPage`, etc.).
*   Implement navigation guards (`beforeEach`) to protect pages requiring login (e.g., `DashboardPage`). If user is not logged in (check `auth.ts` store), they will be redirected to `LoginPage`.