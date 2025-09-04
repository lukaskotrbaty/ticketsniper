import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

// Define routes
const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('@/views/LandingPage.vue'), // Lazy load LandingPage
    meta: { requiresGuest: true } // Show only to non-logged-in users
  },
  {
    path: '/login',
    name: 'Login',
    // component: LoginPage,
    component: () => import('@/views/LoginPage.vue'), // Lazy load component
    meta: { requiresGuest: true } // Only accessible to guests (not logged in)
  },
  {
    path: '/register',
    name: 'Register',
    // component: RegisterPage,
    component: () => import('@/views/RegisterPage.vue'), // Lazy load component
    meta: { requiresGuest: true } // Only accessible to guests
  },
  {
    path: '/confirm-email', // Or '/confirm-email/:token' if token is part of path
    name: 'EmailConfirmation',
    // component: EmailConfirmationPage,
    component: () => import('@/views/EmailConfirmationPage.vue'), // Lazy load component
    // No specific meta needed unless we want to restrict access
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    // component: DashboardPage,
    component: () => import('@/views/DashboardPage.vue'), // Lazy load component
    meta: { requiresAuth: true } // Requires authentication
    // alias: [''] // Removed alias, root path '/' is now the LandingPage for guests
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPasswordPage.vue'), // Lazy load
    meta: { requiresGuest: true } // Only for guests
  },
  {
    path: '/reset-password/:token', // Token as path parameter
    name: 'ResetPassword',
    component: () => import('@/views/ResetPasswordPage.vue'), // Lazy load
    meta: { requiresGuest: true } // Only for guests
  },
  // Catch-all 404 route MUST BE LAST
  {
    path: '/:pathMatch(.*)*', // Matches any path not matched above
    name: 'NotFound',
    component: () => import('@/views/NotFoundPage.vue') // Lazy load NotFoundPage
  }
];

// Create router instance
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Navigation Guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  // Check meta directly on the target route 'to'
  const requiresAuth = to.meta.requiresAuth === true;
  const requiresGuest = to.meta.requiresGuest === true;

  if (requiresAuth && !authStore.isLoggedIn) {
    // Redirect to login if trying to access protected route without being logged in
    next({ name: 'Login' });
  } else if (requiresGuest && authStore.isLoggedIn) {
    // Redirect to dashboard if trying to access guest route while logged in
    if (to.name === 'Landing') {
      next(); // Allow going to Landing page
    } else {
      next({ name: 'Dashboard' }); // Redirect other guest pages (Login, Register...) to Dashboard
    }
  } else {
    // Otherwise, allow navigation
    next();
  }
});


export default router;
