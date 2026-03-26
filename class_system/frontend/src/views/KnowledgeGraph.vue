<template>
  <div class="kg-page">
    <!-- ============================================================
         macOS Window Card
    ============================================================ -->
    <div class="mac-window" role="application" aria-label="知识图谱">

      <!-- ── Title Bar ── -->
      <header class="titlebar">
        <div class="titlebar-title">知识图谱 — GRAPH WORKSPACE</div>
        <span class="titlebar-hint">可视化关系与路径</span>
      </header>

      <!-- ── Toolbar ── -->
      <div class="toolbar">
        <!-- Segmented control: view mode -->
        <div class="segmented" role="tablist" aria-label="视图模式">
          <button
            v-for="item in viewModes"
            :key="item.value"
            type="button"
            :id="item.id"
            :aria-pressed="activeView === item.value ? 'true' : 'false'"
            @click="activeView = item.value"
          >
            {{ item.label }}
          </button>
        </div>

        <!-- Layout -->
        <button type="button" class="tb-btn" title="重新布局" @click="onLayout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 5h16M4 12h16M4 19h16"/>
          </svg>
          布局
        </button>

        <div class="toolbar-spacer"></div>

        <!-- Canvas search -->
        <div class="search-field">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>
          </svg>
          <input
            v-model="searchQuery"
            type="search"
            placeholder="搜索知识点…"
            autocomplete="off"
          />
        </div>

        <!-- Sync -->
        <button type="button" class="tb-btn" title="同步数据" @click="onSync">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
          </svg>
          同步
        </button>
      </div>

      <!-- ── Three-column split ── -->
      <div class="split-root">

        <!-- LEFT: Sidebar — Finder-style -->
        <aside class="sidebar" aria-label="过滤器与图例">
          <div class="sidebar-header">域与筛选</div>

          <nav class="filter-list">
            <button
              v-for="chip in domainChips"
              :key="chip.value"
              type="button"
              class="filter-chip"
              :class="{ active: selectedDomain === chip.value }"
              @click="selectedDomain = chip.value"
            >
              {{ chip.label }}<span class="count">{{ chip.count }}</span>
            </button>
          </nav>

          <div class="sidebar-search">
            <div class="search-field">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>
              </svg>
              <input
                v-model="sidebarSearch"
                type="search"
                placeholder="侧栏过滤…"
                autocomplete="off"
              />
            </div>
          </div>

          <div class="sidebar-footer">
            <div class="stat-row">
              <span>节点总数</span>
              <strong>{{ visibleNodes.length }}</strong>
            </div>
            <div class="stat-row">
              <span>关系边</span>
              <strong>{{ visibleEdges.length }}</strong>
            </div>
          </div>
        </aside>

        <!-- MIDDLE: Canvas pane -->
        <section class="canvas-pane" aria-label="图谱画布">
          <div class="canvas-toolbar">
            <span class="canvas-title">画布</span>
            <span class="hint">拖拽平移 · 滚轮缩放 · 点击节点查看右侧详情</span>
          </div>

          <div class="canvas-body" @click.self="selectedNode = null">
            <div class="canvas-grid" aria-hidden="true"></div>

            <!-- Node cards -->
            <button
              v-for="node in visibleNodes"
              :key="node.id"
              type="button"
              class="canvas-node"
              :class="{ active: selectedNode?.id === node.id }"
              :style="{ left: node.x + '%', top: node.y + '%' }"
              @click.stop="selectedNode = node"
            >
              <span class="canvas-node__label">{{ node.label }}</span>
              <span class="canvas-node__domain">{{ node.domain }}</span>
            </button>

            <!-- Edge lines -->
            <svg class="canvas-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
              <line
                v-for="edge in visibleEdges"
                :key="edge.id"
                :x1="edge.x1"
                :y1="edge.y1"
                :x2="edge.x2"
                :y2="edge.y2"
                class="canvas-edge"
              />
            </svg>

            <!-- Empty placeholder -->
            <div v-if="visibleNodes.length === 0" class="canvas-placeholder">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
              </svg>
              <h3>图谱将在此渲染</h3>
              <p>导入课程知识后在此展示节点、边与先修路径。当前为占位画布。</p>
            </div>
          </div>
        </section>

        <!-- RIGHT: Inspector -->
        <aside class="inspector" aria-label="节点详情与路径">
          <div class="inspector-header">检查器</div>
          <div class="inspector-body">

            <!-- Empty state -->
            <div v-if="!selectedNode" class="inspector-empty">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <ellipse cx="12" cy="6" rx="8" ry="3"/>
                <path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/>
                <path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>
              </svg>
              <h4>选择一个知识点</h4>
              <p>在图谱中点击节点后，此处显示释义、难度、先修与后续建议动作。</p>
            </div>

            <!-- Node detail -->
            <div v-else>
              <div class="group-box">
                <h5>节点</h5>
                <div class="row"><span>名称</span><span>{{ selectedNode.label }}</span></div>
                <div class="row"><span>域</span><span>{{ selectedNode.domain }}</span></div>
                <div class="row"><span>难度</span><span>{{ selectedNode.difficulty }}</span></div>
              </div>

              <div class="group-box">
                <h5>路径</h5>
                <div class="row"><span>相关度</span><span>{{ selectedNode.relevance }}%</span></div>
              </div>

              <div v-if="selectedNode.related && selectedNode.related.length" class="group-box">
                <h5>关联知识</h5>
                <div v-for="rel in selectedNode.related" :key="rel" class="row">
                  <span>{{ rel }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="inspector-actions">
            <button type="button" class="btn" @click="onExport">导出子图</button>
            <button type="button" class="btn btn-primary" @click="onOpenCourse">关联课程</button>
          </div>
        </aside>
      </div>

      <!-- ── Status Bar ── -->
      <footer class="statusline">
        <span>就绪</span>
        <span class="sep">|</span>
        <span>视图：{{ viewLabel }}</span>
        <span class="sep">|</span>
        <span>筛选：{{ domainLabel }}</span>
      </footer>

    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { knowledgeApi } from '@/api'

// ── View mode ────────────────────────────────────────────────────────────────
const viewModes = [
  { id: 'viewGraph', label: '图谱', value: 'graph' },
  { id: 'viewList',  label: '列表', value: 'list'  },
  { id: 'viewPath',  label: '路径', value: 'path'  }
]
const activeView   = ref('graph')
const searchQuery  = ref('')
const sidebarSearch = ref('')

// ── Domain chips ─────────────────────────────────────────────────────────────
const selectedDomain = ref('all')

const domainChips = computed(() => {
  const all = [
    { label: '全部',    value: 'all',   count: '—'  },
    { label: 'Python', value: 'python', count: '0' },
    { label: 'Java',   value: 'java',   count: '0' },
    { label: '算法',   value: 'algo',   count: '0' },
    { label: '数据结构', value: 'ds',  count: '0' },
    { label: 'Web',    value: 'web',   count: '0' }
  ]
  // update counts from graph data
  all.forEach(chip => {
    if (chip.value !== 'all') {
      chip.count = allNodes.value.filter(n => n.domain === chip.label).length.toString()
    }
  })
  // update "all"
  const allNode = all.find(c => c.value === 'all')
  if (allNode) allNode.count = allNodes.value.length.toString()

  // sidebar search filter
  if (sidebarSearch.value.trim()) {
    const q = sidebarSearch.value.toLowerCase()
    return all.filter(c => c.label.toLowerCase().includes(q))
  }
  return all
})

// ── Graph data ────────────────────────────────────────────────────────────────
const allNodes   = ref([])
const allEdges   = ref([])
const selectedNode = ref(null)

// ── Computed: filtered nodes / edges ────────────────────────────────────────
const visibleNodes = computed(() =>
  allNodes.value.filter(node => {
    const domainOk = selectedDomain.value === 'all' || node.domain === selectedDomain.value
    const searchOk  = !searchQuery.value || node.label.includes(searchQuery.value)
    return domainOk && searchOk
  })
)

const visibleEdges = computed(() => {
  const ids = new Set(visibleNodes.value.map(n => n.id))
  return allEdges.value
    .filter(e => ids.has(e.from) && ids.has(e.to))
    .map(e => {
      const fx = allNodes.value.find(n => n.id === e.from)
      const tx = allNodes.value.find(n => n.id === e.to)
      return {
        ...e,
        x1: fx ? fx.x : 50,
        y1: fx ? fx.y : 50,
        x2: tx ? tx.x : 50,
        y2: tx ? tx.y : 50
      }
    })
})

// ── Status bar labels ────────────────────────────────────────────────────────
const viewLabel = computed(() => viewModes.find(v => v.value === activeView.value)?.label ?? '—')
const domainLabel = computed(() => domainChips.value.find(c => c.value === selectedDomain.value)?.label ?? '全部')

// ── Actions ──────────────────────────────────────────────────────────────────
function onLayout() {
  activeView.value = 'graph'
}
function onSync() {
  loadGraphData()
}
function onExport() {
  alert('演示：导出当前子图为 JSON / PNG。')
}
function onOpenCourse() {
  alert('演示：跳转到关联课程单元。')
}

// ── Load data ────────────────────────────────────────────────────────────────
async function loadGraphData() {
  try {
    const graphsRes = await knowledgeApi.graph.list()
    const graphs = graphsRes?.data?.items || graphsRes?.data || []
    const graphId = graphs[0]?.id || graphs[0]?.graph_id

    const [nodesRes, edgesRes] = await Promise.all([
      graphId ? knowledgeApi.graph.nodes(graphId) : Promise.resolve({ data: [] }),
      graphId ? knowledgeApi.graph.edges(graphId) : Promise.resolve({ data: [] })
    ])

    const rawNodes = nodesRes?.data?.items || nodesRes?.data || []
    const rawEdges = edgesRes?.data?.items || edgesRes?.data || []

    allNodes.value = rawNodes.map((node, i) => ({
      id:          node.id || node.node_id || `node_${i}`,
      label:       node.name || node.label || `节点 ${i + 1}`,
      description: node.description || '',
      domain:      node.domain || 'Python',
      difficulty:  node.difficulty || '基础',
      relevance:   node.relevance || 80,
      related:     node.related || [],
      x:           20 + (i % 4) * 22 + Math.random() * 8,
      y:           15 + Math.floor(i / 4) * 28 + Math.random() * 8
    }))

    allEdges.value = rawEdges.slice(0, 20).map((edge, i) => ({
      id:   edge.id || `edge_${i}`,
      from: edge.source || edge.from,
      to:   edge.target || edge.to
    }))

    if (allNodes.value.length > 0 && !selectedNode.value) {
      selectedNode.value = allNodes.value[0]
    }
  } catch {
    // Fallback demo data
    allNodes.value = [
      { id: 'a', label: '函数',       domain: 'Python',   difficulty: '基础',   relevance: 86, related: ['参数', '作用域'],       x: 20, y: 20 },
      { id: 'b', label: '递归',       domain: '算法',      difficulty: '进阶',   relevance: 82, related: ['树结构', '栈'],         x: 50, y: 12 },
      { id: 'c', label: '动态规划',   domain: '算法',      difficulty: '挑战',   relevance: 89, related: ['最优子结构', '递推'],   x: 75, y: 28 },
      { id: 'd', label: '面向对象',   domain: 'Java',      difficulty: '基础',   relevance: 78, related: ['类', '继承'],            x: 30, y: 55 },
      { id: 'e', label: 'HTTP 协议', domain: 'Web',       difficulty: '进阶',   relevance: 75, related: ['TCP', 'REST'],           x: 65, y: 60 },
      { id: 'f', label: '数据结构',   domain: '数据结构',  difficulty: '基础',   relevance: 90, related: ['数组', '链表'],         x: 48, y: 42 }
    ]
    allEdges.value = [
      { id: 'e1', from: 'a', to: 'b' },
      { id: 'e2', from: 'b', to: 'c' },
      { id: 'e3', from: 'd', to: 'b' },
      { id: 'e4', from: 'a', to: 'f' },
      { id: 'e5', from: 'f', to: 'e' },
      { id: 'e6', from: 'd', to: 'e' }
    ]
    selectedNode.value = allNodes.value[0]
  }
}

onMounted(() => {
  loadGraphData()
})
</script>

<style scoped>
/* ================================================================
   Page wrapper — centers the window card on the workspace
   ================================================================ */
.kg-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* ================================================================
   Design tokens (match knowledge-graph.html)
   ================================================================ */
.mac-window {
  --bg-window:       #ececec;
  --bg-content:      #f5f5f7;
  --bg-panel:        rgba(255, 255, 255, 0.72);
  --bg-panel-solid:  #ffffff;
  --bg-sidebar:       rgba(246, 246, 246, 0.85);
  --border:           rgba(0, 0, 0, 0.08);
  --border-strong:    rgba(0, 0, 0, 0.12);
  --text:             #1d1d1f;
  --text-secondary:    rgba(60, 60, 67, 0.72);
  --text-tertiary:     rgba(60, 60, 67, 0.48);
  --accent:           #007aff;
  --accent-soft:      rgba(0, 122, 255, 0.12);
  --shadow-window:    0 22px 70px rgba(0, 0, 0, 0.12);
  --shadow-panel:     0 1px 3px rgba(0, 0, 0, 0.06);
  --radius-window:    14px;
  --radius-panel:     10px;
  --radius-pill:      980px;
}

/* ================================================================
   mac-window
   ================================================================ */
.mac-window {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-window);
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
  font-size: 13px;
  color: var(--text);
}

