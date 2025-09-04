<script setup lang="ts">
import { useRoute } from 'vue-router';
import Header from '@/components/layout/Header.vue';

const route = useRoute();
</script>

<template>
  <div>
    <Header />
    <main class="container mx-auto p-4">
      <router-view></router-view>
    </main>
  </div>
</template>
