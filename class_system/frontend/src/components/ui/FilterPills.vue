<template>
  <div class="filter-pills">
    <button
      v-for="item in items"
      :key="item.value"
      type="button"
      class="filter-pill"
      :class="{ active: modelValue === item.value }"
      @click="$emit('update:modelValue', item.value)"
    >
      {{ item.label }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  items: {
    type: Array,
    default: () => []
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.filter-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-pill {
  min-height: 38px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(37,99,235,0.14);
  background: rgba(255,255,255,0.90);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
  transition: var(--transition-standard);
  box-shadow: var(--shadow-xs);
}

.filter-pill:hover {
  color: var(--text-primary);
  border-color: rgba(37,99,235,0.28);
  background: rgba(255,255,255,0.98);
}

.filter-pill.active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, var(--brand-500), var(--amber-500));
  box-shadow: 0 8px 20px rgba(37,99,235,0.22);
}
</style>