/* ================================================================
   Title Bar
   ================================================================ */
.titlebar {
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 14px;
  background: linear-gradient(180deg, #fbfbfb 0%, #ececec 100%);
  border-bottom: 1px solid var(--border);
}

.titlebar-title {
  flex: 1;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}
.titlebar-hint {
  font-size: 11px;
  color: var(--text-tertiary);
}

/* ================================================================
   Toolbar
   ================================================================ */
.toolbar {
  height: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  background: linear-gradient(180deg, #ebebed 0%, #e4e4e7 100%);
  border-bottom: 1px solid var(--border);
}

.segmented {
  display: inline-flex;
  background: rgba(0,0,0,0.06);
  border-radius: 6px;
  padding: 2px;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.06);
}
.segmented button {
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 4px 12px;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.segmented button[aria-pressed="true"] {
  background: var(--bg-panel-solid);
  color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}
.segmented button:hover:not([aria-pressed="true"]) {
  background: rgba(0,0,0,0.04);
}

.toolbar-spacer { flex: 1; }

.search-field {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 200px;
  max-width: 280px;
  padding: 4px 10px;
  background: rgba(255,255,255,0.85);
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  box-shadow: inset 0 1px 1px rgba(0,0,0,0.04);
}
.search-field:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}
.search-field input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 12px;
  color: var(--text);
}
.search-field input::placeholder { color: var(--text-tertiary); }
.search-field svg { width: 14px; height: 14px; color: var(--text-tertiary); flex-shrink: 0; }

