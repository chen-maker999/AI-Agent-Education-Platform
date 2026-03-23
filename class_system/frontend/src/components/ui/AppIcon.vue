<template>
  <svg
    class="app-icon"
    :style="{ width: `${size}px`, height: `${size}px` }"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.9"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <component
      :is="shape.tag"
      v-for="(shape, index) in iconShapes"
      :key="`${name}-${index}`"
      v-bind="shape.attrs"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    default: 'spark'
  },
  size: {
    type: Number,
    default: 18
  }
})

const icons = {
  search: [
    { tag: 'circle', attrs: { cx: 11, cy: 11, r: 6.5 } },
    { tag: 'path', attrs: { d: 'm20 20-3.4-3.4' } }
  ],
  spark: [{ tag: 'path', attrs: { d: 'M12 2 9.4 9.4 2 12l7.4 2.6L12 22l2.6-7.4L22 12l-7.4-2.6L12 2Z' } }],
  compass: [
    { tag: 'circle', attrs: { cx: 12, cy: 12, r: 8.5 } },
    { tag: 'path', attrs: { d: 'm14.8 9.2-2.2 5.8-5.8 2.2 2.2-5.8 5.8-2.2Z' } }
  ],
  database: [
    { tag: 'ellipse', attrs: { cx: 12, cy: 5.5, rx: 7, ry: 3 } },
    { tag: 'path', attrs: { d: 'M5 5.5v6.8c0 1.7 3.1 3 7 3s7-1.3 7-3V5.5' } },
    { tag: 'path', attrs: { d: 'M5 12.3v6.2c0 1.7 3.1 3 7 3s7-1.3 7-3v-6.2' } }
  ],
  graph: [
    { tag: 'circle', attrs: { cx: 5, cy: 7, r: 1.8 } },
    { tag: 'circle', attrs: { cx: 18.5, cy: 5.5, r: 1.8 } },
    { tag: 'circle', attrs: { cx: 8, cy: 18, r: 1.8 } },
    { tag: 'circle', attrs: { cx: 18.5, cy: 17.5, r: 1.8 } },
    { tag: 'path', attrs: { d: 'M6.6 8 10.5 16.2M9.7 17.6h7M6.7 6.8 16.7 5.8M18.3 7.3v8.4' } }
  ],
  file: [
    { tag: 'path', attrs: { d: 'M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z' } },
    { tag: 'path', attrs: { d: 'M14 3v5h5M9 13h6M9 17h4' } }
  ],
  chart: [{ tag: 'path', attrs: { d: 'M4 20h16M7 16v-5M12 16V8M17 16v-9' } }],
  user: [
    { tag: 'circle', attrs: { cx: 12, cy: 8, r: 3.5 } },
    { tag: 'path', attrs: { d: 'M5 20a7 7 0 0 1 14 0' } }
  ],
  alert: [
    { tag: 'path', attrs: { d: 'M12 4 21 20H3L12 4Z' } },
    { tag: 'path', attrs: { d: 'M12 10v4M12 17.2h.01' } }
  ],
  settings: [
    { tag: 'circle', attrs: { cx: 12, cy: 12, r: 3 } },
    { tag: 'path', attrs: { d: 'M19 12a7 7 0 0 0-.1-1l2-1.5-2-3.5-2.4.8a8 8 0 0 0-1.8-1l-.3-2.5h-4l-.3 2.5a8 8 0 0 0-1.8 1L5 6l-2 3.5L5 11a8 8 0 0 0 0 2l-2 1.5L5 18l2.4-.8a8 8 0 0 0 1.8 1l.3 2.5h4l.3-2.5a8 8 0 0 0 1.8-1L19 18l2-3.5-2-1.5c.1-.3.1-.7.1-1Z' } }
  ],
  layout: [
    { tag: 'rect', attrs: { x: 3, y: 4, width: 18, height: 16, rx: 2.5 } },
    { tag: 'path', attrs: { d: 'M9 4v16M3 10h6' } }
  ],
  plug: [{ tag: 'path', attrs: { d: 'M9 3v5M15 3v5M8 8h8v3a4 4 0 0 1-4 4h0a4 4 0 0 1-4-4V8ZM12 15v6' } }],
  arrowRight: [{ tag: 'path', attrs: { d: 'M5 12h14M13 6l6 6-6 6' } }],
  plus: [{ tag: 'path', attrs: { d: 'M12 5v14M5 12h14' } }],
  upload: [{ tag: 'path', attrs: { d: 'M12 15V4M8 8l4-4 4 4M5 19h14' } }],
  send: [{ tag: 'path', attrs: { d: 'm21 3-8 18-2.3-7.7L3 11l18-8Z' } }],
  book: [
    { tag: 'path', attrs: { d: 'M5 5.5A2.5 2.5 0 0 1 7.5 3H20v17H7.5A2.5 2.5 0 0 0 5 22Z' } },
    { tag: 'path', attrs: { d: 'M5 5.5V20' } }
  ],
  check: [{ tag: 'path', attrs: { d: 'm5 13 4 4L19 7' } }],
  orbit: [
    { tag: 'circle', attrs: { cx: 12, cy: 12, r: 8 } },
    { tag: 'circle', attrs: { cx: 18, cy: 8, r: 2 } },
    { tag: 'path', attrs: { d: 'M12 4a8 8 0 0 1 6 3' } }
  ],
  radar: [
    { tag: 'path', attrs: { d: 'M12 12 20 7' } },
    { tag: 'path', attrs: { d: 'M12 12 18 18' } },
    { tag: 'circle', attrs: { cx: 12, cy: 12, r: 8 } },
    { tag: 'circle', attrs: { cx: 12, cy: 12, r: 2 } }
  ],
  flash: [{ tag: 'path', attrs: { d: 'M13 2 4 14h6l-1 8 9-12h-6l1-8Z' } }],
  layers: [
    { tag: 'path', attrs: { d: 'm12 4 8 4-8 4-8-4 8-4Z' } },
    { tag: 'path', attrs: { d: 'm4 12 8 4 8-4' } },
    { tag: 'path', attrs: { d: 'm4 16 8 4 8-4' } }
  ],
  route: [
    { tag: 'circle', attrs: { cx: 6, cy: 18, r: 2 } },
    { tag: 'circle', attrs: { cx: 18, cy: 6, r: 2 } },
    { tag: 'path', attrs: { d: 'M8 17c1-6 6-10 10-10' } }
  ],
  clock: [
    { tag: 'circle', attrs: { cx: 12, cy: 12, r: 8.5 } },
    { tag: 'path', attrs: { d: 'M12 7v5l3 2' } }
  ]
}

const iconShapes = computed(() => icons[props.name] || icons.spark)
</script>

<style scoped>
.app-icon {
  flex: 0 0 auto;
}
</style>
