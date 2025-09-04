<template>
  <div class="relative">
    <label :for="inputId" class="block text-sm font-medium text-text-secondary mb-1">{{ label }}</label>
    <input
      :id="inputId"
      type="text"
      v-model="searchQuery"
      @blur="onBlur"
      @focus="showSuggestions = true"
      :placeholder="placeholder"
      autocomplete="off"
      class="mt-1 block w-full px-3 py-2 border border-border-neutral rounded-md shadow-sm focus:outline-none focus:ring-primary-light focus:border-primary-light sm:text-sm"
      :class="{ 'border-error': error }"
    />
    <!-- Error message displayed below input -->
    <p v-if="error && !showSuggestions" class="mt-1 text-xs text-error">{{ error }}</p>
    <!-- Suggestion dropdown -->
    <div
      v-if="showSuggestions && (filteredSuggestions.length > 0 || error)"
      class="absolute z-10 mt-1 w-full bg-background-card shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm"
    >
      <!-- Use computed loading/error state -->
      <div v-if="error" class="px-4 py-2 text-sm text-error">{{ error }}</div>
      <!-- Iterate over computed suggestions -->
      <ul v-else-if="filteredSuggestions.length > 0">
        <li
          v-for="suggestion in filteredSuggestions"
          :key="suggestion.id"
          @mousedown.prevent="selectSuggestion(suggestion)"
          class="cursor-pointer select-none relative py-2 pl-3 pr-9 text-text-primary hover:bg-primary hover:text-text-on-primary"
        >
          <span class="block truncate">{{ suggestion.name }}</span>
        </li>
      </ul>
      <!-- Optional: Message when query is typed but no results -->
      <div v-else-if="searchQuery.length > 0" class="px-4 py-2 text-sm text-text-muted">Nebyly nalezeny žádné lokace.</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import { useMonitoringStore } from '@/stores/monitoring'; 
import type { Location } from '@/types/location';
import { normalizeString } from '@/utils/stringUtils';

// --- Store Setup ---
const monitoringStore = useMonitoringStore();

// --- Props ---
interface Props {
  modelValue: Location | null;
  label: string;
  placeholder?: string;
  inputId: string; // Required for label association
}

const props = defineProps<Props>();
const emit = defineEmits(['update:modelValue']);

const searchQuery = ref(props.modelValue?.name || '');
const suggestions = ref<Location[]>([]);
const error = ref<string | null>(null); // Keep error for potential loading errors from store
const showSuggestions = ref(false);

// --- Filtering Logic --- UPDATED
const filteredSuggestions = computed<Location[]>(() => {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    return [];
  }

  // Normalize only the user input
  const normalizedQuery = normalizeString(searchQuery.value);

  // Filter based on the pre-normalized name from backend
  const results = monitoringStore.allLocations.filter(location =>
    // Ensure location and normalized_name exist before calling includes
    location && location.normalized_name && location.normalized_name.includes(normalizedQuery)
  );

  return results.slice(0, 10);
});

// Watch for changes in the search query
watch(searchQuery, (newValue) => {
  // If the new value doesn't match the selected model's name, clear selection
  if (!props.modelValue || newValue !== props.modelValue.name) {
    emit('update:modelValue', null);
  }
  // Show suggestions whenever user types, filtering is handled by computed property
  if (newValue !== '') {
     showSuggestions.value = true;
     // Ensure locations are loaded if not already
     if (monitoringStore.allLocations.length === 0 && !monitoringStore.isLoadingAllLocations) {
       monitoringStore.fetchAllLocations(); // Trigger fetch if needed
     }
  } else {
     showSuggestions.value = false; // Hide if input is empty
     error.value = null; // Clear local error display
  }
});

function selectSuggestion(suggestion: Location) {
  searchQuery.value = suggestion.name; // Update input field
  emit('update:modelValue', suggestion); // Emit selected location object
  showSuggestions.value = false; // Hide suggestions
  error.value = null; // Clear local error display
}

function onBlur() {
  // Hide suggestions after a short delay to allow click event on suggestions
  setTimeout(() => {
    showSuggestions.value = false;
  }, 150);
}

// Sync input field if modelValue changes externally
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    searchQuery.value = newValue.name;
  } else if (!showSuggestions.value) { // Avoid clearing input if user is actively searching
     searchQuery.value = '';
  }
});

</script>