.tb-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.55);
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  font-family: inherit;
}
.tb-btn:hover {
  background: #fff;
  border-color: var(--border-strong);
}
.tb-btn svg { width: 14px; height: 14px; }

/* ================================================================
   Split Root — three columns
   ================================================================ */
.split-root {
  flex: 1;
  display: flex;
  min-height: 0;
  background: var(--bg-content);
}

/* ================================================================
   Left Sidebar — Finder-style
   ================================================================ */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  backdrop-filter: blur(14px);
}

.sidebar-header {
  padding: 12px 12px 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.filter-list {
  padding: 0 8px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  max-height: 280px;
}

.filter-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  border: 1px solid transparent;
  transition: background 0.12s, color 0.12s;
  background: transparent;
  font-family: inherit;
  text-align: left;
}
.filter-chip:hover { background: rgba(0,0,0,0.04); color: var(--text); }
.filter-chip.active {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}
.filter-chip .count {
  font-size: 10px;
  color: var(--text-tertiary);
  font-variant-numeric: tabular-nums;
}
.filter-chip.active .count { color: var(--accent); opacity: 0.85; }

.sidebar-search {
  padding: 0 10px 10px;
}
.sidebar-search .search-field {
  max-width: none;
  min-width: 0;
  width: 100%;
}

