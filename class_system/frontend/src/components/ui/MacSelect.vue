<template>
  <div ref="rootRef" class="mac-select">
    <label v-if="label" class="mac-select__label">{{ label }}</label>
    <button
      type="button"
      class="mac-select__trigger"
      :class="{ 'is-open': open }"
      :aria-expanded="open"
      @click="toggle"
    >
      <span class="mac-select__value">{{ currentLabel }}</span>
      <svg class="mac-select__chev" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m6 9 6 6 6-6"/>
      </svg>
    </button>
    <transition name="mac-select-drop">
      <ul v-show="open" class="mac-select__menu" role="listbox">
        <li
          v-for="opt in options"
          :key="String(opt.value)"
          class="mac-select__option"
          role="option"
          :aria-selected="opt.value === modelValue"
          :class="{ 'is-selected': opt.value === modelValue }"
          @click="choose(opt)"
        >
          <span class="mac-select__option-label">{{ opt.label }}</span>
          <span v-if="opt.desc" class="mac-select__option-desc">{{ opt.desc }}</span>
        </li>
      </ul>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number], required: true },
  options: {
    type: Array,
    required: true
    // { value, label }[]
  },
  label: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue'])

const rootRef = ref(null)
const open = ref(false)

const currentLabel = computed(() => {
  const o = props.options.find((x) => x.value === props.modelValue)
  return o ? o.label : String(props.modelValue)
})

function toggle() {
  open.value = !open.value
}

function close() {
  open.value = false
}

function choose(opt) {
  emit('update:modelValue', opt.value)
  close()
}

function onDocPointerDown(e) {
  if (!open.value) return
  const el = rootRef.value
  if (el && !el.contains(e.target)) close()
}

onMounted(() => {
  document.addEventListener('mousedown', onDocPointerDown)
})
onUnmounted(() => {
  document.removeEventListener('mousedown', onDocPointerDown)
})
</script>

<style scoped>
.mac-select {
  position: relative;
  width: 100%;
}

.mac-select__label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #6e6e73;
  margin-bottom: 8px;
}

.mac-select__trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  font-size: 13px;
  font-family: inherit;
  color: #1d1d1f;
  background: #fff;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.mac-select__trigger:hover {
  border-color: rgba(0, 0, 0, 0.18);
  background: #fafafa;
}

.mac-select__trigger.is-open,
.mac-select__trigger:focus-visible {
  outline: none;
  border-color: #007aff;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
  background: #fff;
}

.mac-select__value {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mac-select__chev {
  flex-shrink: 0;
  color: #007aff;
  transition: transform 0.2s ease;
}

.mac-select__trigger.is-open .mac-select__chev {
  transform: rotate(180deg);
}

.mac-select__menu {
  position: absolute;
  left: 0;
  right: 0;
  top: calc(100% + 6px);
  z-index: 50;
  margin: 0;
  padding: 6px;
  list-style: none;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(0, 0, 0, 0.04);
  max-height: 360px;
  overflow-y: auto;
}

.mac-select__option {
  padding: 10px 12px;
  font-size: 13px;
  color: #1d1d1f;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.mac-select__option-label {
  display: block;
  font-weight: 500;
  margin-bottom: 2px;
}

.mac-select__option-desc {
  display: block;
  font-size: 11px;
  color: #86868b;
  line-height: 1.4;
}

.mac-select__option:hover {
  background: #007aff;
  color: #fff;
}

.mac-select__option:hover .mac-select__option-desc {
  color: rgba(255, 255, 255, 0.8);
}

.mac-select__option.is-selected {
  background: rgba(0, 122, 255, 0.12);
  color: #007aff;
  font-weight: 500;
}

.mac-select__option.is-selected:hover {
  background: #007aff;
  color: #fff;
}

.mac-select-drop-enter-active,
.mac-select-drop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.mac-select-drop-enter-from,
.mac-select-drop-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
