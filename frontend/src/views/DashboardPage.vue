<template>
  <div class="max-w-4xl p-6 mx-auto bg-background-card rounded-lg shadow-md">
    <div v-if="currentUser" class="mb-6">
      <p class="text-text-secondary">Vítejte, <strong class="text-text-primary">{{ currentUser.email }}</strong>!</p>
      <!-- Add more dashboard content here later -->
    </div>

    <!-- Monitoring Form Section -->
    <MonitoringForm class="mt-8"/>

    <!-- Monitoring List Section -->
    <MonitoringList class="mt-8"/>

  </div>
</template>

<script setup lang="ts">
import {computed, onMounted} from 'vue';
import {useAuthStore} from '@/stores/auth';
import {useMonitoringStore} from '@/stores/monitoring';
import MonitoringForm from '@/components/monitoring/MonitoringForm.vue';
import MonitoringList from '@/components/monitoring/MonitoringList.vue';

const authStore = useAuthStore();
const monitoringStore = useMonitoringStore();

const currentUser = computed(() => authStore.currentUser);

// Fetch monitored routes when the component mounts
onMounted(() => {
  monitoringStore.fetchMonitoredRoutes();
});
</script>