.sidebar-footer {
  margin-top: auto;
  padding: 10px 12px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--text-tertiary);
}
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 4px 0;
}
.stat-row strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

/* ================================================================
   Middle: Canvas Pane
   ================================================================ */
.canvas-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: linear-gradient(180deg, #fafafa 0%, #f3f3f5 100%);
}

.canvas-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.5);
  flex-shrink: 0;
}
.canvas-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}
.hint {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-tertiary);
}

.canvas-body {
  flex: 1;
  min-height: 0;
  position: relative;
  background: var(--bg-panel-solid);
  overflow: hidden;
}

.canvas-grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle at 1px 1px, rgba(0,0,0,0.06) 1px, transparent 0);
  background-size: 18px 18px;
  opacity: 0.7;
  pointer-events: none;
}

/* Canvas SVG (edge lines) */
.canvas-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: visible;
}
.canvas-edge {
  stroke: #007aff;
  stroke-width: 1.2;
  opacity: 0.45;
  stroke-dasharray: none;
}

/* Canvas nodes */
.canvas-node {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 10px 14px;
  min-width: 100px;
  max-width: 160px;
  border-radius: 14px;
  border: 1px solid rgba(0,0,0,0.1);
  background: rgba(255,255,255,0.92);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
  z-index: 1;
}
.canvas-node:hover {
  border-color: rgba(0,122,255,0.4);
  box-shadow: 0 4px 16px rgba(0,122,255,0.18);
  transform: translate(-50%, -50%) translateY(-2px);
}
.canvas-node.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft), 0 4px 16px rgba(0,122,255,0.2);
  background: #fff;
}
.canvas-node__label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  text-align: center;
  line-height: 1.3;
}
.canvas-node__domain {
  font-size: 10px;
  color: var(--text-tertiary);
  text-align: center;
}

/* Placeholder */
.canvas-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-tertiary);
  text-align: center;
  padding: 24px;
  pointer-events: none;
}
.canvas-placeholder svg {
  width: 40px;
  height: 40px;
  opacity: 0.35;
}
.canvas-placeholder h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}
.canvas-placeholder p {
  font-size: 12px;
  max-width: 320px;
  line-height: 1.5;
}

/* ================================================================
   Right: Inspector Panel
   ================================================================ */
.inspector {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgba(252, 252, 252, 0.92);
  border-left: 1px solid var(--border);
  backdrop-filter: blur(12px);
}

.inspector-header {
  padding: 12px 14px 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  text-transform: uppercase;
  flex-shrink: 0;
}

.inspector-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 12px;
}

.inspector-empty {
  height: 100%;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;
  color: var(--text-tertiary);
  padding: 20px;
}
.inspector-empty svg { width: 36px; height: 36px; opacity: 0.4; }
.inspector-empty h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.inspector-empty p { font-size: 12px; line-height: 1.45; }

.group-box {
  background: var(--bg-panel-solid);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 10px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.8) inset;
}
.group-box h5 {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}
.group-box .row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 3px 0;
  color: var(--text-secondary);
}
.group-box .row span:last-child {
  color: var(--text);
  font-weight: 500;
}

.inspector-actions {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.btn {
  flex: 1;
  font-family: inherit;
  font-size: 12px;
  font-weight: 500;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid var(--border-strong);
  background: linear-gradient(180deg, #fff 0%, #f2f2f3 100%);
  color: var(--text);
  cursor: pointer;
  transition: filter 0.12s, box-shadow 0.12s;
}
.btn:hover { filter: brightness(1.02); }
.btn:active { filter: brightness(0.98); }
.btn-primary {
  border-color: rgba(0, 122, 255, 0.45);
  background: linear-gradient(180deg, #4da2ff 0%, #007aff 100%);
  color: #fff;
}

/* ================================================================
   Status Bar
   ================================================================ */
.statusline {
  height: 24px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 11px;
  color: var(--text-tertiary);
  background: linear-gradient(180deg, #e9e9eb 0%, #e2e2e5 100%);
  border-top: 1px solid var(--border);
}
.statusline .sep { margin: 0 8px; opacity: 0.5; }

/* ================================================================
   Responsive
   ================================================================ */
@media (max-width: 900px) {
  .kg-page { padding: 12px; }
  /* 高度由 shell-content + flex:1 链铺满，勿用 100vh 以免侧栏/留白算错 */
  .mac-window { width: 100%; }
  .inspector { width: 260px; }
  .sidebar { width: 190px; }
}
@media (max-width: 720px) {
  .split-root { flex-direction: column; }
  .sidebar, .inspector {
    width: 100%;
    border-right: none;
    border-left: none;
    border-bottom: 1px solid var(--border);
  }
  .canvas-pane { min-height: 280px; }
}
</style>
